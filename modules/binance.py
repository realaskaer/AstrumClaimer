import asyncio
import hmac
import time

from hashlib import sha256

from .client import Client
from .interfaces import SoftwareExceptionWithoutRetry, InsufficientBalanceException, CEX, Logger
from utils.tools import helper
from config import BINANCE_NETWORKS_NAME, CEX_WRAPPED_ID


class Binance(CEX, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, 'Binance')

        self.api_url = "https://api.binance.com"
        self.network = self.client.network.name
        self.headers = {
            "Content-Type": "application/json",
            "X-MBX-APIKEY": self.api_key,
        }

    @staticmethod
    def parse_params(params: dict | None = None):
        if params:
            sorted_keys = sorted(params)
            params_str = "&".join(["%s=%s" % (x, params[x]) for x in sorted_keys])
        else:
            params_str = ''
        return params_str + "&timestamp=" + str(int(time.time() * 1000))

    def get_sign(self, payload: str = ""):
        try:
            secret_key_bytes = self.api_secret.encode('utf-8')
            signature = hmac.new(secret_key_bytes, payload.encode('utf-8'), sha256).hexdigest()

            return signature
        except Exception as error:
            raise SoftwareExceptionWithoutRetry(f'Bad signature for Binance request: {error}')

    async def get_balance(self, ccy):
        balances = await self.get_main_balance()

        ccy_balance = [balance for balance in balances if balance['asset'] == ccy]

        if ccy_balance:
            return float(ccy_balance[0]['free'])
        raise SoftwareExceptionWithoutRetry(f'Your have not enough {ccy} balance on CEX')

    async def get_currencies(self, ccy):
        path = '/sapi/v1/capital/config/getall'

        params = {
            'timestamp': str(int(time.time() * 1000))
        }

        parse_params = self.parse_params(params)

        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        data = await self.make_request(url=url, headers=self.headers, module_name='Token info')
        return [item for item in data if item['coin'] == ccy]

    async def get_sub_list(self):
        path = "/sapi/v1/sub-account/list"

        parse_params = self.parse_params()
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"

        await asyncio.sleep(2)
        return await self.make_request(url=url, headers=self.headers, module_name='Get subAccounts list')

    async def get_sub_balance(self, sub_email):
        path = '/sapi/v3/sub-account/assets'

        params = {
            "email": sub_email
        }

        await asyncio.sleep(2)
        parse_params = self.parse_params(params)
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(url=url, headers=self.headers, module_name='Get subAccount balance')

    async def get_main_balance(self):
        path = '/sapi/v3/asset/getUserAsset'

        await asyncio.sleep(2)
        parse_params = self.parse_params()
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(method='POST', url=url, headers=self.headers, content_type=None,
                                       module_name='Get main account balance')

    async def get_cex_balances(self, ccy: str = 'ETH'):
        if ccy == 'USDC.e':
            ccy = 'USDC'

        balances = {}

        main_balance = await self.get_main_balance()

        ccy_balance = [balance for balance in main_balance if balance['asset'] == ccy]

        if ccy_balance:
            balances['Main CEX Account'] = float(ccy_balance[0]['free'])
        else:
            balances['Main CEX Account'] = 0

        sub_list = (await self.get_sub_list())['subAccounts']

        for sub_data in sub_list:
            sub_name = sub_data['email']
            sub_balances = await self.get_sub_balance(sub_name)
            ccy_sub_balance = [balance for balance in sub_balances['balances'] if balance['asset'] == ccy]

            if ccy_sub_balance:
                balances[sub_name] = float(ccy_sub_balance[0]['free'])
            else:
                balances[sub_name] = 0

            await asyncio.sleep(3)

        return balances

    @helper
    async def withdraw(self, withdraw_data: tuple):
        path = '/sapi/v1/capital/withdraw/apply'

        network_id, amount = withdraw_data
        fee_limiter = 2 ** 128
        network_raw_name = BINANCE_NETWORKS_NAME[network_id]
        ccy, network_name = network_raw_name.split('-')
        dst_chain_name = CEX_WRAPPED_ID[network_id]

        if isinstance(amount, str):
            amount = self.client.custom_round(await self.get_balance(ccy=ccy) * float(amount), 6)
        else:
            amount = self.client.custom_round(amount)

        if amount == 0.0:
            raise SoftwareExceptionWithoutRetry('Can`t withdraw zero amount')

        self.logger_msg(*self.client.acc_info, msg=f"Withdraw {amount} {ccy} to {network_name}")

        while True:
            try:
                withdraw_raw_data = (await self.get_currencies(ccy))[0]['networkList']

                network_data = {
                    item['network']: {
                        'withdrawEnable': item['withdrawEnable'],
                        'withdrawFee': item['withdrawFee'],
                        'withdrawMin': item['withdrawMin'],
                        'withdrawMax': item['withdrawMax']
                    } for item in withdraw_raw_data
                }[network_name]

                if network_data['withdrawEnable']:
                    if float(network_data['withdrawFee']) <= fee_limiter or fee_limiter == 0:
                        min_wd, max_wd = float(network_data['withdrawMin']), float(network_data['withdrawMax'])

                        if min_wd <= amount <= max_wd:

                            params = {
                                "address": f"{self.client.address}",
                                "amount": amount,
                                "coin": ccy,
                                "network": network_name,
                            }

                            ccy = f"{ccy}.e" if network_id in [29, 30] else ccy

                            old_balance_data_on_dst = await self.client.wait_for_receiving(
                                dst_chain_name, token_name=ccy, check_balance_on_dst=True
                            )

                            parse_params = self.parse_params(params)
                            url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"

                            await self.make_request(method='POST', url=url, headers=self.headers, module_name='Withdraw')

                            self.logger_msg(
                                *self.client.acc_info, msg=f"Withdraw complete. Note: wait a little for receiving funds",
                                type_msg='success'
                            )

                            await self.client.wait_for_receiving(
                                dst_chain_name, old_balance_data=old_balance_data_on_dst, token_name=ccy
                            )
                            return True
                        else:
                            raise SoftwareExceptionWithoutRetry(
                                f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}")
                    else:
                        raise SoftwareExceptionWithoutRetry(
                            f"Fee exceeds the limit. Fee: {network_data['min_fee']}, limit: {fee_limiter}"
                        )
                else:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Withdraw from {network_name} is not active now. Will try again in 1 min...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(60)
            except InsufficientBalanceException:
                continue
