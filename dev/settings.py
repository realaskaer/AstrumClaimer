import importlib.util
import os


class Settings:
    PROGRESS_FILE_PATH = None

    @staticmethod
    def load_settings(settings: dict):
        for key, value in settings.items():
            if hasattr(Settings, key):
                setattr(Settings, key, value)

    @staticmethod
    def get_presets_settings(with_custom: bool = False):

        def load_settings_from_file(f_path):
            spec = importlib.util.spec_from_file_location(os.path.basename(f_path), f_path)
            settings_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings_module)
            settings = {
                attr: value for attr, value in vars(settings_module).items() if not attr.startswith("__")
            }
            return settings

        presets_dir = 'presets'

        all_settings = {}

        for filename in os.listdir(presets_dir):
            if filename.endswith('.py'):
                setting_name = filename[:-3]
                file_path = os.path.join(presets_dir, filename)
                all_settings[setting_name] = load_settings_from_file(file_path)

        if with_custom:
            custom_settings = load_settings_from_file('settings.py')
            all_settings['custom'] = custom_settings

        return all_settings

    @staticmethod
    def prepare_settings(route: str = 'custom'):
        all_settings = Settings.get_presets_settings(with_custom=True)

        if route != 'custom':
            Settings.load_settings(all_settings['custom'])
            Settings.PROGRESS_FILE_PATH = f'./data/services/{route}_wallets_progress.json'
        else:
            Settings.PROGRESS_FILE_PATH = f'./data/services/wallets_progress.json'

        settings = all_settings[route]
        Settings.load_settings(settings)

    WANTED_DELEGATOR_ADDRESS = None
    MOVEMENT_CLAIM_AT_AMOUNT = None
    TOTAL_DECIMALS = None
    TRANSFER_ETH_AMOUNT = None
    CLASSIC_ROUTES_BLOCKS_COUNT = None
    CLASSIC_ROUTES_MODULES_USING = None
