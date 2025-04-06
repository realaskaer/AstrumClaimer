import json
import random
import time
import traceback

from termcolor import colored
from dev import GeneralSettings, Settings
from web3 import AsyncWeb3, AsyncHTTPProvider
from modules.interfaces import SoftwareExceptionWithoutRetry, Logger, SoftwareException


class ClientUtils(Logger):
    def __init__(self, client):
        Logger.__init__(self)
        self.client = client

    async def _change_w3(self, proxy: str, rpc_url: str):
        from .evm_client import EVMClient
        from .solana_client import SolanaClient

        if isinstance(self.client, EVMClient):

            self.client.request_kwargs = {
                "proxy": f"http://{proxy}", "verify_ssl": False
            } if proxy else {"verify_ssl": False}

            self.client.rpc_url = rpc_url

            self.client.w3 = AsyncWeb3(
                AsyncHTTPProvider(endpoint_uri=rpc_url, request_kwargs=self.client.request_kwargs)
            )
        elif isinstance(self.client, SolanaClient):
            from .solana_client import CustomAsyncClient

            self.client.rpc_url = rpc_url
            self.client.w3 = CustomAsyncClient(endpoint=rpc_url, proxy=f"http://{proxy}")
        else:
            self.logger_msg(
                *self.client.acc_info, msg=f'Software do not support change proxy on {type(self.client)}',
                type_msg='warning'
            )
            return True

    async def change_rpc(self):
        self.logger_msg(*self.client.acc_info, msg=f'Trying to replace old RPC: {self.client.rpc_url}', type_msg='warning')

        fresh_rpc_list = [rpc_url for rpc_url in self.client.rpc_list if rpc_url != self.client.rpc_url]
        if len(self.client.rpc_list) != 1 and fresh_rpc_list:
            new_rpc_url = random.choice(fresh_rpc_list)

            await self._change_w3(proxy=self.client.proxy, rpc_url=new_rpc_url)

            self.logger_msg(
                *self.client.acc_info, msg=f'RPC successfully replaced. New RPC: {new_rpc_url}', type_msg='success'
            )
        else:
            self.logger_msg(
                *self.client.acc_info,
                msg=f'This network has only 1 RPC, no replacement is possible', type_msg='warning'
            )

    async def change_proxy(self):
        from config import ACCOUNTS_DATA

        proxies = [proxy for proxy in ACCOUNTS_DATA['proxies_pool']]

        self.logger_msg(
            *self.client.acc_info, msg=f'Trying to replace old proxy: {self.client.proxy}', type_msg='warning'
        )

        if len(set(proxies)) > 1:
            fresh_proxy = random.choice(proxies)

            # proxies.remove(fresh_proxy)
            # ACCOUNTS_DATA['proxies_pool'] = [encrypt_data(proxy) for proxy in proxies]

            self.client.proxy = fresh_proxy
            self.client.proxy_url = f"http://{fresh_proxy}"

            await self._change_w3(proxy=fresh_proxy, rpc_url=self.client.rpc_url)

            self.logger_msg(
                *self.client.acc_info, msg=f'Proxy successfully replaced. New Proxy: {fresh_proxy}', type_msg='success'
            )
            return
        else:
            self.logger_msg(
                *self.client.acc_info,
                msg=f'All proxies were used, please add more proxies into table via this guide: https://docs.astrum.foundation/nachalo-raboty/nastroika-softa/zapolnenie-tablicy',
                type_msg='warning'
            )
