import asyncio
import copy
import random

from dev import Settings
from .client import Client
from utils.tools import helper, sleep, network_handler, gas_checker
from config import TOKENS_PER_CHAIN, WETH_ABI
from .interfaces import (
    SoftwareException, SoftwareExceptionWithoutRetry, SoftwareExceptionHandled, Logger, RequestClient
)


class Custom(Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    @helper
    @gas_checker
    async def wrap_native(self, settings: list):
        token_name = f"W{self.client.token}"
        amount_in_wei, amount = await self.client.get_smart_amount(settings, token_name=token_name)

        weth_contract = self.client.get_contract(TOKENS_PER_CHAIN[self.client.network.name][token_name], WETH_ABI)

        self.logger_msg(*self.client.acc_info, msg=f"Wrap {amount} ${self.client.token}")

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)
            transaction = await weth_contract.functions.deposit().build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise SoftwareException("Insufficient balance!")

    @helper
    @gas_checker
    async def unwrap_native(self):
        weth_contract = self.client.get_contract(
            TOKENS_PER_CHAIN[self.client.network.name][f"W{self.client.token}"], WETH_ABI,
        )

        amount_in_wei = await weth_contract.functions.balanceOf(self.client.address).call()

        if amount_in_wei == 0:
            raise SoftwareException("Can not withdraw Zero amount")

        amount = round(amount_in_wei / 10**18, 6)

        self.logger_msg(*self.client.acc_info, msg=f"Unwrap {amount:.6f} {self.client.token}")

        tx_params = await self.client.prepare_transaction()

        transaction = await weth_contract.functions.withdraw(amount_in_wei).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    def get_wallet_for_transfer(self):
        from config import ACCOUNTS_DATA

        cex_address = ACCOUNTS_DATA['accounts'][self.client.account_name].get('evm_deposit_address')

        if not cex_address:
            raise SoftwareExceptionWithoutRetry(f'There is no wallet listed for transfer, please add wallet into accounts_data.xlsx')

        return cex_address

    @helper
    @gas_checker
    async def transfer_eth(self):
        transfer_address = self.get_wallet_for_transfer()

        amount_in_wei, amount = await self.client.get_smart_amount(Settings.TRANSFER_ETH_AMOUNT)

        simulate_amount_fee = await self.client.simulate_transfer('ETH')

        amount = self.client.custom_round(amount - simulate_amount_fee, 6)
        amount_in_wei = self.client.to_wei(amount)

        transaction = await self.client.prepare_transaction(value=int(amount_in_wei)) | {
            'to': self.client.w3.to_checksum_address(transfer_address),
            'data': '0x'
        }

        self.logger_msg(*self.client.acc_info, msg=f"Transfer {amount} ETH to {transfer_address} address")

        return await self.client.send_transaction(transaction)

    @network_handler
    async def balance_searcher(
            self, chains, tokens: tuple | list = None, native_check: bool = False, silent_mode: bool = False,
            balancer_mode: bool = False, random_mode: bool = False, wrapped_tokens: bool = False,
            need_token_name: bool = False, raise_handle: bool = False, without_error: bool = False
    ):
        index = 0
        clients = [self.client.new_client(chain) for chain in chains]

        if native_check:
            tokens = [client.token for client in clients]
        elif wrapped_tokens:
            tokens = [f'W{client.token}' for client in clients]

        balances = []
        for client, token in zip(clients, tokens):
            balances.append(await client.get_token_balance(
                token_name=token,
                without_error=without_error
            ) if token in TOKENS_PER_CHAIN[client.network.name] or token in [f'W{client.token}',
                                                                             client.token] else (0, 0, ''))

        flag = all(balance_in_wei == 0 for balance_in_wei, _, _ in balances)

        if raise_handle and flag:
            raise SoftwareExceptionHandled('Insufficient balances in all networks!')

        if flag and not balancer_mode:
            raise SoftwareException('Insufficient balances in all networks!')

        balances_in_usd = []
        token_prices = {}
        for balance_in_wei, balance, token_name in balances:
            token_price = 1
            if 'USD' != token_name:
                if token_name not in token_prices:
                    if token_name != '':
                        token_price = 1 #await self.get_token_price(token_name)
                    else:
                        token_price = 0
                    token_prices[token_name] = token_price
                else:
                    token_price = token_prices[token_name]
            balance_in_usd = balance * token_price

            if need_token_name:
                balances_in_usd.append([balance_in_usd, token_price, token_name])
            else:
                balances_in_usd.append([balance_in_usd, token_price])

        if not random_mode:
            index = balances_in_usd.index(max(balances_in_usd, key=lambda x: x[0]))
        else:
            try:
                index = balances_in_usd.index(random.choice(
                    [balance for balance in balances_in_usd if balance[0] > 0.2]
                ))
            except Exception as error:
                if 'list index out of range' in str(error):
                    raise SoftwareExceptionWithoutRetry('All networks have lower 0.2$ of native')

        if not silent_mode:
            clients[index].logger_msg(
                *clients[index].acc_info,
                msg=f"Detected {round(balances[index][1], 5)} {tokens[index]} in {clients[index].network.name}",
                type_msg='success'
            )

        return clients[index], index, balances[index][1], balances[index][0], balances_in_usd[index]

    @helper
    async def smart_cex_withdraw(self, dapp_id: int):
        while True:
            try:
                from functions import Binance

                cex_class, withdraw_data = {
                    # 1: (okx_withdraw_util, Settings.OKX_WITHDRAW_DATA),
                    # 2: (bingx_withdraw_util, Settings.BINGX_WITHDRAW_DATA),
                    3: (Binance, Settings.BINANCE_WITHDRAW_DATA),
                    # 4: (bitget_withdraw_util, Settings.BITGET_WITHDRAW_DATA)
                }[dapp_id]

                withdraw_data_copy = copy.deepcopy(withdraw_data)

                random.shuffle(withdraw_data_copy)
                result_list = []

                for index, data in enumerate(withdraw_data_copy, 1):
                    current_data = data
                    if isinstance(data[0], list):
                        current_data = random.choice(data)
                        if not current_data:
                            continue

                    network, amount = current_data

                    current_client = self.client

                    if isinstance(amount[0], str):
                        amount = f"{self.client.custom_round(random.uniform(float(amount[0]), float(amount[1])), 6) / 100}"

                    result_list.append(await cex_class(current_client).withdraw(withdraw_data=(network, amount)))

                    if index != len(withdraw_data_copy):
                        await sleep(self)

                return all(result_list)
            except Exception as error:
                msg = f"Software cannot continue, awaiting operator's action. Will try again in 1 min... Error: {error}"
                self.logger_msg(self.client.account_name, None, msg=msg, type_msg='warning')
                await asyncio.sleep(60)

    @helper
    @gas_checker
    async def smart_bridge(self, dapp_id: int = None):
        from functions import bridge_utils

        dapp_chains, dapp_tokens, limiter = {
            # 1: (Settings.ACROSS_CHAIN_FROM_NAMES, Settings.ACROSS_TOKEN_NAME, Settings.ACROSS_AMOUNT_LIMITER),
            # 2: (Settings.BUNGEE_CHAIN_FROM_NAMES, Settings.BUNGEE_TOKEN_NAME, Settings.BUNGEE_AMOUNT_LIMITER),
            3: (Settings.RELAY_CHAIN_FROM_NAMES, Settings.RELAY_TOKEN_NAME, Settings.RELAY_AMOUNT_LIMITER),
        }[dapp_id]

        if len(dapp_tokens) == 2:
            from_token_name, to_token_name = dapp_tokens
        else:
            from_token_name, to_token_name = dapp_tokens, dapp_tokens

        dapp_tokens = [from_token_name for _ in dapp_chains]

        client, chain_index, balance, _, balance_data = await self.balance_searcher(
            chains=dapp_chains, tokens=dapp_tokens, raise_handle=True
        )

        fee_client = client.new_client(dapp_chains[chain_index])
        chain_from_name, token_name = dapp_chains[chain_index], from_token_name

        switch_id = dapp_id

        bridge_cfg_from_name, bridge_cfg_to_name, amount, chain_to_name = await client.get_bridge_data(
            chain_from_name=chain_from_name, dapp_id=switch_id, settings_id=dapp_id
        )

        from_token_addr = TOKENS_PER_CHAIN[client.network.name][from_token_name]

        if to_token_name == 'USDC':
            to_token_addr = TOKENS_PER_CHAIN[chain_to_name].get('USDC.e')
            if not to_token_addr:
                to_token_addr = TOKENS_PER_CHAIN[chain_to_name]['USDC']
        else:
            to_token_addr = TOKENS_PER_CHAIN[chain_to_name][to_token_name]

        balance_in_usd, token_price = balance_data
        limit_amount, wanted_to_hold_amount = limiter
        min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)
        fee_bridge_data = (
            bridge_cfg_from_name, bridge_cfg_to_name, amount, from_token_name,
            to_token_name, from_token_addr, to_token_addr, chain_to_name
        )

        if balance_in_usd >= limit_amount:
            bridge_fee = await bridge_utils(fee_client, switch_id, fee_bridge_data, need_fee=True)
            min_hold_balance = random.uniform(min_wanted_amount, max_wanted_amount) / token_price
            if balance - bridge_fee - min_hold_balance > 0:
                if balance < amount - bridge_fee and from_token_name == client.token:
                    raise SoftwareExceptionWithoutRetry(
                        f"Not enough balance to bridge {amount} {from_token_name} "
                        f"with {bridge_fee} {from_token_name} fee. "
                        f"Current balance = {balance} {from_token_name}"
                    )
                else:
                    bridge_amount = self.client.custom_round(amount - bridge_fee, 6)
                if balance - bridge_amount < min_hold_balance:
                    need_to_freeze_amount = min_hold_balance - (balance - bridge_amount)
                    bridge_amount = self.client.custom_round(bridge_amount - need_to_freeze_amount)

                if bridge_amount < 0:
                    raise SoftwareExceptionWithoutRetry(
                        f'Set BRIDGE_AMOUNT_LIMITER[2 value] lower than {wanted_to_hold_amount}. '
                        f'Current amount = {bridge_amount} {from_token_name}')

                bridge_amount_in_usd = bridge_amount * token_price

                bridge_data = (
                    bridge_cfg_from_name, bridge_cfg_to_name, bridge_amount, from_token_name,
                    to_token_name, from_token_addr, to_token_addr, chain_to_name
                )

                if balance_in_usd >= bridge_amount_in_usd:
                    return await bridge_utils(client, switch_id, bridge_data)

                info = f"{balance_in_usd:.2f}$ < {bridge_amount_in_usd:.2f}$"
                raise SoftwareExceptionHandled(f'Account {token_name} balance < wanted bridge amount: {info}')

            full_need_amount = self.client.custom_round(bridge_fee + min_hold_balance)
            info = f"{balance:.2f} {token_name} < {full_need_amount:.2f} {token_name}"
            raise SoftwareExceptionHandled(f'Account {token_name} balance < bridge fee + hold amount: {info}')

        info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
        raise SoftwareExceptionHandled(f'Account {token_name} balance < wanted limit amount: {info}')
