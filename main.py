import asyncio
import sys
import os
from config import TITLE
from termcolor import cprint
from questionary import Choice, select
from modules.interfaces import SoftwareException
from utils.modules_runner import Runner
from utils.route_generator import RouteGenerator
from modules.movement.wallet_checker import TxChecker
from utils.tools import progress_file_is_not_empty
from dev import Settings
from version import VERSION


def are_you_sure(module=None, gen_route: bool = False):
    if gen_route or not progress_file_is_not_empty():
        answer = select(
            '\n ⚠️⚠️⚠️ THIS ACTION WILL DELETE ALL PREVIOUS PROGRESS FOR ROUTES, continue? ⚠️⚠️⚠️ \n',
            choices=[
                Choice("❌  NO", 'main'),
                Choice("✅  YES", 'module'),
            ],
            qmark='☢️',
            pointer='👉'
        ).ask()
        print()
        if answer == 'main':
            main()
        else:
            if module:
                module()


def choose_run_option(route: str):
    if progress_file_is_not_empty():
        answer = select(
            f'\n ⚠️⚠️⚠️ Detected progress for {route}, what do you want to do? ⚠️⚠️⚠️ \n',
            choices=[
                Choice(f"✅  Save progress and run {route} without route generation", 'run_accounts'),
                Choice(f"⚠️ Clear progress and run {route} with route generation", 'gen_route'),
            ],
            qmark='☢️',
            pointer='👉'
        ).ask()
        print()
        if answer == 'gen_route':
            generator = RouteGenerator()
            generator.classic_routes_json_save()
        elif answer == 'run_accounts':
            pass
        else:
            raise KeyboardInterrupt
    else:
        generator = RouteGenerator()
        generator.classic_routes_json_save()


def choose_preset_to_run():
    saved_presets_settings = Settings.get_presets_settings()
    saved_routes = sorted(list(saved_presets_settings.keys()))
    choices = [
        Choice(f"↩️ Go back", 'go_back')
    ]
    for saved_route in saved_routes:
        choices.append(
            Choice(f"🟢 {saved_route}", saved_route)
        )
    answer = select(
        'Choose saved route to run for each wallet',
        choices=choices,
        qmark='🛠️',
        pointer='👉'
    ).ask()
    if answer in saved_routes:
        Settings.prepare_settings(route=answer)
        runner = Runner()
        choose_run_option(route=answer)
        asyncio.run(runner.run_accounts())
    elif answer == 'go_back':
        main()
    else:
        raise KeyboardInterrupt


def main():
    try:
        # cprint(TITLE, color='light_cyan')
        # cprint(f'⚙️ v{VERSION}\n', attrs=["bold"])
        cprint(TITLE, color='blue')
        cprint(f'⚙️ v{VERSION}\n', attrs=["bold"])
        cprint(f'\n📝 Main Software documentation: https://docs.astrum.foundation\n', 'light_green', attrs=["bold"])

        while True:
            answer = select(
                'What do you want to do?',
                choices=[
                    # Choice("🚀 Start running routes for each wallet", 'classic_routes_run'),
                    # Choice("📄 Generate route for each wallet", 'classic_routes_gen'),
                    Choice("📂 Open presets", 'get_presets'),
                    # Choice("💰 Check Movement Drop", 'check_movement_drop'),
                    Choice("💰 Check Hyper Drop", 'check_hyper_drop'),
                    Choice("💰 Check Story Drop", 'check_story_drop'),
                    Choice("✅ Check the connection of each proxy", 'check_proxy'),
                    Choice('❌ Exit', "exit")
                ],
                qmark='🛠️',
                pointer='👉'
            ).ask()

            match answer:
                case 'check_proxy':
                    print()
                    runner = Runner()
                    asyncio.run(runner.check_proxies_status())
                    print()
                case 'classic_routes_run':
                    print()
                    Settings.prepare_settings()
                    runner = Runner()
                    asyncio.run(runner.run_accounts())
                    print()
                case 'classic_routes_gen':
                    Settings.prepare_settings()
                    generator = RouteGenerator()
                    are_you_sure(generator.classic_routes_json_save, gen_route=True)
                case 'check_movement_drop':
                    print()
                    tx_checker = TxChecker()
                    asyncio.run(tx_checker.check_wallets())
                    print()
                case 'check_hyper_drop':
                    from modules.hyperlane.wallet_checker import HyperChecker
                    asyncio.run(HyperChecker().check_progress())
                case 'check_story_drop':
                    from modules.story.wallet_checker import StoryChecker
                    asyncio.run(StoryChecker().check_progress())
                    print()
                case 'get_presets':
                    print()
                    choose_preset_to_run()
                case 'exit':
                    sys.exit()
                case _:
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        cprint(f'\nQuick software shutdown by <ctrl + C>', color='light_yellow')
        os.system("pause")

    except SoftwareException as error:
        cprint(f'\n{error}', color='light_red')
        os.system("pause")


if __name__ == "__main__":
    main()
