import os
import importlib.util


class GeneralSettings:
    @staticmethod
    def load_general_settings(settings: dict):
        for key, value in settings.items():
            if hasattr(GeneralSettings, key):
                setattr(GeneralSettings, key, value)

    @staticmethod
    def get_general_settings():
        file_name = 'general_settings.py'
        spec = importlib.util.spec_from_file_location(os.path.basename(file_name), file_name)
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)

        general_settings = {
            attr: value for attr, value in vars(settings_module).items() if not attr.startswith("__")
        }

        return general_settings

    @staticmethod
    def prepare_general_settings():
        general_settings = GeneralSettings.get_general_settings()
        GeneralSettings.load_general_settings(general_settings)

    BINANCE_API_KEY = None
    BINANCE_API_SECRET = None
    SOFTWARE_MODE = None
    ACCOUNTS_IN_STREAM = None
    WALLETS_TO_WORK = None
    WALLETS_TO_EXCLUDE = None
    SHUFFLE_WALLETS = None
    BREAK_ROUTE = None
    SAVE_PROGRESS = None
    TELEGRAM_NOTIFICATIONS = None
    BREAK_FAUCET = None
    CHECK_NATIVE_ON_FAUCET = None
    MIN_BERA_AMOUNT = None
    INFINITY_MODE = None
    SLEEP_MODE = None
    SLEEP_TIME_MODULES = None
    SLEEP_TIME_ACCOUNTS = None
    SLEEP_TIME_FOR_NEW_RUN = None
    MAXIMUM_RETRY = None
    SLEEP_TIME_RETRY = None
    GAS_CONTROL = None
    MAXIMUM_GWEI = None
    SLEEP_TIME_GAS = None
    CONTROL_TIMES_FOR_SLEEP = None
    GAS_LIMIT_MULTIPLIER = None
    GAS_PRICE_MULTIPLIER = None
    UNLIMITED_APPROVE = None
    PROXY_REPLACEMENT_COUNT = None
    MAIN_PROXY = None
    USE_PROXY = None
    MOBILE_PROXY = None
    MOBILE_PROXY_URL_CHANGER = None
    CAPTCHA_SOLVER = None
    TWO_CAPTCHA_API_KEY = None
    CAP_MONSTER_API_KEY = None
    EXCEL_PASSWORD = None
    EXCEL_PAGE_NAME = None
    EXCEL_FILE_PATH = None
    TG_TOKEN = None
    TG_ID = None
