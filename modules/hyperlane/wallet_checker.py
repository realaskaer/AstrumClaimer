import os
import copy
import random
import asyncio
import traceback
import pandas as pd

from datetime import datetime
from dev import GeneralSettings
from config import ACCOUNTS_DATA
from .claimer import HyperClaimer
from modules.evm_client import EVMClient
from prettytable import PrettyTable
from utils.networks import EthereumRPC, SolanaRPC
from termcolor import cprint, colored

from ..interfaces import SoftwareException
from ..solana_client import SolanaClient


class HyperChecker:
    @staticmethod
    async def get_account_stats(account_data, index):

        solana_client = False
        if len(account_data['evm_private_key']) < 20:
            raise SoftwareException('Please provide correct private key')
        elif len(account_data['evm_private_key']) in [64, 66]:
            account_data['network'] = EthereumRPC
            client = EVMClient(account_data)
        else:
            account_data['network'] = SolanaRPC
            client = SolanaClient(account_data)
            solana_client = True

        await asyncio.sleep(random.randint(1, 3))

        counter = 0
        while True:
            try:

                allocation, allocation_chain = await HyperClaimer(client).register_on_drop(
                    from_checker=True, solana_client=solana_client
                )

                account_stats = {
                    "#": index + 1,
                    "Account Name": client.account_name,
                    "Address": client.address,
                    "Allocation": allocation,
                    "Reward Chain": allocation_chain.capitalize(),
                }

                return account_stats
            except Exception as error:
                traceback.print_exc()
                client.logger_msg(*client.acc_info, msg=f"Can`t get account stats: {error}", type_msg="error")
                if counter > 5:
                    return {
                        "#": index + 1,
                        "Account Name": client.account_name,
                        "Address": client.address,
                        "Allocation": "ERROR",
                        "Reward Chain": "ERROR",
                    }

    async def check_progress(self):
        cprint("✅  Processing wallets for $HYPER drop")

        fields = [
            "#",
            "Account Name",
            "Address",
            "Allocation",
            "Reward Chain"
        ]

        table = PrettyTable()
        table.field_names = [colored(field, "light_yellow", attrs=["bold"]) for field in fields]

        cfg_acc_names = copy.deepcopy(list(ACCOUNTS_DATA["accounts"].keys()))
        account_names = []

        if GeneralSettings.NEEDED_WALLETS_CHECKER == 0:
            account_names = cfg_acc_names
        elif isinstance(GeneralSettings.NEEDED_WALLETS_CHECKER, int):
            account_names = [cfg_acc_names[GeneralSettings.NEEDED_WALLETS_CHECKER - 1]]
        elif isinstance(GeneralSettings.NEEDED_WALLETS_CHECKER, tuple):
            account_names = [
                cfg_acc_names[i - 1] for i in GeneralSettings.NEEDED_WALLETS_CHECKER if 0 < i <= len(cfg_acc_names)
            ]
        elif isinstance(GeneralSettings.NEEDED_WALLETS_CHECKER, list):
            for item in GeneralSettings.NEEDED_WALLETS_CHECKER:
                if isinstance(item, int):
                    if 0 < item <= len(cfg_acc_names):
                        account_names.append(cfg_acc_names[item - 1])
                elif isinstance(item, list) and len(item) == 2:
                    start, end = item
                    if 0 < start <= end <= len(cfg_acc_names):
                        account_names.extend([cfg_acc_names[i - 1] for i in range(start, end + 1)])
        else:
            account_names = []

        accounts_data = []
        for account_name, account_data in ACCOUNTS_DATA['accounts'].items():
            if account_name in account_names:
                account_data = {
                    'account_name': account_name,
                    'evm_private_key': account_data['evm_private_key'],
                    'network': EthereumRPC,
                    'proxy': account_data['proxy'],
                }
                accounts_data.append(account_data)

        batch_size = 100
        batches = [accounts_data[i: i + batch_size] for i in range(0, len(accounts_data), batch_size)]

        wallets_data = []
        for batch_index, batch in enumerate(batches):
            cprint(f"🔁  Processing batch {batch_index + 1}/{len(batches)}...", "light_yellow", attrs=["blink"])

            tasks = [
                self.get_account_stats(account_data, index + batch_index * batch_size)
                for index, account_data in enumerate(batch)
            ]
            batch_wallets_data = await asyncio.gather(*tasks)

            wallets_data.extend(batch_wallets_data)

        xlsx_data = pd.DataFrame(wallets_data)
        current_date = datetime.now().strftime("%Y-%m-%d")
        directory = "./data/accounts_stats/"
        file_name = f"wallets_stats_soneium_{current_date}.xlsx"  # Добавляем дату
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        xlsx_data.to_excel(file_path, index=False)
        print()
        cprint(
            "✅  Data successfully loaded to /data/accounts_stats/wallets_stats_hyperlane.xlsx (Excel format)\n",
            "light_green",
            attrs=["blink"],
        )

        total_hyper = 0
        for row in wallets_data:
            colored_row_data = []
            for field in fields:
                if field in ["#", "Account Name", "Address"]:
                    colored_row_data.append(colored(row[field], "light_green"))
                elif field in ["Allocation"]:
                    if row[field]:
                        colored_row_data.append(colored(row[field], "light_green"))
                        total_hyper += float(row[field])
                    else:
                        colored_row_data.append(colored(row[field], "light_grey"))
                else:
                    colored_row_data.append(colored(row[field], "light_cyan"))
            table.add_row(colored_row_data, divider=True)

        print(table)
        print()
        if total_hyper:
            cprint(f'TOTAL $HYPER DROP: {total_hyper}', 'light_green', attrs=["blink", 'bold'])
