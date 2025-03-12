import time

from modules.client import Client
from utils.tools import helper, gas_checker
from config import MOVEMENT_ABI, TOTAL_USER_AGENT
from modules.interfaces import Logger, RequestClient, SoftwareException, SoftwareExceptionWithoutRetry


class StoryClaimer(Logger, RequestClient):
    def __init__(self, client: Client):
        Logger.__init__(self)
        RequestClient.__init__(self, client)
        self.client = client
        self.nonce = None

        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://rewards.story.foundation',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://rewards.story.foundation/',
            'sec-ch-ua': '"Google Chrome";v="133", "Chromium";v="133", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': TOTAL_USER_AGENT
        }

        self.fee_contract = self.client.get_contract(
            contract_address='0x429d6E96bbD6b4134c92954c71200BD0BEA751fb',
            abi=MOVEMENT_ABI['fee_collector']
        )

        self.claim_contract = self.client.get_contract(
            contract_address='0x4B3883cCE3313Ed4445a897355032c273fd87A6f',
            abi=MOVEMENT_ABI['claimer']
        )

    async def sign_msg(self):
        url = 'https://claim.storyapis.com/sign'

        timestamp = int(time.time() * 1000)

        msg = f"""By signing this message, I confirm ownership of this wallet and that I have read and agree to the Token Claim Terms.

nonce: {timestamp}"""

        signature = await self.client.sign_message(msg)

        json_data = {
            'wallet': self.client.address,
            'nonce': f"{timestamp}",
            'signature': signature,
        }

        response = await self.make_request("POST", url=url, headers=self.headers, json=json_data)

        if response['code'] == 200:
            self.logger_msg(*self.client.acc_info, msg=f"You are eligible for claiming", type_msg='success')
            self.headers['authorization'] = response['msg']
            return True
        elif response['code'] == 1003:
            self.logger_msg(*self.client.acc_info, msg=f"You are not eligible for claiming", type_msg='error')
            return False
        else:
            raise SoftwareExceptionWithoutRetry(f'This response is not handled: {response}')

    async def process_claim(self):
        url = 'https://claim.storyapis.com/claim/process'

        response = await self.make_request(method="GET", url=url, headers=self.headers)
        if response['code'] == 200:
            if response['msg']['status'] == 'not_eligible_gitcoin':
                passport_score = float(response['msg']['gitCoin']['score'])
                self.logger_msg(
                    *self.client.acc_info, msg=f"Your GitCoin passort score: {passport_score}, upgrade it first!",
                    type_msg='warning'
                )
                return passport_score, False
                # else:
                #     self.logger_msg(
                #         *self.client.acc_info, msg=f"Your GitCoin passort score: {passport_score}, you can claim $IP",
                #         type_msg='success'
                #     )
                #     return passport_score
            elif response['msg']['status'] == 'claimed':
                passport_score = 20
                self.logger_msg(*self.client.acc_info, msg=f"You already claimed $IP", type_msg='success')
                return passport_score, True
            elif response['msg']['status'] == 'can_claim':
                passport_score = 21
                self.logger_msg(*self.client.acc_info, msg=f"You can claim $IP", type_msg='success')
                return passport_score, True
            else:
                raise SoftwareExceptionWithoutRetry(
                    f"Response status: '{response['msg']['status']}' is not supported, response: {response}"
                )
        else:
            raise SoftwareExceptionWithoutRetry(
                f"Response code {response['code']} is not handled, response: {response}"
            )

        #     "code": 200,
        #     "msg": {
        #         "status": "not_eligible_gitcoin",
        #         "detail": "need pass gitcoin score first",
        #         "gitCoin": {
        #             "address": "0xe4beb23ffebbefff8faf5e5db6e1c81781727d6a",
        #             "score": 0.00000,
        #             "passing_score": false,
        #             "threshold": "20.00000",
        #             "error": null
        #         },
        #         "txHash": ""
        #     },
        #     "error": ""
        # }

    async def claim_ip_util(self):
        response = await self.make_request(
            method='GET', url='https://claim.storyapis.com/address_data', headers=self.headers
        )

        if response.get('code') == 200:
            merkle_tree = response['msg']['merkle_tree']

            self.logger_msg(
                *self.client.acc_info, msg=f"IP amount: {int(merkle_tree['amount']) / 10 ** 18:.2f}, initialize claiming..."
            )

            deadline = int(time.time() + 86400)
            typed_data = {
                "domain": {
                    "name": "MerkleClaimer",
                    "version": "1",
                    "chainId": 1514,
                    "verifyingContract": self.client.w3.to_checksum_address(merkle_tree['contractAddress'])
                },
                "message": {
                    "index": int(merkle_tree['index']),
                    "amount": merkle_tree['amount'],
                    "to": self.client.address.lower(),
                    "proof": merkle_tree['proof'],
                    "deadline": deadline,
                },
                "primaryType": "ClaimOnBehalfData",
                "types": {
                    "EIP712Domain": [
                        {
                            "name": "name",
                            "type": "string"
                        },
                        {
                            "name": "version",
                            "type": "string"
                        },
                        {
                            "name": "chainId",
                            "type": "uint256"
                        },
                        {
                            "name": "verifyingContract",
                            "type": "address"
                        }
                    ],
                    "ClaimOnBehalfData": [
                        {
                            "name": "index",
                            "type": "uint256"
                        },
                        {
                            "name": "amount",
                            "type": "uint256"
                        },
                        {
                            "name": "to",
                            "type": "address"
                        },
                        {
                            "name": "proof",
                            "type": "bytes32[]"
                        },
                        {
                            "name": "deadline",
                            "type": "uint256"
                        }
                    ]
                }
            }

            signature = self.client.w3.eth.account.sign_typed_data(
                full_message=typed_data, private_key=self.client.private_key
            ).signature.hex()

            json_data = {
                'address': self.client.address,
                'deadline': deadline,
                'signature': signature,
            }

            response = await self.make_request(
                method="POST", url='https://claim.storyapis.com/claim', headers=self.headers, json=json_data
            )

            if response.get('code') == 200 and response.get('msg') == 'queued':
                self.logger_msg(*self.client.acc_info, msg=f"Successfully claimed IP", type_msg='success')
                return True

        raise SoftwareException(f'Bad response from Story API: {response}')

    @helper
    async def claim_ip(self, from_checker: bool = False):
        eligible_status = await self.sign_msg()

        gitcoin_score = 0
        claimed = False
        if eligible_status:
            gitcoin_score, claimed = await self.process_claim()

        if from_checker:
            return eligible_status, gitcoin_score, claimed

        if gitcoin_score == 21 and claimed:
            return await self.claim_ip_util()

        return True

    def get_wallet_for_transfer(self):
        from config import ACCOUNTS_DATA

        cex_address = ACCOUNTS_DATA['accounts'][self.client.account_name].get('evm_deposit_address')

        if not cex_address:
            raise SoftwareExceptionWithoutRetry(f'There is no wallet listed for transfer, please add wallet into accounts_data.xlsx')

        return cex_address

    @helper
    async def transfer_ip(self):
        self.logger_msg(*self.client.acc_info, msg=f'Initiate IP transfer')

        transfer_address = self.get_wallet_for_transfer()

        balance_in_wei, balance = await self.client.get_smart_amount(settings=('100', '100'), fee_support=(0.05, 0.1))

        transaction = await self.client.prepare_transaction(value=balance_in_wei) | {
            'to': self.client.w3.to_checksum_address(transfer_address)
        }

        self.logger_msg(*self.client.acc_info, msg=f"Transfer {balance} IP to {transfer_address} address")

        return await self.client.send_transaction(transaction)
