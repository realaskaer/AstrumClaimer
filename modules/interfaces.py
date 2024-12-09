import asyncio
import json as js

import aiohttp.client_exceptions
from loguru import logger
from sys import stderr
from datetime import datetime
from abc import ABC
from aiohttp import ClientSession, TCPConnector
from random import uniform
from dev import GeneralSettings, Settings
from config import TOKEN_API_INFO
from aiohttp_socks import ProxyConnector
from utils.tools import network_handler
from version import VERSION


def get_user_agent():
    random_version = f"{uniform(520, 540):.2f}"
    return (f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version} (KHTML, like Gecko)'
            f' Chrome/128.0.0.0 Safari/{random_version} Edg/128.0.0.0')


class PriceImpactException(Exception):
    pass


class BlockchainException(Exception):
    pass


class SoftwareException(Exception):
    pass


class SoftwareExceptionWithoutRetry(Exception):
    pass


class FaucetException(Exception):
    pass


class WrongGalxeCode(Exception):
    pass


class SoftwareExceptionHandled(Exception):
    pass


class CriticalException(Exception):
    pass


class BlockchainExceptionWithoutRetry(Exception):
    pass


class BridgeExceptionWithoutRetry(Exception):
    pass


class Logger(ABC):
    def __init__(self):
        self.logger = logger
        self.logger.remove()
        logger_format = "<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>"
        self.logger.add(stderr, format=logger_format)
        date = datetime.today().date()
        self.logger.add(f"./data/logs/{date}.log", rotation="500 MB", level="INFO", format=logger_format)
        self.connection = None

    def logger_msg(self, account_name, address, network_name=None, msg=None, type_msg: str = 'info'):
        class_name = self.__class__.__name__
        software_chain = network_name if network_name else 'OmniChain'
        acc_info = '1/1'
        module_info = '1/1'
        if account_name:
            try:
                with open(Settings.PROGRESS_FILE_PATH) as file:
                    wallets_progress_data = js.load(file)
                keys_list = list(wallets_progress_data.keys())
                acc_index = keys_list.index(account_name) + 1
                accs_count = len(wallets_progress_data)
                acc_info = f'{acc_index}/{accs_count}'
                module_index = wallets_progress_data[account_name]['current_step']
                modules_count = len(wallets_progress_data[account_name]['route'])
                module_info = f'{module_index}/{modules_count}'
            except (ValueError, TypeError):
                acc_info = "0/0"
                module_info = "0/0"

        if account_name is None and address is None:
            info = f'[AstrumClaimer] | {software_chain} | {class_name} |'
        elif account_name is not None and address is None:
            info = f'[{acc_info}] | [{account_name}] | [{module_info}] | v{VERSION} | {software_chain} | {class_name} |'
        else:
            info = f'[{acc_info}] | [{account_name}] | [{module_info}] | {address} | {software_chain} | {class_name} |'

        if type_msg == 'info':
            self.logger.info(f"{info} {msg}")
        elif type_msg == 'error':
            self.logger.error(f"{info} {msg}")
        elif type_msg == 'success':
            self.logger.success(f"{info} {msg}")
        elif type_msg == 'warning':
            self.logger.warning(f"{info} {msg}")


class RequestClient(ABC):
    def __init__(self, client):
        self.client = client

    async def make_request(
            self, method: str = 'GET', url: str = None, headers: dict = None, params: dict = None, data: str = None,
            json: dict = None, module_name: str = 'Request'
    ):

        errors = None

        total_time = 0
        timeout = 360
        while True:
            try:
                async with self.client.session.request(
                        method=method, url=url, headers=headers, data=data, params=params, json=json
                ) as response:
                    if response.status in [200, 201]:
                        if response.content_type == 'text/plain':
                            text_data = await response.text()
                            data = js.loads(text_data)
                        elif response.content_type == 'text/html':
                            data = await response.text()
                        else:
                            data = await response.json()
                        if isinstance(data, dict):
                            errors = data.get('errors')
                        elif isinstance(data, list) and isinstance(data[0], dict):
                            errors = data[0].get('errors')

                        if not errors:
                            return data
                        elif 'You have exceeded the rate limit. Please wait' in f"{errors}":
                            raise SoftwareExceptionWithoutRetry(
                                f"Can`t get $BERA: {errors}")
                        else:
                            raise SoftwareException(
                                f"Bad request to {self.__class__.__name__}({module_name}) API: {errors[0]['message']}")

                    raise SoftwareException(
                        f"Bad request to {self.__class__.__name__}({module_name}) API: {await response.text()}")
            except aiohttp.client_exceptions.ServerDisconnectedError as error:
                total_time += 15
                await asyncio.sleep(15)
                if total_time > timeout:
                    raise SoftwareException(error)
                continue
            except SoftwareExceptionWithoutRetry as error:
                raise SoftwareExceptionWithoutRetry(error)
            except Exception as error:
                raise SoftwareException(error)

    async def get_token_price_via_gate(self, token_name: str) -> float:

        url = f'https://api.gateio.ws/api/v4/spot/tickers'

        params = {
            'currency_pair': f'{token_name}_USDT'
        }

        async with ClientSession(
                connector=ProxyConnector.from_url(f"http://{GeneralSettings.MAIN_PROXY}", )
                if GeneralSettings.MAIN_PROXY != '' else TCPConnector()
        ) as session:
            async with session.request(method='GET', url=url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data[0]['last'])
                elif response.status == 429:
                    self.client.logger_msg(
                        *self.client.acc_info, msg='Gate API got rate limit. Next try in 300 second',
                        type_msg='warning')
                    await asyncio.sleep(300)
                raise SoftwareException(f'Bad request to Gate API: {response.status}')

    async def get_token_price_via_okx(self, token_name: str) -> float:

        url = f'https://www.okx.com/api/v5/market/ticker'

        params = {
            'instId': f'{token_name}-USDT'
        }

        async with ClientSession(
                connector=ProxyConnector.from_url(f"http://{GeneralSettings.MAIN_PROXY}", )
                if GeneralSettings.MAIN_PROXY != '' else TCPConnector()
        ) as session:
            async with session.request(method='GET', url=url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['data'][0]['last'])
                elif response.status == 429:
                    self.client.logger_msg(
                        *self.client.acc_info, msg='OKX API got rate limit. Next try in 300 second',
                        type_msg='warning')
                    await asyncio.sleep(300)
                raise SoftwareException(f'Bad request to OKX API: {response.status}')

    async def get_token_price_via_bybit(self, token_name: str) -> float:

        url = f'https://api.bybit.com/spot/v3/public/quote/ticker/price?symbol={token_name}USDT'

        params = {
            'symbol': f'{token_name}USDT'
        }

        async with ClientSession(
                connector=ProxyConnector.from_url(f"http://{GeneralSettings.MAIN_PROXY}", )
                if GeneralSettings.MAIN_PROXY != '' else TCPConnector()
        ) as session:
            async with session.request(method='GET', url=url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['result']['price'])
                elif response.status == 429:
                    self.client.logger_msg(
                        *self.client.acc_info, msg='Bybit API got rate limit. Next try in 300 second',
                        type_msg='warning')
                    await asyncio.sleep(300)
                raise SoftwareException(f'Bad request to Bybit API: {response.status}')

    async def get_token_price_via_binance(self, token_name: str) -> float:
        if 'ETH' in token_name:
            token_name = 'ETH'
        elif 'MATIC' in token_name:
            token_name = 'MATIC'
        elif 'TIA' in token_name:
            token_name = 'TIA'
        elif 'BNB' in token_name:
            token_name = 'BNB'

        url = f'https://api.binance.com/api/v3/ticker/price'

        params = {
            'symbol': f'{token_name}USDT'
        }

        async with ClientSession(
                connector=ProxyConnector.from_url(f"http://{GeneralSettings.MAIN_PROXY}", )
                if GeneralSettings.MAIN_PROXY != '' else TCPConnector()
        ) as session:
            async with session.request(method='GET', url=url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
                elif response.status == 429:
                    self.client.logger_msg(
                        *self.client.acc_info, msg='Binance API got rate limit. Next try in 300 second',
                        type_msg='warning')
                    await asyncio.sleep(300)
                raise SoftwareException(f'Bad request to Binance API: {response.status}')

    @network_handler
    async def get_token_price(self, token_name: str, vs_currency: str = 'usd') -> float:

        if token_name in TOKEN_API_INFO['stables']:
            return 1.0

        if token_name not in TOKEN_API_INFO['coingecko']:
            if token_name in TOKEN_API_INFO['binance']:
                return await self.get_token_price_via_binance(token_name)
            elif token_name in TOKEN_API_INFO['gate']:
                return await self.get_token_price_via_gate(token_name)
            else:
                raise SoftwareExceptionWithoutRetry(
                    f"CEX on which the rate for {token_name} will be calculated hasn't been determined"
                )
        else:
            await asyncio.sleep(10)
            url = 'https://api.coingecko.com/api/v3/simple/price'

            token_name = TOKEN_API_INFO['coingecko'][token_name]

            params = {
                'ids': f'{token_name}',
                'vs_currencies': f'{vs_currency}'
            }

            async with ClientSession(
                    connector=ProxyConnector.from_url(f"http://{GeneralSettings.MAIN_PROXY}", )
                    if GeneralSettings.MAIN_PROXY != '' else TCPConnector()
            ) as session:
                async with session.request(method='GET', url=url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data[token_name][vs_currency])
                    elif response.status == 429:
                        self.client.logger_msg(
                            *self.client.acc_info, msg='CoinGecko API got rate limit. Next try in 300 second',
                            type_msg='warning')
                        await asyncio.sleep(300)
                    raise SoftwareException(f'Bad request to CoinGecko API: {response.status}')
