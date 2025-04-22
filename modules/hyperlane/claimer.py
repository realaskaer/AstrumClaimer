import base64
import random

from nacl.signing import SigningKey
from web3 import AsyncWeb3

from config import CHAIN_IDS, TOTAL_USER_AGENT, HYPERLANE_ABI, CHAIN_NAME_FROM_ID, TOKENS_PER_CHAIN
from modules import Custom
from modules.astrum_solver import AstrumSolver
from modules.solana_client import SolanaClient
from utils.tools import helper
from modules.interfaces import Logger, RequestClient, SoftwareExceptionWithoutRetry, SoftwareExceptionWithProxy, \
    SoftwareException
from modules.evm_client import EVMClient
from dev import Settings


class HyperClaimer(Logger, RequestClient):
    def __init__(self, client: EVMClient | SolanaClient):
        Logger.__init__(self)
        RequestClient.__init__(self, client)
        self.client = client
        self.nonce = None
        self.vercel_cookie = ""
        self.headers = {
            'accept': '*/*',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://claim.hyperlane.foundation/',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

        self.cookies = {}

    async def get_account(self, receiving_address):
        self.logger_msg(*self.client.acc_info, msg=f"Fetching registrations for {receiving_address}...")

        url = f'https://claim.hyperlane.foundation/api/get-registration-for-address?address={receiving_address}'

        try:
            response = await self.make_tls_request(
                method='GET', url=url, headers=self.headers, cookies=self.cookies, rate_limit_sleep=0
            )
        except Exception as error:
            if 'Address not found' in str(error):
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Registrant wallet ({receiving_address[:10]}..) haven`t any registration yet, initiating...",
                    type_msg='warning'
                )
                return False
            else:
                raise error

        if response.get('message') == 'Success' and response['response']:
            registered_wallets = response['response']
            self.logger_msg(
                *self.client.acc_info,
                msg=f"Successfully fetch registered {len(registered_wallets)} wallets on {receiving_address}",
                type_msg='success'
            )

            if any([wallet['eligibleAddress'] == f"{self.client.address}" for wallet in registered_wallets]):
                self.logger_msg(
                    *self.client.acc_info, msg=f"Wallet already registered to receiving tokens on {receiving_address}",
                    type_msg='success'
                )
                return True

    async def check_drop_eligible(self, from_checker: bool = False):

        params = {
            'address': self.client.address,
        }

        response = await self.make_tls_request(
            url='https://claim.hyperlane.foundation/api/check-eligibility', params=params, headers=self.headers,
            cookies=self.cookies, rate_limit_sleep=0
        )

        try:
            if response.get("message") == 'Address found':
                self.logger_msg(*self.client.acc_info, msg=f"Address found in Hyperlane database", type_msg='success')
                eligible = response['response']['isEligible']
                if eligible:
                    allocation = [eligibility['amount'] for eligibility in response['response']['eligibilities']][0]
                    allocation_chain = [eligibility['network'] for eligibility in response['response']['eligibilities']][0]
                    self.logger_msg(
                        *self.client.acc_info, msg=f"Account eligible for HYPER drop, total allocation: {allocation}",
                        type_msg='success'
                    )

                    client, _, balance, balance_in_wei, _ = await Custom(self.client).balance_searcher(
                        chains=['Arbitrum', 'Optimism', 'BNB Chain', 'Ethereum', 'Base'],
                        tokens=['HYPER', 'HYPER', 'HYPER', 'HYPER', 'HYPER'], raise_handle=True
                    )

                    return allocation, allocation_chain, balance
                else:
                    raise SoftwareExceptionWithoutRetry('Account don`t eligible for HYPER drop')
            else:
                raise SoftwareExceptionWithoutRetry(f'Response don`t handled: {response}')
        except Exception as error:
            if from_checker:
                self.logger_msg(
                    *self.client.acc_info, msg=f"Bad response from Hyperlane API: {error}", type_msg='warning'
                )
                return 0, 'empty'
            else:
                raise error

    @helper
    async def register_on_drop(self, from_checker: bool = False, solana_client: bool = False):
        self.logger_msg(*self.client.acc_info, msg=f"Fetching allocation for HYPER registration...")

        if not from_checker and not Settings.HYPERLANE_TOKEN_REGISTER:
            raise SoftwareExceptionWithoutRetry('Please provide a token type in HYPERLANE_TOKEN_REGISTER')

        token_type = Settings.HYPERLANE_TOKEN_REGISTER

        if not from_checker and not Settings.HYPERLANE_NETWORKS_REGISTER:
            raise SoftwareExceptionWithoutRetry('Please provide a chain type in HYPERLANE_NETWORKS_REGISTER')

        if not from_checker and not AsyncWeb3().is_address(self.client.module_input_data['evm_deposit_address']):
            raise SoftwareExceptionWithoutRetry('Please provide Transfer address into account_data.xlsx')

        if not self.vercel_cookie:
            self.logger_msg(*self.client.acc_info, msg=f"Vercel challenge is not passed yet, processing...")

            vcrcs = await AstrumSolver(self.client).solve_captcha(
                captcha_name='vercel',
                data_for_solver={
                    'websiteURL': 'https://claim.hyperlane.foundation/'
                }
            )

            self.vercel_cookie = vcrcs
            self.cookies |= {"_vcrcs": self.vercel_cookie}

        receiving_address = AsyncWeb3().to_checksum_address(self.client.module_input_data['evm_deposit_address'])

        try:
            if not from_checker and await self.get_account(receiving_address):
                return True

            allocation, allocation_chain, hyper_balance = await self.check_drop_eligible(from_checker)

            if from_checker:
                return allocation, allocation_chain, hyper_balance
        except Exception as error:
            if '<!DOCTYPE html>' in str(error):
                raise SoftwareExceptionWithProxy('Probably bad Vercel solution')
            else:
                raise error

        chain_type = random.choice(Settings.HYPERLANE_NETWORKS_REGISTER)
        chain_id = CHAIN_IDS[chain_type]

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Receiving address for $HYPER drop found: {receiving_address}. Claim network name: {chain_type}",
            type_msg='success'
        )

        if solana_client:
            msg_to_sign = f'{self.client.address} selects {receiving_address} ({chain_id}) to receive {allocation} {token_type}'

            signing_key = SigningKey(self.client.wallet.secret())
            signed = signing_key.sign(msg_to_sign.encode())
            signature = base64.b64encode(signed.signature).decode('utf-8')

        else:
            typed_data = {
                "domain": {
                    "name": "Hyperlane",
                    "version": "1"
                },
                "message": {
                    "eligibleAddress": self.client.address,
                    "chainId": chain_id,
                    "amount": f"{allocation}",
                    "receivingAddress": receiving_address,
                    "tokenType": token_type
                },
                "primaryType": "Message",
                "types": {
                    "EIP712Domain": [
                        {
                            "name": "name",
                            "type": "string"
                        },
                        {
                            "name": "version",
                            "type": "string"
                        }
                    ],
                    "Message": [
                        {
                            "name": "eligibleAddress",
                            "type": "string"
                        },
                        {
                            "name": "chainId",
                            "type": "uint256"
                        },
                        {
                            "name": "amount",
                            "type": "string"
                        },
                        {
                            "name": "receivingAddress",
                            "type": "string"
                        },
                        {
                            "name": "tokenType",
                            "type": "string"
                        }
                    ]
                }
            }

            signature = self.client.w3.eth.account.sign_typed_data(
                private_key=self.client.private_key, full_message=typed_data
            ).signature

            signature = self.client.w3.to_hex(signature)

        self.headers['referer'] = 'https://claim.hyperlane.foundation/airdrop-registration'

        json_data = {
            'wallets': [
                {
                    'eligibleAddress': f"{self.client.address}",
                    'chainId': chain_id,
                    'eligibleAddressType': allocation_chain.lower(),
                    'receivingAddress': receiving_address,
                    'signature': f"{signature}",
                    'tokenType': token_type,
                    'amount': f'{allocation}',
                },
            ],
        }

        response = await self.make_tls_request(
            method='POST', url='https://claim.hyperlane.foundation/api/save-registration', headers=self.headers,
            json=json_data, cookies=self.cookies
        )

        if response.get('validationResult') and response['validationResult'].get('success'):
            self.logger_msg(
                *self.client.acc_info, msg=f"Registration {token_type} in {chain_type} was successful",
                type_msg='success'
            )

            return True

        raise SoftwareException(f'Bad response from HYPER API, response: {response}')

    @staticmethod
    def generate_random_user_agent():
        platforms = {
            "Windows": [
                ("Windows NT 10.0; Win64; x64", "Windows"),
                ("Windows NT 11.0; Win64; x64", "Windows"),
                ("Windows NT 10.0; WOW64", "Windows"),
            ],
            "Mac": [
                ("Macintosh; Intel Mac OS X 10_15_7", "macOS"),
                ("Macintosh; Intel Mac OS X 11_2_3", "macOS"),
                ("Macintosh; Intel Mac OS X 12_3_1", "macOS"),
                ("Macintosh; Intel Mac OS X 13_0", "macOS"),
            ],
            "Linux": [
                ("X11; Linux x86_64", "Linux"),
                ("X11; Ubuntu; Linux x86_64", "Linux"),
                ("X11; Fedora; Linux x86_64", "Linux"),
            ],
            "iOS": [
                ("iPhone; CPU iPhone OS 16_0 like Mac OS X", "iOS"),
                ("iPad; CPU OS 16_0 like Mac OS X", "iOS"),
                ("iPhone; CPU iPhone OS 15_6_1 like Mac OS X", "iOS"),
            ],
            "Android": [
                ("Linux; Android 13", "Android"),
                ("Linux; Android 12; SM-S908B", "Android"),
                ("Linux; Android 11; Pixel 6", "Android"),
            ]
        }

        browsers = {
            "Chrome": {
                "versions": ["106.0.0.0", "107.0.0.0", "108.0.0.0", "109.0.0.0", "110.0.0.0",
                             "111.0.0.0", "112.0.0.0", "113.0.0.0", "114.0.0.0", "115.0.0.0",
                             "116.0.0.0", "117.0.0.0", "118.0.0.0", "119.0.0.0", "120.0.0.0",
                             "121.0.0.0", "122.0.0.0", "123.0.0.0", "124.0.0.0", "125.0.0.0",
                             "126.0.0.0", "127.0.0.0", "128.0.0.0", "129.0.0.0", "130.0.0.0",
                             "131.0.0.0", "132.0.0.0", "133.0.0.0", "134.0.0.0", "135.0.0.0",
                             "136.0.0.0", "137.0.0.0"],
                "ua_template": "Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                "sec_ch_ua": '"Google Chrome";v="{version_major}", "Not(A:Brand";v="99", "Chromium";v="{version_major}"'
            },
            "Edge": {
                "versions": ["106.0.1370.47", "107.0.1418.35", "108.0.1462.54", "109.0.1518.70",
                             "110.0.1587.57", "111.0.1661.51", "112.0.1722.48", "113.0.1774.50",
                             "114.0.1823.51", "115.0.1901.183", "116.0.1938.54", "117.0.2045.41",
                             "118.0.2088.46", "119.0.2151.44", "120.0.2210.77", "121.0.2277.83",
                             "122.0.2365.59", "123.0.2420.65", "124.0.2478.55", "125.0.2535.49",
                             "126.0.2592.57", "127.0.2653.100", "128.0.2723.44", "129.0.2793.44",
                             "130.0.2857.82", "131.0.2929.79", "132.0.3007.99", "133.0.3135.63"],
                "ua_template": "Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{version}",
                "sec_ch_ua": '"Microsoft Edge";v="{version_major}", "Not(A:Brand";v="99", "Chromium";v="{chrome_major}"'
            },
            "Firefox": {
                "versions": ["106.0", "107.0", "108.0", "109.0", "110.0", "111.0", "112.0",
                             "113.0", "114.0", "115.0", "116.0", "117.0", "118.0", "119.0",
                             "120.0", "121.0", "122.0", "123.0", "124.0", "125.0", "126.0",
                             "127.0", "128.0", "129.0", "130.0", "131.0", "132.0", "133.0"],
                "ua_template": "Mozilla/5.0 ({platform}; rv:{version}) Gecko/20100101 Firefox/{version}",
                "sec_ch_ua": '"Firefox";v="{version_major}", "Not(A:Brand";v="99"'
            },
            "Safari": {
                "versions": ["15.0", "15.1", "15.2", "15.3", "15.4", "15.5", "15.6",
                             "16.0", "16.1", "16.2", "16.3", "16.4", "16.5", "16.6",
                             "17.0", "17.1", "17.2", "17.3", "17.4", "17.5"],
                "ua_template": "Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15",
                "sec_ch_ua": '"Safari";v="{version_major}", "Not(A:Brand";v="99", "Apple WebKit";v="605"'
            }
        }

        platform_name = random.choice(list(platforms.keys()))
        platform_data, platform_sec_ch = random.choice(platforms[platform_name])

        browser_name = "Chrome" if platform_name in ["Android"] else random.choice(list(browsers.keys()))
        if browser_name == "Safari" and platform_name not in ["Mac", "iOS"]:
            browser_name = "Chrome"  # Safari только на Apple устройствах

        browser_data = browsers[browser_name]
        version = random.choice(browser_data["versions"])
        version_major = version.split('.')[0]

        ua_template = browser_data["ua_template"]

        if browser_name == "Edge":
            chrome_ver = random.choice(browsers["Chrome"]["versions"])
            chrome_major = chrome_ver.split('.')[0]
            ua = ua_template.format(platform=platform_data, chrome_ver=chrome_ver, version=version)
            sec_ch_ua = browser_data["sec_ch_ua"].format(version_major=version_major, chrome_major=chrome_major)
        else:
            ua = ua_template.format(platform=platform_data, version=version)
            sec_ch_ua = browser_data["sec_ch_ua"].format(version_major=version_major)

        is_mobile = platform_name in ["iOS", "Android"]
        sec_ch_ua_mobile = "?1" if is_mobile else "?0"

        return {
            "user_agent": ua,
            "sec_ch_ua": sec_ch_ua,
            "sec_ch_ua_platform": f'"{platform_sec_ch}"',
            "sec_ch_ua_mobile": sec_ch_ua_mobile,
            # "is_mobile": is_mobile
        }

    @helper
    async def claim_hyper(self):
        self.cookies = {}
        self.vercel_cookie = {}

        self.logger_msg(*self.client.acc_info, msg=f"Fetching allocation for claim $HYPER...")

        if not self.vercel_cookie:
            self.logger_msg(*self.client.acc_info, msg=f"Vercel challenge is not passed yet, processing...")

            vcrcs = await AstrumSolver(self.client).solve_captcha(
                captcha_name='vercel',
                data_for_solver={
                    'websiteURL': 'https://claim.hyperlane.foundation/'
                }
            )

            self.vercel_cookie = vcrcs
            self.cookies |= {"_vcrcs": self.vercel_cookie}

        fingerprints = self.generate_random_user_agent()

        headers = {
            'authority': 'claim.hyperlane.foundation',
            'accept': '*/*',
            'accept-language': 'pl',
            'referer': 'https://claim.hyperlane.foundation/',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="135", "Google Chrome";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': TOTAL_USER_AGENT
        } | fingerprints

        params = {
            'address': self.client.address,
        }

        try:
            response = await self.make_tls_request(
                method='GET', url='https://claim.hyperlane.foundation/api/claims', params=params, cookies=self.cookies,
                headers=headers, rate_limit_sleep=0
            )
        except Exception as error:
            if '<!DOCTYPE html><html' in str(error):
                raise SoftwareExceptionWithProxy('Probably bad Vercel solutions')
            else:
                raise error

        if response.get('message') == 'Claims found':
            merkle_proof = response['response']['claims'][0]['merkle']['proof']
            merkle_index = response['response']['claims'][0]['merkle']['index']
            amount_to_claim = self.client.w3.to_int(hexstr=response['response']['claims'][0]['merkle']['amount'])
            amount = round(amount_to_claim / 10 ** 18, 2)
            network_to_claim = response['response']['claims'][0]['chainId']

            chain_name = CHAIN_NAME_FROM_ID[network_to_claim]
            contract_address = {
                "ETHEREUM": "0xE5d5e5891a11b3948d84307af7651D684b87e730",
                "BASE": "0x3D115377ec8E55A5c18ad620102286ECD068a36c",
                "ARBITRUM": "0x3D115377ec8E55A5c18ad620102286ECD068a36c",
                "OPTIMISM": "0x93A2Db22B7c736B341C32Ff666307F4a9ED910F5",
                "BNB CHAIN": "0xa7D7422cf603E40854D26aF151043e73c1201563"
            }[chain_name.upper()]

            claim_client = self.client.new_client(chain_name)

            self.logger_msg(
                *self.client.acc_info,
                msg=f"Successfully found address for claiming {amount} HYPER in {chain_name} chain",
                type_msg='success'
            )

            claim_contract = claim_client.get_contract(contract_address=contract_address, abi=HYPERLANE_ABI)

            try:
                transaction = await claim_contract.functions.claim(
                    merkle_index,
                    claim_client.address,
                    amount_to_claim,
                    merkle_proof
                ).build_transaction(await claim_client.prepare_transaction())
            except Exception as error:
                if '0x646cf558' in str(error):
                    self.logger_msg(*self.client.acc_info, msg=f'You already claim $HYPER', type_msg='success')
                    return True
                elif 'gas required exceeds' in str(error) or 'insufficient funds' in str(error):
                    from modules.custom_modules import Custom

                    cex_chain_id = {
                        'Arbitrum': 2,
                        'Optimism': 3,
                        'Base': 6,
                        'BNB Chain': 8,
                    }[chain_name]

                    Settings.OKX_WITHDRAW_DATA = [
                        [cex_chain_id, (0.0002, 0.0003)],
                    ]

                    await Custom(self.client).smart_cex_withdraw(dapp_id=Settings.HYPERLANE_CEX_USE)
                    raise SoftwareException('Exception for retry...')
                else:
                    raise error

            return await claim_client.send_transaction(transaction)
        else:
            raise SoftwareExceptionWithoutRetry("You not eligible or address not found in Hyperlane")

    @helper
    async def swap_hyper(self):
        from modules.custom_modules import Custom
        from modules.hyperlane.odos import ODOS
        self.logger_msg(*self.client.acc_info, msg=f"Fetching balance for HYPER in all possible chains")

        client, _, balance, balance_in_wei, _ = await Custom(self.client).balance_searcher(
            chains=['Arbitrum', 'Optimism', 'BNB Chain', 'Ethereum', 'Base'],
            tokens=['HYPER', 'HYPER', 'HYPER', 'HYPER', 'HYPER'], raise_handle=True
        )

        if balance == 0:
            return False

        if client.network.name in ['Base', 'Optimism']:
            raise SoftwareExceptionWithoutRetry(
                f'Slippage in {client.network.name} chain is too high, please bridge into BNB Chain first'
            )

        hyper_address = {
            'Arbitrum': '0xC9d23ED2ADB0f551369946BD377f8644cE1ca5c4',
            'BNB Chain': '0xC9d23ED2ADB0f551369946BD377f8644cE1ca5c4',
            'Base': '0xC9d23ED2ADB0f551369946BD377f8644cE1ca5c4',
            'Ethereum': '0x93A2Db22B7c736B341C32Ff666307F4a9ED910F5',
            'Optimism': '0x9923DB8d7FBAcC2E69E87fAd19b886C81cd74979',
        }[client.network.name]

        return await ODOS(client).swap(swap_data=[hyper_address, '0x0000000000000000000000000000000000000000', balance, balance_in_wei])

    @helper
    async def bridge_hyper_to_bsc(self):
        from modules.custom_modules import Custom
        from modules.hyperlane.usenexus import UseNexus

        self.logger_msg(*self.client.acc_info, msg=f"Fetching balance for HYPER in all possible chains")

        client, _, balance, balance_in_wei, _ = await Custom(self.client).balance_searcher(
            chains=['Arbitrum', 'Optimism', 'BNB Chain', 'Ethereum', 'Base'],
            tokens=['HYPER', 'HYPER', 'HYPER', 'HYPER', 'HYPER'], raise_handle=True
        )

        if client.network.name == 'BNB Chain':
            self.logger_msg(*self.client.acc_info, msg=f"HYPER already in BNB Chain", type_msg='success')
            return True

        if balance == 0:
            return True

        return await UseNexus(client).bridge(bridge_data=[client.network.name, balance, balance_in_wei])

    @helper
    async def transfer_hyper(self):
        from modules.custom_modules import Custom

        from config import ACCOUNTS_DATA

        transfer_address = ACCOUNTS_DATA['accounts'][self.client.account_name].get('evm_deposit_address')

        if not transfer_address:
            raise SoftwareExceptionWithoutRetry(
                f'There is no wallet listed for transfer, please add wallet into accounts_data.xlsx'
            )

        client, _, amount, amount_in_wei, _ = await Custom(self.client).balance_searcher(
            chains=['Arbitrum', 'Optimism', 'BNB Chain', 'Ethereum', 'Base'],
            tokens=['HYPER', 'HYPER', 'HYPER', 'HYPER', 'HYPER'], raise_handle=True
        )

        # if client.network.name == 'BNB Chain':
        #     self.logger_msg(*self.client.acc_info, msg=f"HYPER already in BNB Chain", type_msg='success')
        #     return True

        if amount == 0:
            return True

        token_contract = client.get_contract(contract_address=TOKENS_PER_CHAIN[client.network.name]['HYPER'])

        try:
            transaction = await token_contract.functions.transfer(
                transfer_address,
                amount_in_wei
            ).build_transaction(await client.prepare_transaction())
        except Exception as error:
            if 'gas required exceeds' in str(error) or 'insufficient funds' in str(error):
                from modules.custom_modules import Custom

                cex_chain_id = {
                    'Arbitrum': 2,
                    'Optimism': 3,
                    'Base': 6,
                    'BNB Chain': 8,
                }[client.network.name]

                Settings.OKX_WITHDRAW_DATA = [
                    [cex_chain_id, (0.0001, 0.0002)],
                ]

                await Custom(client).smart_cex_withdraw(dapp_id=Settings.HYPERLANE_CEX_USE)
                raise SoftwareException('Exception for retry...')
            else:
                raise error

        self.logger_msg(*client.acc_info, msg=f"Transfer {amount} HYPER to {transfer_address} address")

        return await client.send_transaction(transaction)
