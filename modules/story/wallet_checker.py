import copy
import os
import random
import asyncio
import traceback

import pandas as pd

from datetime import datetime
from config import ACCOUNTS_DATA
from dev import GeneralSettings
from modules.evm_client import EVMClient
from prettytable import PrettyTable
from termcolor import cprint, colored
from utils.networks import EthereumRPC
from modules.story.story_claimer import StoryClaimer


class StoryChecker:
    @staticmethod
    async def get_account_stats(account_data, index):
        evm_client = EVMClient(account_data)

        await asyncio.sleep(random.randint(1, 3))

        counter = 0
        while True:
            try:
                eligible_status, passport_score, claimed = await StoryClaimer(evm_client).claim_ip(from_checker=True)

                return {
                    "#": index + 1,
                    "Account Name": evm_client.account_name,
                    "Address": evm_client.address,
                    "Eligible": eligible_status,
                    "Gitcoin Score": passport_score,
                    "Claimed": claimed,
                }
            except Exception as error:
                traceback.print_exc()
                evm_client.logger_msg(
                    *evm_client.acc_info, msg=f'Can`t get account stats: {error}', type_msg='error'
                )
                if counter > 5:
                    return {
                        "#": index + 1,
                        "Account Name": evm_client.account_name,
                        "Address": evm_client.address,
                        "Eligible": "ERROR",
                        "Gitcoin Score": "ERROR",
                        "Claimed": "ERROR",
                    }

    async def check_progress(self):
        cprint('✅  Processing wallets for Story Drop')

        fields = ['#', 'Account Name', 'Address', 'Eligible', 'Gitcoin Score', 'Claimed']

        table = PrettyTable()
        table.field_names = [colored(field, 'light_yellow', attrs=['bold']) for field in fields]

        accounts_data = []

        cfg_acc_names = copy.deepcopy(list(ACCOUNTS_DATA['accounts'].keys()))
        account_names = []

        if GeneralSettings.NEEDED_WALLETS_CHECKER == 0:
            account_names = cfg_acc_names
        elif isinstance(GeneralSettings.NEEDED_WALLETS_CHECKER, int):
            account_names = [cfg_acc_names[GeneralSettings.NEEDED_WALLETS_CHECKER - 1]]
        elif isinstance(GeneralSettings.NEEDED_WALLETS_CHECKER, tuple):
            account_names = [cfg_acc_names[i - 1] for i in GeneralSettings.NEEDED_WALLETS_CHECKER if
                             0 < i <= len(cfg_acc_names)]
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

        for account_name in account_names:
            account_data = {
                "account_name": account_name,
                "evm_private_key": ACCOUNTS_DATA['accounts'][account_name]['evm_private_key'],
                "network": EthereumRPC,
                "proxy": ACCOUNTS_DATA['accounts'][account_name]['proxy'],
                "email_login": None,
                "email_password": None,
                "twitter_token": None,
                "discord_token": None,
            }
            accounts_data.append(account_data)

        batch_size = 50
        batches = [accounts_data[i:i + batch_size] for i in range(0, len(accounts_data), batch_size)]

        wallets_data = []
        for batch_index, batch in enumerate(batches):
            cprint(f"🔁  Processing batch {batch_index + 1}/{len(batches)}...", 'light_yellow', attrs=["blink"])

            tasks = [self.get_account_stats(account_data, index + batch_index * batch_size)
                     for index, account_data in enumerate(batch)]
            batch_wallets_data = await asyncio.gather(*tasks)

            wallets_data.extend(batch_wallets_data)

        xlsx_data = pd.DataFrame(wallets_data)
        current_date = datetime.now().strftime("%Y-%m-%d")
        directory = './data/accounts_stats/'
        file_name = f'wallets_stats_eclipse_tap_{current_date}.xlsx'  # Добавляем дату
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        xlsx_data.to_excel(file_path, index=False)
        print()
        cprint('✅  Data successfully loaded to /data/accounts_stats/wallets_stats_story.xlsx (Excel format)\n',
               'light_green', attrs=["blink"])

        for row in wallets_data:
            colored_row_data = []
            for field in fields:
                if field in ['#', 'Account Name', 'Address']:
                    colored_row_data.append(colored(row[field], 'light_green'))
                elif field in ['Eligible', 'Claimed']:
                    if row[field]:
                        colored_row_data.append(colored(row[field], 'light_green', attrs=['bold']))
                    else:
                        colored_row_data.append(colored(row[field], 'light_red', attrs=['bold']))
                elif field in ['Gitcoin Score']:
                    if float(row[field]) >= 20:
                        colored_row_data.append(colored(row[field], 'light_green', attrs=['bold']))
                    elif float(row[field]) != 0:
                        colored_row_data.append(colored(row[field], 'light_red', attrs=['bold']))
                    elif float(row[field]) == 0:
                        colored_row_data.append(colored(row[field], 'light_grey', attrs=['bold']))
                else:
                    colored_row_data.append(colored(row[field], 'light_cyan'))
            table.add_row(colored_row_data, divider=True)

        print(table)
