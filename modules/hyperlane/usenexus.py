from eth_abi import abi
from web3.contract import AsyncContract
from config import TOKENS_PER_CHAIN
from config import USENEXUS_ABI
from modules import Logger, EVMClient
from utils.tools import helper, gas_checker


class UseNexus(Logger):
    def __init__(self, client: EVMClient):
        self.client = client
        Logger.__init__(self)

    @helper
    @gas_checker
    async def bridge(self, bridge_data):
        src_chain_name, amount, amount_in_wei = bridge_data

        dest_chain_int = 56

        bridge_info = f'{amount} HYPER {src_chain_name} -> HYPER BNB Chain'
        self.logger_msg(*self.client.acc_info, msg=f'Bridge on UseNexus: {bridge_info}')

        bridge_contract: AsyncContract = self.client.get_contract(
            TOKENS_PER_CHAIN[self.client.network.name]['HYPER'], USENEXUS_ABI['router']
        )

        bridge_gas_fee = await bridge_contract.functions.quoteGasPayment(
            dest_chain_int
        ).call()

        int_address = self.client.w3.to_int(hexstr=self.client.address)
        dst_address = abi.encode(['uint256'], [int_address])

        transaction = await bridge_contract.functions.transferRemote(
            dest_chain_int,
            dst_address,
            amount_in_wei
        ).build_transaction(await self.client.prepare_transaction(value=bridge_gas_fee))

        old_balance_data_on_dst = await self.client.wait_for_receiving(
            chain_to_name='BNB Chain', token_name="HYPER", check_balance_on_dst=True
        )

        await self.client.send_transaction(transaction)

        self.logger_msg(
            *self.client.acc_info, msg=f"Bridge complete. Note: wait a little for receiving funds",
            type_msg='success'
        )

        return await self.client.wait_for_receiving(
            chain_to_name='BNB Chain', token_name="HYPER", old_balance_data=old_balance_data_on_dst,
        )
