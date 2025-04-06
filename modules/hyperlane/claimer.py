import base64
import random

from nacl.signing import SigningKey
from web3 import AsyncWeb3

from config import CHAIN_IDS
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

    async def check_drop_eligible(self, from_checker: bool = False):

        params = {
            'address': self.client.address,
        }

        response = await self.make_tls_request(
            url='https://claim.hyperlane.foundation/api/check-eligibility', params=params, headers=self.headers,
            cookies=self.cookies
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
                    return allocation, allocation_chain
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

            response = await self.make_tls_request(
                method="GET", url="https://claim.hyperlane.foundation/", headers=self.headers, return_response_headers=True
            )
            secret_value = response["X-Vercel-Challenge-Token"]

            vercel_solution = await AstrumSolver(self.client).solve_captcha(
                captcha_name='vercel',
                data_for_solver={
                    'challenge_token': secret_value
                }
            )

            headers = self.headers | {
                "x-vercel-challenge-token": secret_value,
                "x-vercel-challenge-solution": vercel_solution,
                "x-vercel-challenge-version": "2",
            }

            try:
                response_cookies, _ = await self.make_tls_request(
                    method="POST", url="https://claim.hyperlane.foundation/.well-known/vercel/security/request-challenge",
                    headers=headers, return_cookies=True
                )
            except Exception as error:
                if 'Bad Request' in str(error):
                    raise SoftwareExceptionWithProxy('Probably your proxy is dead, will chain it')
                else:
                    raise error

            if response_cookies.get('_vcrcs'):
                vcrcs = response_cookies.get("_vcrcs")
            else:
                raise SoftwareExceptionWithProxy('Vercel challenge is not passed')

            self.vercel_cookie = vcrcs
            self.cookies |= {"_vcrcs": self.vercel_cookie}

        allocation, allocation_chain = await self.check_drop_eligible(from_checker)

        if from_checker:
            return allocation, allocation_chain

        chain_type = random.choice(Settings.HYPERLANE_NETWORKS_REGISTER)
        chain_id = CHAIN_IDS[chain_type]

        receiving_address = AsyncWeb3().to_checksum_address(self.client.module_input_data['evm_deposit_address'])
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
                    "amount": f"{round(allocation, 6)}",
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
