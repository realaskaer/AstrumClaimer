import hmac
import base64
import asyncio

from hashlib import sha256
from datetime import datetime, timezone

from dev import Settings, GeneralSettings
from utils.tools import helper, network_handler
from config import OKX_NETWORKS_NAME, CEX_WRAPPED_ID, TOKENS_PER_CHAIN
from modules.interfaces import Logger, CEX, SoftwareExceptionWithoutRetry, SoftwareException, \
    InsufficientBalanceException
from modules import EVMClient


class OKX(CEX, Logger):
    def __init__(self, client: EVMClient):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, "OKX")
        self.network = self.client.network.name

    async def get_headers(self, request_path: str, method: str = "GET", body: str = ""):
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            prehash_string = timestamp + method.upper() + request_path[19:] + body
            secret_key_bytes = self.api_secret.encode('utf-8')
            signature = hmac.new(secret_key_bytes, prehash_string.encode('utf-8'), sha256).digest()
            encoded_signature = base64.b64encode(signature).decode('utf-8')

            return {
                "Content-Type": "application/json",
                "OK-ACCESS-KEY": self.api_key,
                "OK-ACCESS-SIGN": encoded_signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": self.passphras,
                "x-simulated-trading": "0"
            }
        except Exception as error:
            raise SoftwareExceptionWithoutRetry(f'Bad headers for OKX request: {error}')

    async def get_currencies(self, ccy: str = 'ETH'):
        if ccy == 'USDC.e':
            ccy = 'USDC'

        url = f'https://www.okx.cab/api/v5/asset/currencies?ccy={ccy}'

        headers = await self.get_headers(url)

        return await self.make_request(url=url, headers=headers, module_name='Token info')

    async def get_sub_list(self):
        url_sub_list = "https://www.okx.cab/api/v5/users/subaccount/list"

        headers = await self.get_headers(request_path=url_sub_list)
        return await self.make_request(url=url_sub_list, headers=headers, module_name='Get subAccounts list')

    async def get_main_acc_balance(self, ccy, deposit_mode: bool = False):
        if GeneralSettings.OKX_EU_TYPE and deposit_mode:
            url_balance = f"https://www.okx.cab/api/v5/account/balance?ccy={ccy}"
        else:
            url_balance = f"https://www.okx.cab/api/v5/asset/balances?ccy={ccy}"

        headers = await self.get_headers(request_path=url_balance)
        response = (
            await self.make_request(url=url_balance, headers=headers, module_name='Get Main Account balance')
        )

        if response:
            if GeneralSettings.OKX_EU_TYPE and deposit_mode:
                if response[0]['details']:
                    balance_data = response[0]['details']
                    if balance_data:
                        for bal in balance_data:
                            if bal['ccy'] == ccy:
                                return float(bal['availBal'])
            else:
                return float(response[0]['availBal'])
        return 0

    async def get_sub_acc_balance(self, sub_name, ccy):
        if GeneralSettings.OKX_EU_TYPE:
            url_balance = f'https://www.okx.cab/api/v5/account/subaccount/balances?subAcct={sub_name}'
        else:
            url_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy={ccy}"

        headers = await self.get_headers(request_path=url_balance)
        response = (
            await self.make_request(url=url_balance, headers=headers, module_name='Get Sub-account balance')
        )

        if response:
            if GeneralSettings.OKX_EU_TYPE:
                if response[0]['details']:
                    balance_data = response[0]['details']
                    if balance_data:
                        for bal in balance_data:
                            if bal['ccy'] == ccy:
                                return float(bal['availBal'])
            else:
                return float(response[0]['availBal'])
        return 0

    @helper
    async def transfer_from_subaccounts(self, ccy: str = 'ETH', amount: float = None, silent_mode: bool = False):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        if not silent_mode:
            self.logger_msg(*self.client.acc_info, msg=f'Checking subAccounts balance')

        flag = True
        sub_list = await self.get_sub_list()
        await asyncio.sleep(1)

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            sub_balance = await self.get_sub_acc_balance(sub_name, ccy)

            await asyncio.sleep(1)
            amount = amount if amount else sub_balance

            if sub_balance == amount and sub_balance != 0.0:
                flag = False
                self.logger_msg(*self.client.acc_info, msg=f'{sub_name} | subAccount balance : {sub_balance:.8f} {ccy}')

                body = {
                    "ccy": ccy,
                    "type": "2",
                    "amt": f"{amount:.10f}",
                    "from": "6" if not GeneralSettings.OKX_EU_TYPE else "18",
                    "to": "6" if not GeneralSettings.OKX_EU_TYPE else "18",
                    "subAcct": sub_name
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(method="POST", request_path=url_transfer, body=str(body))

                await self.make_request(
                    method="POST", url=url_transfer, data=str(body), headers=headers, module_name='SubAccount transfer'
                )

                self.logger_msg(
                    *self.client.acc_info, msg=f"Transfer {amount:.8f} {ccy} to main account complete",
                    type_msg='success'
                )

                if not silent_mode:
                    break
        if flag and not silent_mode:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 {ccy}', type_msg='warning')
        return True

    @helper
    async def transfer_from_spot_to_funding(self, ccy: str = 'ETH'):

        await asyncio.sleep(5)

        if ccy == 'USDC.e':
            ccy = 'USDC'

        url_balance = f"https://www.okx.cab/api/v5/account/balance?ccy={ccy}"
        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(
            url=url_balance, headers=headers, module_name='Trading account'
        ))[0]["details"]

        for ccy_item in balance:
            if ccy_item['ccy'] == ccy and ccy_item['availBal'] != '0':

                self.logger_msg(
                    *self.client.acc_info, msg=f"Main trading account balance: {ccy_item['availBal']} {ccy}")

                body = {
                    "ccy": ccy,
                    "amt": ccy_item['availBal'],
                    "from": "18",
                    "to": "6"
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(request_path=url_transfer, body=str(body), method="POST")
                await self.make_request(
                    url=url_transfer, data=str(body), method="POST", headers=headers, module_name='Trading account'
                )

                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Transfer {float(ccy_item['availBal']):.6f} {ccy} to funding account complete",
                    type_msg='success'
                )
                break
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Main trading account balance: 0 {ccy}", type_msg='warning')
                break

        return True

    async def get_cex_balances(self, ccy: str = 'ETH', deposit_mode: bool = False):
        balances = {}

        await asyncio.sleep(10)

        if ccy == 'USDC.e':
            ccy = 'USDC'

        sub_list = await self.get_sub_list()
        main_balance = await self.get_main_acc_balance(ccy=ccy, deposit_mode=deposit_mode)

        if main_balance:
            balances['Main CEX Account'] = main_balance
        else:
            balances['Main CEX Account'] = 0

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            sub_balance = await self.get_sub_acc_balance(sub_name=sub_name, ccy=ccy)

            await asyncio.sleep(3)

            if sub_balance:
                balances[sub_name] = sub_balance
            else:
                balances[sub_name] = 0

        return balances

    @network_handler
    async def wait_deposit_confirmation(
            self, amount: float, old_sub_balances: dict, ccy: str = 'ETH', check_time: int = 45,
    ):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f"Start checking CEX balances")

        await asyncio.sleep(10)
        while True:
            try:
                new_sub_balances = await self.get_cex_balances(ccy=ccy, deposit_mode=True)
                for sub_name, sub_balance in new_sub_balances.items():

                    if sub_balance > old_sub_balances[sub_name]:
                        self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} complete", type_msg='success')
                        return True
                    else:
                        continue
                else:
                    self.logger_msg(*self.client.acc_info, msg=f"Deposit still in progress...", type_msg='warning')
                    await asyncio.sleep(check_time)
            except Exception as error:
                if 'Too many requests' in str(error):
                    self.logger_msg(
                        *self.client.acc_info, msg=f"OKX API got rate limit, will wait 1 min and try again",
                        type_msg='warning'
                    )
                    await self.client.smart_sleep([55, 60], without_setting=True)
                else:
                    raise error

    @helper
    async def withdraw(self, withdraw_data: tuple = None):
        url = 'https://www.okx.cab/api/v5/asset/withdrawal'

        network, amount = withdraw_data
        network_raw_name = OKX_NETWORKS_NAME[network]
        split_network_data = network_raw_name.split('-')
        ccy, network_name = split_network_data[0], '-'.join(split_network_data[1:])
        dst_chain_name = CEX_WRAPPED_ID[network]

        await self.transfer_from_subs(ccy=ccy, silent_mode=True)

        if isinstance(amount, str):
            amount = self.client.custom_round(await self.get_main_acc_balance(ccy=ccy) * float(amount), 6)
        else:
            amount = self.client.custom_round(amount)

        if amount == 0.0:
            raise SoftwareExceptionWithoutRetry(f'You CEX account {ccy} balance is zero')

        while True:
            withdraw_raw_data = await self.get_currencies(ccy)
            network_data = {
                item['chain']: {
                    'can_withdraw': item['canWd'],
                    'min_fee': item['minFee'],
                    'min_wd': item['minWd'],
                    'max_wd': item['maxWd']
                } for item in withdraw_raw_data
            }[network_raw_name]

            if network_data['can_withdraw']:
                min_wd, max_wd = float(network_data['min_wd']), float(network_data['max_wd'])

                self.logger_msg(*self.client.acc_info, msg=f"Withdraw {amount} {ccy} to {network_name}")

                if min_wd <= amount <= max_wd:
                    pass
                else:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}, will set minimum",
                        type_msg='warning'
                    )
                    amount = self.client.custom_round([min_wd, min_wd * 1.1], 6)

                amount = amount - float(network_data['min_fee'])
                if amount < float(network_data['min_wd']):
                    amount = amount + float(network_data['min_fee'])

                body = {
                    "ccy": ccy,
                    "amt": amount,
                    "dest": "4",
                    "toAddr": f"{self.client.address}",
                    "fee": network_data['min_fee'],
                    "chain": network_raw_name,
                }

                ccy = f"{ccy}.e" if network in [29, 30] else ccy

                old_balance_data_on_dst = await self.client.wait_for_receiving(
                    dst_chain_name, token_name=ccy, check_balance_on_dst=True
                )

                headers = await self.get_headers(method="POST", request_path=url, body=str(body))
                await self.make_request(
                    method='POST', url=url, data=str(body), headers=headers, module_name='Withdraw'
                )

                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Withdraw complete. Note: wait a little for receiving funds", type_msg='success'
                )

                await self.client.wait_for_receiving(
                    dst_chain_name, old_balance_data=old_balance_data_on_dst, token_name=ccy
                )

                return True
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Withdraw from {network_name} is not active now. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)

    def get_wallet_for_deposit(self, deposit_network: int = None):
        from config import ACCOUNTS_DATA

        cex_address = ACCOUNTS_DATA['accounts'][self.client.account_name].get('evm_deposit_address')

        if not cex_address:
            raise SoftwareExceptionWithoutRetry(f'There is no wallet listed for deposit into CEX, please add wallet into accounts_data.xlsx')

        return cex_address

    @helper
    async def deposit(self, deposit_data: tuple = None):
        deposit_network, amount = deposit_data
        network_raw_name = OKX_NETWORKS_NAME[deposit_network]
        split_network_data = network_raw_name.split('-')
        ccy, network_name = split_network_data[0], '-'.join(split_network_data[1:])
        ccy = f"{ccy}.e" if deposit_network in [29, 30] else ccy
        cex_wallet = self.get_wallet_for_deposit(deposit_network)
        info = f"{cex_wallet[:10]}....{cex_wallet[-6:]}"

        await self.transfer_from_subs(ccy=ccy, silent_mode=True)

        self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to OKX wallet: {info}")

        while True:
            try:
                withdraw_data = await self.get_currencies(ccy)
                network_data = {item['chain']: {'can_dep': item['canDep'], 'min_dep': item['minDep']}
                                for item in withdraw_data}[network_raw_name]

                if network_data['can_dep']:

                    min_dep = float(network_data['min_dep'])

                    if amount >= min_dep:

                        cex_balances = await self.get_cex_balances(ccy=ccy, deposit_mode=True)

                        if ccy != self.client.token:
                            token_contract = self.client.get_contract(TOKENS_PER_CHAIN[self.network][ccy])
                            decimals = await self.client.get_decimals(ccy)
                            amount_in_wei = self.client.to_wei(amount, decimals)

                            transaction = await token_contract.functions.transfer(
                                self.client.w3.to_checksum_address(cex_wallet),
                                amount_in_wei
                            ).build_transaction(await self.client.prepare_transaction())
                        else:
                            amount_in_wei = self.client.to_wei(amount)
                            transaction = (await self.client.prepare_transaction(value=int(amount_in_wei))) | {
                                'to': self.client.w3.to_checksum_address(cex_wallet),
                                'data': '0x'
                            }

                        result_tx = await self.client.send_transaction(transaction)

                        if result_tx:
                            result_confirmation = await self.wait_deposit_confirmation(amount, cex_balances, ccy=ccy)

                            result_transfer = await self.transfer_from_subs(ccy=ccy, amount=amount)

                            return all([result_tx, result_confirmation, result_transfer])
                        else:
                            raise SoftwareException('Transaction not sent, trying again')
                    else:
                        raise SoftwareExceptionWithoutRetry(f"Minimum to deposit: {min_dep} {ccy}")
                else:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Deposit to {network_name} is not active now. Will try again in 1 min...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(60)
            except InsufficientBalanceException:
                continue

    async def transfer_from_subs(self, ccy, amount: float = None, silent_mode: bool = False):
        await self.transfer_from_subaccounts(ccy=ccy, amount=amount, silent_mode=silent_mode)

        await self.transfer_from_spot_to_funding(ccy=ccy)

        return True

    async def get_currency_pair(self, from_ccy: str, to_ccy: str):
        if from_ccy == 'USDC.e':
            from_ccy = 'USDC'

        if to_ccy == 'USDC.e':
            to_ccy = 'USDC'

        url = f'https://www.okx.cab/api/v5/asset/convert/currency-pair?fromCcy={from_ccy}&toCcy={to_ccy}'

        headers = await self.get_headers(url)

        return (await self.make_request(url=url, headers=headers, module_name='Token pair info'))[0]

    async def estimate_quote(self, base_ccy, quote_ccy, side, amount, base_currency_amount_mode=True):
        url = f'https://www.okx.cab/api/v5/asset/convert/estimate-quote'

        body = {
            "baseCcy": base_ccy,
            "quoteCcy": quote_ccy,
            "side": side,
            "rfqSz": amount,
            "rfqSzCcy": base_ccy if base_currency_amount_mode else quote_ccy
        }

        headers = await self.get_headers(method="POST", request_path=url, body=str(body))

        return (await self.make_request(
            method="POST", url=url, data=str(body), headers=headers, module_name='Estimate quote'
        ))[0]

    @helper
    async def convert(self, from_ccy, to_ccy, amount=None, base_currency_amount_mode=True):
        currency_pair_data = await self.get_currency_pair(from_ccy, to_ccy)
        side = 'sell' if from_ccy == currency_pair_data['baseCcy'] else 'buy'

        if not amount:
            amount = await self.get_main_acc_balance(ccy=from_ccy)
        else:
            amount = self.client.custom_round(amount)

        quote_data = await self.estimate_quote(
            currency_pair_data['baseCcy'],
            currency_pair_data['quoteCcy'],
            side,
            amount,
            base_currency_amount_mode
        )

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Convert {self.client.custom_round(quote_data['baseSz'])} {from_ccy} -> "
                f"{self.client.custom_round(quote_data['quoteSz'])} {to_ccy}",
        )

        url = f'https://www.okx.cab/api/v5/asset/convert/trade'

        body = {
            "baseCcy": quote_data['baseCcy'],
            "quoteCcy": quote_data['quoteCcy'],
            "side": side,
            "sz": amount,
            "szCcy": quote_data['baseCcy'] if base_currency_amount_mode else quote_data['quoteCcy'],
            "quoteId": quote_data['quoteId']
        }

        headers = await self.get_headers(method="POST", request_path=url, body=str(body))

        response = (await self.make_request(
            method="POST", url=url, data=str(body), headers=headers, module_name='Estimate quote'
        ))[0]

        if response['state'] == 'fullyFilled':
            self.logger_msg(*self.client.acc_info, msg=f"Successfully converted", type_msg='success')
            return True
        else:
            self.logger_msg(*self.client.acc_info, msg=f"Can not complete conversion", type_msg='error')
            return False