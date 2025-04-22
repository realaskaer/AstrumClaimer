import copy
import json
import random

from config import ACCOUNTS_DATA
from modules.interfaces import SoftwareException
from utils.tools import clean_progress_file
from functions import *
from modules import Logger
from dev import GeneralSettings, Settings


AVAILABLE_MODULES_INFO = {
    # module_name                       : (module name, priority, tg info, can`t be shuffled, supported network)
    wrap_native                         : (wrap_native, 2, 'Wrap Native', 0, [0]),
    binance_withdraw                    : (binance_withdraw, 2, 'Binance Withdraw', 0, [0]),
    bridge_relay                        : (bridge_relay, 2, 'Bridge Relay', 0, [0]),
    movement_claim_on_l2                : (movement_claim_on_l2, 2, 'Claim $MOVE on L2 Mainnet', 0, [0]),
    movement_claim_on_ethereum          : (movement_claim_on_ethereum, 2, 'Claim $MOVE on Ethereum Mainnet', 0, [0]),
    hyper_register_on_drop              : (hyper_register_on_drop, 2, 'Register on HYPER drop', 0, [0]),
    hyperlane_claim_drop                : (hyperlane_claim_drop, 2, 'Claim $HYPER drop', 0, [0]),
    movement_transfer_move              : (movement_transfer_move, 2, 'Transfer $MOVE on Ethereum Mainnet', 0, [0]),
    unwrap_native                       : (unwrap_native, 2, 'Unwrap Native', 0, [0]),
    transfer_eth                        : (transfer_eth, 3, 'Transfer $ETH', 0, [0]),

    story_claim                         : (story_claim, 2, 'Claim $IP on Story Mainnet', 0, [0]),
    story_transfer                       : (story_transfer, 2, 'Transfer $IP on Story Mainnet to EVM Deposit Address', 0, [0]),
}


def get_func_by_name(module_name, help_message: bool = False):
    for k, v in AVAILABLE_MODULES_INFO.items():
        if k.__name__ == module_name:
            if help_message:
                return v[2]
            return v[0]


class RouteGenerator(Logger):
    def __init__(self):
        Logger.__init__(self)
        self.modules_names_const = [module.__name__ for module in list(AVAILABLE_MODULES_INFO.keys())]

    @staticmethod
    def classic_generate_route():
        route = []
        copy_full_route = copy.deepcopy(Settings.CLASSIC_ROUTES_MODULES_USING)
        rpc = 'Ethereum'
        flag = any(isinstance(sub_route, tuple) for sub_route in copy_full_route)

        if flag:
            blocks = []
            individual_modules_positions = []

            for i, item in enumerate(copy_full_route):
                if isinstance(item, tuple):
                    blocks.append(tuple(item))
                else:
                    individual_modules_positions.append((i, item))

            random.shuffle(blocks)
            blocks_count = random.randint(*copy.deepcopy(Settings.CLASSIC_ROUTES_BLOCKS_COUNT))
            total_blocks = blocks[:blocks_count]

            new_full_route_flat = []
            for block in total_blocks:
                new_full_route_flat.append(block)

            for position, modules in individual_modules_positions:
                new_full_route_flat.insert(position, modules)

        else:
            new_full_route_flat = copy_full_route

        for i in new_full_route_flat:
            if isinstance(i, list):
                module_name = random.choice(i)
                if module_name is None:
                    continue
                if ':' in module_name:
                    module_name, rpc = module_name.split(':')

                module = get_func_by_name(module_name)
                if module:
                    module = get_func_by_name(module_name)
                    route.append(f"{module.__name__}:{rpc}")
                else:
                    raise SoftwareException(f'Нет модуля с именем "{module_name}" в софте.')
            else:
                for sub_module in i:
                    module_name = random.choice(sub_module)
                    if module_name is None:
                        continue
                    if ':' in module_name:
                        module_name, rpc = module_name.split(':')

                    module = get_func_by_name(module_name)
                    if module:
                        route.append(f"{module.__name__}:{rpc}")
                    else:
                        raise SoftwareException(f'Нет модуля с именем "{module_name}" в софте.')
            rpc = "Ethereum"

        return route

    def classic_routes_json_save(self):
        clean_progress_file()
        acc_data = ACCOUNTS_DATA['accounts']
        with open(Settings.PROGRESS_FILE_PATH, 'w') as file:
            accounts_data = {}
            cfg_acc_names = copy.deepcopy(list(acc_data.keys()))

            account_names = []
            if GeneralSettings.WALLETS_TO_WORK == 0:
                account_names = cfg_acc_names
            elif isinstance(GeneralSettings.WALLETS_TO_WORK, int):
                account_names = [cfg_acc_names[GeneralSettings.WALLETS_TO_WORK - 1]]
            elif isinstance(GeneralSettings.WALLETS_TO_WORK, tuple):
                account_names = [cfg_acc_names[i - 1] for i in GeneralSettings.WALLETS_TO_WORK if 0 < i <= len(cfg_acc_names)]
            elif isinstance(GeneralSettings.WALLETS_TO_WORK, list):
                for item in GeneralSettings.WALLETS_TO_WORK:
                    if isinstance(item, int):
                        if 0 < item <= len(cfg_acc_names):
                            account_names.append(cfg_acc_names[item - 1])
                    elif isinstance(item, list) and len(item) == 2:
                        start, end = item
                        if 0 < start <= end <= len(cfg_acc_names):
                            account_names.extend([cfg_acc_names[i - 1] for i in range(start, end + 1)])
            else:
                account_names = []

            if GeneralSettings.WALLETS_TO_EXCLUDE == 0:
                pass
            elif isinstance(GeneralSettings.WALLETS_TO_EXCLUDE, int):
                if GeneralSettings.WALLETS_TO_EXCLUDE <= len(account_names):
                    account_names = [account for account in account_names if
                                     account != cfg_acc_names[GeneralSettings.WALLETS_TO_EXCLUDE - 1]]
            elif isinstance(GeneralSettings.WALLETS_TO_EXCLUDE, tuple):
                indices_to_remove = sorted(GeneralSettings.WALLETS_TO_EXCLUDE, reverse=True)
                for index in indices_to_remove:
                    if 0 < index <= len(cfg_acc_names):
                        account_names = [account for account in account_names if account != cfg_acc_names[index - 1]]
            elif isinstance(GeneralSettings.WALLETS_TO_EXCLUDE, list):
                for item in GeneralSettings.WALLETS_TO_EXCLUDE:
                    if isinstance(item, int):
                        if 0 < item <= len(cfg_acc_names):
                            account_names = [account for account in account_names if account != cfg_acc_names[item - 1]]
                    elif isinstance(item, list) and len(item) == 2:
                        start, end = item
                        if 0 < start <= end <= len(cfg_acc_names):
                            for i in range(start, end + 1):
                                account_names = [account for account in account_names if
                                                 account != cfg_acc_names[i - 1]]
            else:
                account_names = []

            if GeneralSettings.SHUFFLE_WALLETS:
                random.shuffle(account_names)

            for account_name in account_names:
                classic_route = self.classic_generate_route()

                account_data = {
                    "current_step": 0,
                    "route": classic_route
                }
                accounts_data[account_name] = account_data
            json.dump(accounts_data, file, indent=4)
        self.logger_msg(
            None, None,
            msg=f'Successfully generated {len(accounts_data)} classic routes in {Settings.PROGRESS_FILE_PATH}\n',
            type_msg='success'
        )
