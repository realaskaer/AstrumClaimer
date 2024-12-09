from modules import *
from utils.networks import *


def get_client(module_input_data) -> Client:
    return Client(module_input_data)


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


async def movement_claim_on_l2(module_input_data):
    worker = MovementClaimer(get_client(module_input_data))
    return await worker.claim_on_l2()


async def movement_claim_on_ethereum(module_input_data):
    module_input_data['network'] = EthereumRPC
    worker = MovementClaimer(get_client(module_input_data))
    return await worker.claim_on_ethereum()


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
    worker = Custom(get_client(module_input_data))
    return await worker.transfer_eth()
