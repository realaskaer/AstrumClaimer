import io
import json
import os
import random
import asyncio
import functools
import traceback

import httpx
import msoffcrypto
import pandas as pd
from getpass import getpass

from solana.exceptions import SolanaRpcException
from termcolor import cprint
from aiohttp import ClientError, ClientConnectorError
from utils.networks import EthereumRPC
from dev import GeneralSettings, Settings
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import ContractLogicError
from python_socks._protocols.errors import ReplyError
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from python_socks import ProxyError, ProxyTimeoutError, ProxyConnectionError


async def sleep(self, min_time=None, max_time=None):
    if min_time is None:
        min_time = GeneralSettings.SLEEP_TIME_MODULES[0]
    if max_time is None:
        max_time = GeneralSettings.SLEEP_TIME_MODULES[1]
    duration = random.randint(min_time, max_time)
    print()
    self.logger_msg(*self.client.acc_info, msg=f"💤 Sleeping for {duration} seconds")
    await asyncio.sleep(duration)


def get_accounts_data():
    try:
        decrypted_data = io.BytesIO()
        with open(GeneralSettings.EXCEL_FILE_PATH, 'rb') as file:
            if GeneralSettings.EXCEL_PASSWORD:
                cprint('⚔️ Enter the password degen', color='light_blue')
                password = getpass()
                office_file = msoffcrypto.OfficeFile(file)

                try:
                    office_file.load_key(password=password)
                except msoffcrypto.exceptions.DecryptionError:
                    cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️', color='light_red', attrs=["blink"])
                    raise DecryptionError('Incorrect password')

                try:
                    office_file.decrypt(decrypted_data)
                except msoffcrypto.exceptions.InvalidKeyError:
                    cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️', color='light_red', attrs=["blink"])
                    raise InvalidKeyError('Incorrect password')

                except msoffcrypto.exceptions.DecryptionError:
                    cprint('\n⚠️ Set password on your Excel file first! ⚠️', color='light_red', attrs=["blink"])
                    raise DecryptionError('Excel without password')

                office_file.decrypt(decrypted_data)

                try:
                    wb = pd.read_excel(decrypted_data, sheet_name=GeneralSettings.EXCEL_PAGE_NAME)
                except ValueError as error:
                    cprint('\n⚠️ Wrong page name! ⚠️', color='light_red', attrs=["blink"])
                    raise ValueError(f"{error}")
            else:
                try:
                    wb = pd.read_excel(file, sheet_name=GeneralSettings.EXCEL_PAGE_NAME)
                except ValueError as error:
                    cprint('\n⚠️ Wrong page name! ⚠️', color='light_red', attrs=["blink"])
                    raise ValueError(f"{error}")

            wb = wb.where(pd.notnull(wb), None)

            accounts_data = {}
            accounts_data['accounts'] = {}
            for index, row in wb.iterrows():
                if row['Name']:
                    accounts_data['accounts'] |= {
                        f"{row['Name']}": {
                            "evm_private_key": row["Private Key"].strip(),
                            "proxy": row["Proxy"].strip(),
                            "evm_deposit_address": row['Transfer address'],
                        }
                    }

            return accounts_data
    except (DecryptionError, InvalidKeyError, DecryptionError, ValueError):
        os.system("pause")

    except ImportError:
        cprint(f'\nAre you sure about EXCEL_PASSWORD in general_settings.py?', color='light_red')
        os.system("pause")

    except Exception as error:
        cprint(f'\nError in <get_accounts_data> function! Error: {error}\n', color='light_red')
        os.system("pause")


def clean_progress_file():
    with open(Settings.PROGRESS_FILE_PATH, 'w') as file:
        file.truncate(0)


def progress_file_is_not_empty():
    if not os.path.exists(Settings.PROGRESS_FILE_PATH):
        with open(Settings.PROGRESS_FILE_PATH, 'w') as file:
            json.dump({}, file)
        return False
    else:
        with open(Settings.PROGRESS_FILE_PATH, 'r') as file:
            route_dict = json.load(file)
        if route_dict:
            return True
        else:
            return False


def network_handler(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        from modules.interfaces import SoftwareException

        k = 0
        client_object = False
        while True:
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:
                from modules import EVMClient
                msg = f'{error}'
                k += 1

                if hasattr(self, 'client') and isinstance(self.client, EVMClient):
                    client_info = self.client.acc_info
                    client_object = True
                else:
                    if isinstance(self, EVMClient):
                        client_info = self.acc_info
                    else:
                        client_info = None, None

                if k % 2 == 0:
                    if int(k / 2) < GeneralSettings.PROXY_REPLACEMENT_COUNT:
                        if client_object:
                            await self.client.change_proxy()
                            await self.client.change_rpc()
                        else:
                            await self.change_proxy()
                            await self.change_rpc()
                        continue
                    else:
                        raise SoftwareException(
                            f'Account can not find a good proxy {GeneralSettings.PROXY_REPLACEMENT_COUNT} times'
                        )

                if isinstance(error, KeyError):
                    self.logger_msg(*client_info, msg=msg, type_msg='error')
                    return False

                elif any(keyword in str(error) for keyword in (
                         '502 Bad Gateway', 'Invalid proxy', 'NO_HOST_CONNECTION', 'www.cloudflare.com',
                        '403 Forbidden', '504 Gateway', '503 Service', '500 Internal Server',
                        '[SSL: WRONG_VERSION_NUMBER] wrong version number', 'no such host',
                        '417 Expectation Failed', '407 Proxy Authentication Required',
                        '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed',
                        'connection reset by peer', 'certificate signed by unknown authority',
                        'server gave HTTP response to HTTPS client', 'EOF', 'the target machine actively refused it',
                        'tls: handshake failure', 'tls: bad record MAC', '503 No exit node', 'Bad Request',
                        'Proxy connection timed out', '502 NO_HOST_CONNECTION'
                )):
                    self.logger_msg(*client_info, msg=msg, type_msg='warning')
                    if client_object:
                        await self.client.change_proxy()
                    else:
                        await self.change_proxy()
                    continue

                elif 'Error code' in str(error):
                    msg = f'{error}. Will try again...'

                elif 'Server disconnected' in str(error):
                    msg = f'{error}. Will try again...'

                elif 'StatusCode.UNAVAILABLE' in str(error):
                    msg = f'RPC got autism response, will try again...'

                elif '<html lang="en">' in str(error):
                    msg = f'Proxy got non-permanent ban, will try again...'

                elif isinstance(error, (ClientError, asyncio.TimeoutError, ProxyError, ReplyError)):
                    msg = f"Connection to RPC is not stable. Will try again..."

                else:
                    raise error

                self.logger_msg(*client_info, msg=msg, type_msg='warning')
                await asyncio.sleep(10)

        return False
    return wrapper


def helper(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        from modules.interfaces import (
            BlockchainException, SoftwareException, SoftwareExceptionWithoutRetry,
            BlockchainExceptionWithoutRetry, SoftwareExceptionHandled, InsufficientBalanceException,
            SoftwareExceptionWithProxy
        )

        attempts = 0
        k = 0

        no_sleep_flag = False
        while attempts <= GeneralSettings.MAXIMUM_RETRY:
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:
                attempts += 1
                k += 1
                msg = f'{error}'
                # traceback.print_exc()

                if isinstance(error, KeyError):
                    msg = f"Parameter '{error}' for this module is not exist in software!"
                    self.logger_msg(*self.client.acc_info, msg=msg, type_msg='error')
                    return False

                elif not isinstance(error, asyncio.exceptions.IncompleteReadError) and "0 bytes read" in str(error):
                    msg = f'Probably SOCKS5 request was bad'
                    self.logger_msg(*self.client.acc_info, msg=msg, type_msg='warning')
                    await self.client.change_proxy()
                    continue

                elif 'StatusCode.UNAVAILABLE' in str(error):
                    msg = f'RPC got autism response, will try again......'

                elif 'insufficient funds' in str(error):
                    msg = f'Insufficient funds to complete transaction'

                elif 'gas required exceeds' in str(error):
                    msg = f'Not enough {self.client.network.token} for transaction gas payment'

                elif isinstance(error, SoftwareExceptionHandled):
                    self.logger_msg(*self.client.acc_info, msg=f"{error}", type_msg='warning')
                    return True

                elif isinstance(error, (SoftwareExceptionWithoutRetry, BlockchainExceptionWithoutRetry)):
                    self.logger_msg(self.client.account_name, None, msg=msg, type_msg='error')
                    return False

                elif isinstance(error, (SoftwareException, InsufficientBalanceException)):
                    msg = f'{error}'

                elif isinstance(error, ContractLogicError):
                    msg = f"Contract reverted: {error}"

                elif isinstance(error, SoftwareExceptionWithProxy):
                    await self.client.change_proxy()

                elif isinstance(error, BlockchainException):
                    if 'insufficient funds' not in str(error):
                        self.logger_msg(
                            self.client.account_name,
                            None, msg=f'Maybe problem with node: {self.client.rpc_url}', type_msg='warning'
                        )
                        await self.client.change_rpc()

                elif isinstance(error, (
                        ClientError, asyncio.TimeoutError, ProxyError, ReplyError, ConnectionResetError,
                        ProxyTimeoutError, ProxyConnectionError, httpx.ConnectTimeout, httpx.RemoteProtocolError,
                        asyncio.exceptions.IncompleteReadError, ClientConnectorError, httpx.ProxyError,
                        SolanaRpcException
                )) or any(keyword in msg for keyword in (
                    '502 Bad Gateway', 'Invalid proxy', 'NO_HOST_CONNECTION', 'www.cloudflare.com',
                    '403 Forbidden', '504 Gateway', '503 Service', '500 Internal Server',
                    '[SSL: WRONG_VERSION_NUMBER] wrong version number', 'no such host',
                    '417 Expectation Failed', '407 Proxy Authentication Required',
                    '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed',
                    'connection reset by peer', 'certificate signed by unknown authority',
                    'server gave HTTP response to HTTPS client', 'EOF', 'the target machine actively refused it',
                    'tls: handshake failure', 'tls: bad record MAC', '503 No exit node', 'Bad Request',
                    'Proxy connection timed out', '502 NO_HOST_CONNECTION', 'failed to do request:',
                    '503 Service Unavailable'
                )):

                    if 'www.cloudflare.com' in msg:
                        msg = f'Response came from Cloudflare server(likely IP or Server got problem)'
                    elif '403 Forbidden' in msg:
                        msg = f'Probably your IP got problem by protection system'
                    elif '0 bytes read' in msg:
                        msg = f'Probably SOCKS5 request was bad'
                    elif '502 Bad Gateway' in msg or '504 Gateway' in msg or '503 Service' in msg or '500 Internal Server' in msg:
                        msg = f'API Server or proxy is not available now'
                    elif 'SSL' in msg or 'certificate signed by unknown authority' in msg:
                        msg = f"Your proxy SSL version is bad"
                    elif 'connection reset by peer' in msg:
                        msg = f"API Server reset connection by peer"
                    elif 'no such host' in msg or 'the target machine actively refused it' in msg:
                        msg = f'Probably your DNS domains is down, please set 8.8.8.8 and 8.8.4.4, and restart PC. If error still exist, try use VPN or another internet provider'
                    if not msg:
                        msg = 'Your proxy is probably not available'

                    self.logger_msg(*self.client.acc_info, msg=msg, type_msg='warning')
                    await self.client.change_proxy()
                    continue

                else:
                    msg = f'Unknown Error: {error}'
                    traceback.print_exc()

                self.logger_msg(
                    self.client.account_name,
                    None,
                    msg=f"{msg} | Try[{attempts}/{GeneralSettings.MAXIMUM_RETRY + 1}]",
                    type_msg='error'
                )

                if attempts > GeneralSettings.MAXIMUM_RETRY:
                    self.logger_msg(
                        self.client.account_name, None,
                        msg=f"Tries are over, software will stop module\n", type_msg='error'
                    )
                    break
                else:
                    if not no_sleep_flag:
                        await sleep(self, *GeneralSettings.SLEEP_TIME_RETRY)

        return False

    return wrapper


def get_max_gwei_setting():
    file_path = './data/services/maximum_gwei.json'
    data = {}

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data['maximum_gwei'] = GeneralSettings.MAXIMUM_GWEI

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    return data['maximum_gwei']


def gas_checker(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if GeneralSettings.GAS_CONTROL:
            await asyncio.sleep(1)
            print()
            counter = 0

            self.logger_msg(self.client.account_name, None, msg=f"Checking for gas price")

            if self.client.network.name != 'Solana':
                w3 = AsyncWeb3(AsyncHTTPProvider(
                    random.choice(EthereumRPC.rpc), request_kwargs=self.client.request_kwargs)
                )
            else:
                return await func(self, *args, **kwargs)
            while True:
                try:
                    gas = round(AsyncWeb3.from_wei(await w3.eth.gas_price, 'gwei'), 3)

                    if gas < get_max_gwei_setting():

                        self.logger_msg(
                            self.client.account_name, None, msg=f"{gas} Gwei | Gas price is good", type_msg='success')
                        return await func(self, *args, **kwargs)

                    else:

                        counter += 1
                        self.logger_msg(
                            self.client.account_name, None,
                            msg=f"{gas} Gwei | Gas is too high. Next check in {GeneralSettings.SLEEP_TIME_GAS} second",
                            type_msg='warning'
                        )

                        await asyncio.sleep(GeneralSettings.SLEEP_TIME_GAS)
                except (ClientError, asyncio.TimeoutError, ProxyError, ReplyError):
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Connection to RPC is not stable. Will try again in 10 second...",
                        type_msg='warning'
                    )
                    if counter % 2 == 0:
                        await self.client.change_proxy()
                        await self.client.change_rpc()
                    else:
                        await asyncio.sleep(10)

        return await func(self, *args, **kwargs)

    return wrapper
