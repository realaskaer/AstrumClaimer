from eth_abi import abi
from web3.contract import AsyncContract
from config import TOKENS_PER_CHAIN
from config import USENEXUS_ABI
from dev import Settings
from modules import Logger, EVMClient
from modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry
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

        bridge_gas_fee = await bridge_contract.functions.quoteGasPayment(dest_chain_int).call()

        from config import ACCOUNTS_DATA

        transfer_address = ACCOUNTS_DATA['accounts'][self.client.account_name].get('evm_deposit_address')

        if not transfer_address:
            if not Settings.HYPERLANE_USENEXUS_ADDRESS:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'There is no wallet listed for transfer, will use self address',
                    type_msg='warning'
                )
                transfer_address = self.client.address
            else:
                raise SoftwareExceptionWithoutRetry(
                    f'There is no wallet listed for transfer, please add wallet into accounts_data.xlsx'
                )

        int_address = self.client.w3.to_int(hexstr=transfer_address)
        dst_address = abi.encode(['uint256'], [int_address])

        try:
            transaction = await bridge_contract.functions.transferRemote(
                dest_chain_int,
                dst_address,
                amount_in_wei
            ).build_transaction(await self.client.prepare_transaction(value=bridge_gas_fee))
        except Exception as error:
            if 'gas required exceeds' in str(error) or 'insufficient funds' in str(error):
                from modules.custom_modules import Custom

                cex_chain_id = {
                    'Arbitrum': 2,
                    'Optimism': 3,
                    'Base': 6,
                    'BNB Chain': 8,
                }[self.client.network.name]

                Settings.OKX_WITHDRAW_DATA = [
                    [cex_chain_id, (0.00035, 0.0004)],
                ]

                await Custom(self.client).smart_cex_withdraw(dapp_id=Settings.HYPERLANE_CEX_USE)
                raise SoftwareException('Exception for retry...')
            else:
                raise error

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
