from modules import *
from modules.interfaces import SoftwareException
from modules.solana_client import SolanaClient
from utils.networks import *


def get_client(module_input_data) -> EVMClient:
    return EVMClient(module_input_data)


def get_rpc_by_chain_name(chain_name):
    return {
        0: BeraChainRPC,
        "Arbitrum": ArbitrumRPC,
        "Arbitrum Nova": Arbitrum_novaRPC,
        "Base": BaseRPC,
        "Linea": LineaRPC,
        "Manta": MantaRPC,
        "Polygon": PolygonRPC,
        "Optimism": OptimismRPC,
        "Scroll": ScrollRPC,
        "Polygon zkEVM": Polygon_ZKEVM_RPC,
        "zkSync": zkSyncEraRPC,
        "Zora": ZoraRPC,
        "Ethereum": EthereumRPC,
        "Avalanche": AvalancheRPC,
        "BNB Chain": BSC_RPC,
        "BeraChain": BeraChainRPC
    }[chain_name]


async def bridge_utils(current_client, dapp_id, bridge_data, need_fee=False):
    class_bridge = {
        # 1: Across,
        # 2: Bungee,
        3: Relay,
    }[dapp_id]

    return await class_bridge(current_client).bridge(bridge_data, need_check=need_fee)


async def binance_withdraw(module_input_data):
    worker = Custom(get_client(module_input_data))
    return await worker.smart_cex_withdraw(dapp_id=3)


async def bridge_relay(module_input_data):
    worker = Custom(get_client(module_input_data))
    return await worker.smart_bridge(dapp_id=3)


async def story_claim(module_input_data):
    worker = StoryClaimer(get_client(module_input_data))
    return await worker.claim_ip()


async def story_transfer(module_input_data):
    module_input_data['network'] = StoryRPC
    worker = StoryClaimer(EVMClient(module_input_data))
    return await worker.transfer_ip()


async def movement_claim_on_l2(module_input_data):
    worker = MovementClaimer(get_client(module_input_data))
    return await worker.claim_on_l2()


async def movement_claim_on_ethereum(module_input_data):
    module_input_data['network'] = EthereumRPC
    worker = MovementClaimer(get_client(module_input_data))
    return await worker.claim_on_ethereum()


async def hyper_register_on_drop(module_input_data):
    private_key = module_input_data['evm_private_key']

    if len(private_key) < 20:
        raise SoftwareException('Please provide correct private key')
    elif len(private_key) in [64, 66]:
        module_input_data['network'] = EthereumRPC
        worker = HyperClaimer(EVMClient(module_input_data))
        return await worker.register_on_drop()
    else:
        module_input_data['network'] = SolanaRPC
        worker = HyperClaimer(SolanaClient(module_input_data))
        return await worker.register_on_drop(solana_client=True)


async def hyperlane_claim_drop(module_input_data):
    module_input_data['network'] = EthereumRPC
    worker = HyperClaimer(get_client(module_input_data))
    return await worker.claim_hyper()


async def movement_transfer_move(module_input_data):
    module_input_data['network'] = EthereumRPC
    worker = MovementClaimer(get_client(module_input_data))
    return await worker.transfer_move()


async def wrap_native(module_input_data):
    worker = Custom(get_client(module_input_data))
    return await worker.wrap_native()


async def unwrap_native(module_input_data):
    worker = Custom(get_client(module_input_data))
    return await worker.unwrap_native()


async def transfer_eth(module_input_data):
    module_input_data['network'] = EthereumRPC
    worker = Custom(EVMClient(module_input_data))
    return await worker.transfer_eth()
