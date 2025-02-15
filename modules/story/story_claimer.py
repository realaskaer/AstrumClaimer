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
                passport_score = 20
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

    @helper
    async def claim_ip(self, from_checker: bool = False):
        eligible_status = await self.sign_msg()

        gitcoin_score = 0
        claimed = False
        if eligible_status:
            gitcoin_score, claimed = await self.process_claim()

        if from_checker:
            return eligible_status, gitcoin_score, claimed

        return True

    @helper
    @gas_checker
    async def transfer_move(self):
        self.logger_msg(*self.client.acc_info, msg=f'Initiate transfer')

        transfer_address = self.get_wallet_for_transfer()

        balance_in_wei, balance, _ = await self.client.get_token_balance(
            token_name="MOVE", token_address="0x3073f7aAA4DB83f95e9FFf17424F71D4751a3073"
        )

        token_contract = self.client.get_contract("0x3073f7aAA4DB83f95e9FFf17424F71D4751a3073")

        try:
            transaction = await token_contract.functions.transfer(
                self.client.w3.to_checksum_address(transfer_address),
                balance_in_wei
            ).build_transaction(await self.client.prepare_transaction())
        except Exception as error:
            if 'no data' in str(error):
                raise SoftwareException('Not enough ETH for cover gas fee')
            else:
                raise error

        self.logger_msg(*self.client.acc_info, msg=f"Transfer {balance} MOVE to {transfer_address} address")

        return await self.client.send_transaction(transaction)
