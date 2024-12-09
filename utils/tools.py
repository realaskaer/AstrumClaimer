import io
import json
import os
import random
import asyncio
import functools
import traceback
import msoffcrypto
import pandas as pd
from getpass import getpass
from aiohttp import ClientError
from python_socks._protocols.errors import ReplyError
from termcolor import cprint
from web3 import AsyncWeb3, AsyncHTTPProvider
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from python_socks import ProxyError
from utils.networks import EthereumRPC
from dev import GeneralSettings, Settings


async def sleep(self, min_time=None, max_time=None):
    if min_time is None:
        min_time = GeneralSettings.SLEEP_TIME_MODULES[0]
    if max_time is None:
        max_time = GeneralSettings.SLEEP_TIME_MODULES[1]
    duration = random.randint(min_time, max_time)
    print()
    self.logger_msg(*self.client.acc_info, msg=f"💤 Sleeping for {duration} seconds")
    await asyncio.sleep(duration)


def create_transfer_list():
    from config import (
        ACCOUNT_NAMES, TRANSFERS_ADDRESSES
    )

    file_data = {}
    file_path = 'transfers_addresses'

    if ACCOUNT_NAMES and TRANSFERS_ADDRESSES:
        with open(f'./data/services/{file_path}.json', 'w') as file:
            for account_name, cex_wallet in zip(ACCOUNT_NAMES, TRANSFERS_ADDRESSES):
                file_data[str(account_name)] = str(cex_wallet).strip()
            json.dump(file_data, file, indent=4)
        cprint(f'✅ Successfully added and saved addresses for transfers', 'light_blue')
        cprint(f'⚠️ Check all transfers wallets by yourself to avoid problems',
               'light_yellow', attrs=["blink"])
    else:
        cprint('❌ Put your wallets into files, before running this function', 'light_red')


def get_wallet_for_transfer(self):
    file_path = f'transfers_addresses'

    try:
        with open(f'./data/services/{file_path}.json') as file:
            from json import load
            transfers_addresses_list = load(file)
            transfer_address = transfers_addresses_list[self.client.account_name]
        return transfer_address
    except json.JSONDecodeError:
        raise RuntimeError(f"Bad data in {file_path}.json")
    except Exception as error:
        raise RuntimeError(f'There is no wallet listed for transfers: {error}')


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

            accounts_data = {}
            for index, row in wb.iterrows():
                account_name = row["Name"]
                private_key = row["Private Key"]
                proxy = row["Proxy"]
                transfer_address = row["Transfer address"]

                accounts_data[int(index) + 1] = {
                    "account_number": account_name,
                    "private_key": private_key,
                    "proxy": proxy,
                    "transfer_address": transfer_address,
                }

            acc_names, private_keys, proxies, transfer_addresses, = [], [], [], []
            for k, v in accounts_data.items():
                acc_names.append(v['account_number'] if isinstance(v['account_number'], (int, str)) else None)
                private_keys.append(v['private_key'])
                proxies.append(v['proxy'] if isinstance(v['proxy'], str) else None)
                transfer_addresses.append(v['transfer_address'] if isinstance(v['transfer_address'], str) else None)

            acc_names = [str(item).strip() for item in acc_names if item is not None]
            proxies = [str(item).strip() for item in proxies if item is not None]
            transfer_addresses = [str(item).strip() for item in transfer_addresses if item is not None]

            return acc_names, private_keys, proxies, transfer_addresses
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
                from modules import Client
                msg = f'{error}'
                k += 1

                if hasattr(self, 'client') and isinstance(self.client, Client):
                    client_info = self.client.acc_info
                    client_object = True
                else:
                    if isinstance(self, Client):
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
                        'Bad Gateway', '403', 'SSL', 'Invalid proxy', 'rate limit', '429', '407', '503'
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
            BlockchainExceptionWithoutRetry, SoftwareExceptionHandled, FaucetException
        )

        attempts = 0
        k = 0

        no_sleep_flag = False
        try:
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

                    elif any(keyword in str(error) for keyword in (
                            'Bad Gateway', '403', 'SSL', 'Invalid proxy', 'rate limit', '429', '407', '503'
                    )):
                        self.logger_msg(*self.client.acc_info, msg=msg, type_msg='warning')
                        await self.client.change_proxy()
                        continue

                    elif 'Error code' in str(error):
                        msg = f'{error}. Will try again...'

                    elif 'Server disconnected' in str(error):
                        msg = f'{error}. Will try again...'

                    elif 'StatusCode.UNAVAILABLE' in str(error):
                        msg = f'RPC got autism response, will try again......'

                    elif '<html lang="en">' in str(error):
                        msg = f'Proxy got non-permanent ban, will try again...'

                    elif isinstance(error, SoftwareExceptionHandled):
                        self.logger_msg(*self.client.acc_info, msg=f"{error}", type_msg='warning')
                        return True

                    elif isinstance(error, FaucetException):
                        if not GeneralSettings.BREAK_FAUCET:
                            self.logger_msg(*self.client.acc_info, msg=f"{error}", type_msg='warning')
                            await self.client.change_proxy()
                            continue
                        else:
                            self.logger_msg(*self.client.acc_info, msg=f"{error}", type_msg='warning')
                            raise SoftwareException(f"{error}")

                    elif isinstance(error, (SoftwareExceptionWithoutRetry, BlockchainExceptionWithoutRetry)):
                        self.logger_msg(self.client.account_name, None, msg=msg, type_msg='error')
                        return False

                    elif isinstance(error, SoftwareException):
                        msg = f'{error}'

                    elif isinstance(error, BlockchainException):
                        if 'insufficient funds' not in str(error):
                            self.logger_msg(
                                self.client.account_name,
                                None, msg=f'Maybe problem with node: {self.client.rpc}', type_msg='warning'
                            )
                            await self.client.change_rpc()

                    elif isinstance(error, (ClientError, asyncio.TimeoutError, ProxyError, ReplyError)):
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Connection to RPC is not stable. Will try again in 10 seconds...",
                            type_msg='warning'
                        )
                        await asyncio.sleep(10)
                        self.logger_msg(*self.client.acc_info, msg=msg, type_msg='warning')

                        if k % 2 == 0:
                            if int(k / 2) < GeneralSettings.PROXY_REPLACEMENT_COUNT:
                                await self.client.change_proxy()
                                await self.client.change_rpc()
                            else:
                                raise SoftwareException(
                                    f'Account can not find a good proxy {GeneralSettings.PROXY_REPLACEMENT_COUNT} times'
                                )
                        attempts -= 1

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

        finally:
            await self.client.session.close()
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