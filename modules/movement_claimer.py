from eth_abi import abi

from config import MOVEMENT_ABI
from utils.tools import helper, gas_checker
from .interfaces import Logger, RequestClient, SoftwareException, SoftwareExceptionWithoutRetry
from .client import Client


class MovementClaimer(Logger, RequestClient):
    def __init__(self, client: Client):
        Logger.__init__(self)
        RequestClient.__init__(self, client)
        self.client = client
        self.nonce = None

        self.headers = {
            'accept': '*/*',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
            'priority': 'u=1, i',
            'referer': 'https://claims.movementnetwork.xyz/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

        self.fee_contract = self.client.get_contract(
            contract_address='0x429d6E96bbD6b4134c92954c71200BD0BEA751fb',
            abi=MOVEMENT_ABI['fee_collector']
        )

        self.claim_contract = self.client.get_contract(
            contract_address='0x4B3883cCE3313Ed4445a897355032c273fd87A6f',
            abi=MOVEMENT_ABI['claimer']
        )

    async def get_nonce(self):
        if not self.nonce:
            url = 'https://claims.movementnetwork.xyz/api/get-nonce'

            response = await self.make_request(url=url, headers=self.headers)

            self.nonce = response['nonce']

    async def get_drop_status(self):
        await self.get_nonce()

        url = 'https://claims.movementnetwork.xyz/api/claim/start'

        msg_to_sign = f'Please sign this message to confirm ownership. nonce: {self.nonce}'
        signature = await self.client.sign_message(msg_to_sign)

        json_data = {
            'address': f"{self.client.address}",
            'message': f'Please sign this message to confirm ownership. nonce: {self.nonce}',
            'signature': signature,
            'nonce': self.nonce,
        }

        response = await self.make_request("POST", url, headers=self.headers, json=json_data)

        if response.get('success'):
            if response['eligibility_status'] == 'eligible':
                move_drop, move_l2_drop = response['amount'], response['amountL2']
                self.client.logger_msg(
                    *self.client.acc_info, msg=f'You are eligible to claim $MOVE: Now: {move_drop}, L2: {move_l2_drop}',
                    type_msg='success'
                )
                return move_drop, move_l2_drop
            elif response['eligibility_status'] == 'claimed_l2':
                move_l2_drop = response['amountL2']
                self.client.logger_msg(
                    *self.client.acc_info, msg=f'You are already claimed {move_l2_drop} $MOVE on L2',
                    type_msg='success'
                )
                return False
        else:
            raise SoftwareExceptionWithoutRetry(f'You are not eligible to claim $MOVE')

    @helper
    async def claim_on_l2(self):
        self.logger_msg(*self.client.acc_info, msg=f'Initiate claiming on L2 Movement Mainnet')

        url = 'https://claims.movementnetwork.xyz/api/claim/l2'

        claim_status = await self.get_drop_status()

        if not claim_status:
            return True

        msg_to_sign = f'Please sign this message to confirm ownership. nonce: {self.nonce}'
        signature = await self.client.sign_message(msg_to_sign)

        json_data = {
            'address': self.client.address.lower(),
            'signature': signature,
            'message': msg_to_sign,
        }

        response = await self.make_request("POST", url=url, headers=self.headers, json=json_data)

        if response.get('success'):
            self.logger_msg(*self.client.acc_info, msg=f'{response["message"]}', type_msg='success')
            return True

        raise SoftwareException(f'Failed to claim on l2, response: {response}')

    async def get_project_id(self):
        url = 'https://claim.tokentable.xyz/api/airdrop-open/query-pid'

        json_data = {
            'recipient': self.client.address,
            'slug': 'move',
        }

        response = await self.make_request("POST", url=url, headers=self.headers, json=json_data)

        if response.get('success'):
            return response['data']['projectIds'][0]

        raise SoftwareException(f"Bad request to Movement API: {response}")

    async def get_claim_data(self, project_id):
        url = 'https://claim.tokentable.xyz/api/airdrop-open/query'

        json_data = {
            'recipient': self.client.address,
            'projectId': project_id,
            'recipientType': 'WalletAddress',
        }

        response = await self.make_request("POST", url=url, headers=self.headers, json=json_data)

        if response.get('success'):
            return response['data']['claims'][0]

        raise SoftwareException(f"Bad request to Movement API: {response}")

    @helper
    @gas_checker
    async def claim_on_ethereum(self):
        self.logger_msg(*self.client.acc_info, msg=f'Initiate claiming on Ethereum')

        claim_status = await self.get_drop_status()

        if not claim_status:
            return True

        project_id = await self.get_project_id()
        claim_data = await self.get_claim_data(project_id)

        amount_to_claim = int(claim_data['amount'])

        claim_fee = await self.fee_contract.functions.getFee(
            "0x4B3883cCE3313Ed4445a897355032c273fd87A6f",
            amount_to_claim
        ).call()

        transaction = await self.claim_contract.functions.claim(
            claim_data['proof'],
            abi.encode(['int'], [0]),
            claim_data['data'],
            abi.encode(['int', 'int'], [1, 1])
        ).build_transaction(await self.client.prepare_transaction(value=claim_fee))

        return await self.client.send_transaction(transaction)