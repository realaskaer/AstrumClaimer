import random

from modules import Logger, RequestClient
from utils.tools import helper, network_handler
from config import TOKENS_PER_CHAIN, WETH_ABI
from dev import Settings
from modules.interfaces import (
    SoftwareException, SoftwareExceptionWithoutRetry, SoftwareExceptionHandled
)


class Custom(Logger, RequestClient):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    @helper
    async def wrap_native(self):

        amount_in_wei, amount = await self.client.get_smart_amount(Settings.WRAP_BERA_AMOUNT)

        weth_contract = self.client.get_contract(
            TOKENS_PER_CHAIN[self.client.network.name][self.client.token], WETH_ABI
        )

        self.logger_msg(*self.client.acc_info, msg=f'Wrap {amount} ${self.client.token}')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)
            transaction = await weth_contract.functions.deposit().build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise SoftwareException('Insufficient balance!')

    @helper
    async def unwrap_native(self):
        weth_contract = self.client.get_contract(
            TOKENS_PER_CHAIN[self.client.network.name][self.client.token], WETH_ABI
        )

        amount_in_wei = await weth_contract.functions.balanceOf(self.client.address).call()

        if amount_in_wei == 0:
            raise SoftwareExceptionWithoutRetry('Can not withdraw Zero amount')

        amount = round(amount_in_wei / 10 ** 18, 6)

        self.logger_msg(*self.client.acc_info, msg=f'Unwrap {amount:.6f} {self.client.token}')

        tx_params = await self.client.prepare_transaction()

        transaction = await weth_contract.functions.withdraw(
            amount_in_wei
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    async def transfer_eth(self):
        from utils.tools import get_wallet_for_transfer

        eth_client = None
        try:
            eth_client = await self.client.new_client("Ethereum")
            transfer_address = get_wallet_for_transfer(self)

            amount_in_wei, amount = await eth_client.get_smart_amount(Settings.TRANSFER_ETH_AMOUNT)

            transaction = (await eth_client.prepare_transaction(value=int(amount_in_wei))) | {
                'to': eth_client.w3.to_checksum_address(transfer_address),
                'data': '0x'
            }

            self.logger_msg(*eth_client.acc_info, msg=f"Transfer {amount} ETH to {transfer_address} address")

            return await eth_client.send_transaction(transaction)
        finally:
            await eth_client.session.close()

    @helper
    async def transfer_bera(self):
        from utils.tools import get_wallet_for_transfer

        transfer_address = get_wallet_for_transfer(self)

        amount_in_wei, amount = await self.client.get_smart_amount(Settings.TRANSFER_BERA_AMOUNT)

        transaction = (await self.client.prepare_transaction(value=int(amount_in_wei))) | {
            'to': self.client.w3.to_checksum_address(transfer_address),
            'data': '0x'
        }

        self.logger_msg(*self.client.acc_info, msg=f"Transfer {amount} BERA to {transfer_address} address")

        return await self.client.send_transaction(transaction)

    @network_handler
    async def balance_searcher(
            self, chains, tokens=None, native_check: bool = False, silent_mode: bool = False,
            balancer_mode: bool = False, random_mode: bool = False, wrapped_tokens: bool = False,
            need_token_name: bool = False, raise_handle: bool = False, without_error: bool = False
    ):
        index = 0
        clients = [await self.client.new_client(chain) for chain in chains]
        try:
            if native_check:
                tokens = [client.token for client in clients]
            elif wrapped_tokens:
                tokens = [f'W{client.token}' for client in clients]

            balances = []
            for client, token in zip(clients, tokens):
                balances.append(await client.get_token_balance(
                    token_name=token,
                    without_error=without_error
                ) if token in TOKENS_PER_CHAIN[client.network.name] or token in [f'W{client.token}', client.token] else (0, 0, ''))

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
                            token_price = await self.get_token_price(token_name)
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

            for index_client, client in enumerate(clients):
                if index_client != index:
                    await client.session.close()

            if not silent_mode:
                clients[index].logger_msg(
                    *clients[index].acc_info,
                    msg=f"Detected {round(balances[index][1], 5)} {tokens[index]} in {clients[index].network.name}",
                    type_msg='success'
                )

            if balances[index][1] < Settings.MIN_AMOUNT_TO_BRIDGE:
                raise SoftwareExceptionWithoutRetry('Can not return zero amount')

            return clients[index], index, balances[index][1], balances[index][0], balances_in_usd[index]

        finally:
            for index_client, client in enumerate(clients):
                if index_client != index:
                    await client.session.close()
