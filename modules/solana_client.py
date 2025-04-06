import httpx
import random
import base58
import asyncio

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from config import TOTAL_USER_AGENT
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder
from typing import Optional, Dict
from dev import GeneralSettings, Settings
from solana.rpc.commitment import Commitment
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solana.rpc.providers.core import DEFAULT_TIMEOUT
from solders.rpc.responses import GetTokenAccountsByOwnerResp
from solana.rpc.providers.async_http import AsyncHTTPProvider

from modules.client_utils import ClientUtils
from modules.interfaces import SoftwareException, Logger, RequestClient


class CustomAsyncHTTPProvider(AsyncHTTPProvider):
    def __init__(
            self,
            endpoint=None,
            extra_headers=None,
            timeout: float = DEFAULT_TIMEOUT,
            proxy: Optional[Dict[str, str]] = None,
    ):
        super().__init__(endpoint=endpoint, extra_headers=extra_headers)
        self.session = httpx.AsyncClient(timeout=timeout, proxy=proxy)


class CustomAsyncClient(AsyncClient):
    def __init__(
            self,
            endpoint: Optional[str] = None,
            commitment: Optional[Commitment] = None,
            timeout: float = 10,
            extra_headers: Optional[Dict[str, str]] = None,
            proxy: Optional[str] = None,
    ):
        super().__init__(commitment=commitment)
        self._provider = CustomAsyncHTTPProvider(endpoint, timeout=timeout, extra_headers=extra_headers, proxy=proxy)


class SolanaClient(Logger, RequestClient):
    def __init__(self, module_input_data: dict):
        Logger.__init__(self)

        self.module_input_data = module_input_data

        self.network = module_input_data['network']
        self.eip1559_support = self.network.eip1559_support
        self.token = self.network.token
        self.explorer = self.network.explorer
        self.chain_id = self.network.chain_id
        self.rpc_list = self.network.rpc
        self.rpc_url = random.choice(self.rpc_list)

        if not module_input_data['evm_private_key']:
            raise SoftwareException("Solana private key is missing, please fill it into accounts data!")

        self.wallet: Keypair = Keypair.from_base58_string(module_input_data['evm_private_key'])
        self.proxy = module_input_data['proxy']
        self.proxy_url = "http" + f"://{self.proxy}"

        headers = {
            'accept': '*/*',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Google Chrome";v="134", "Chromium";v="134", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            # 'solana-client': 'js/1.95.8',
            'user-agent': TOTAL_USER_AGENT,
        }

        self.w3 = CustomAsyncClient(
            endpoint=self.rpc_url, extra_headers=headers, proxy=self.proxy_url if self.proxy else None
        )

        self.client = self
        self.address = self.wallet.pubkey()
        self.account_name = str(module_input_data['account_name'])
        self.acc_info = self.account_name, self.address, self.network.name

    async def change_rpc(self):
        return await ClientUtils(self).change_rpc()

    async def change_proxy(self):
        return await ClientUtils(self).change_proxy()

    async def smart_sleep(self, sleep_settings, without_setting:bool = False):
        if GeneralSettings.SLEEP_MODE or without_setting:
            duration = round(random.uniform(*sleep_settings), 2)
            self.logger_msg(*self.acc_info, msg=f"💤 Sleeping for {duration} seconds\n")
            await asyncio.sleep(duration)

    def sign_message(self, message: str):
        signing_key = SigningKey(self.wallet.secret())
        signed = signing_key.sign(message.encode())
        signature = base58.b58encode(signed.signature).decode('utf-8')

        return signature

    @staticmethod
    def custom_round(number: int | float | list | tuple, decimals: int = None) -> float:
        if not decimals:
            decimals = Settings.TOTAL_DECIMALS
        if not decimals:
            decimals = 6

        if isinstance(number, (list, tuple)):
            number = random.uniform(*number)
        number = float(number)
        str_number = f"{number:.18f}".split('.')
        if len(str_number) != 2:
            return round(number, decimals)
        str_number_to_round = str_number[1]
        rounded_number = str_number_to_round[:decimals]
        final_number = float('.'.join([str_number[0], rounded_number]))
        return final_number

    @staticmethod
    async def simulate_transfer(**_) -> float:
        return 0

    @staticmethod
    def get_normalize_error(error: Exception) -> Exception | str:
        try:
            if isinstance(error.args[0], dict):
                error = error.args[0].get('message', error)
            return error
        except:
            return error

    async def find_token_account(self, token_address: str):
        response = await self.w3.get_token_accounts_by_owner(
            self.address, TokenAccountOpts(mint=Pubkey.from_string(token_address)),
        )

        if isinstance(response, GetTokenAccountsByOwnerResp):
            accounts = response.value
            if not accounts:
                raise SoftwareException(
                    f"Error getting token account for {token_address}. Probably owner has no specified token"
                )
            return str(accounts[0].pubkey)
        else:
            raise SoftwareException(f"Error getting token account for {token_address}: {response}")

    @staticmethod
    def to_decimals(number: int | float | str, decimals: int = 9) -> int:
        return int(number * 10 ** decimals)

    @staticmethod
    async def sign_ed25519(message_data, secret_key):
        signing_key = SigningKey(secret_key[:32], encoder=RawEncoder)
        return signing_key.sign(message_data).signature
