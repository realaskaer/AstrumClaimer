class Network:
    def __init__(
            self,
            name: str,
            rpc: list,
            chain_id: int,
            eip1559_support: bool,
            token: str,
            explorer: str,
            decimals: int = 18
    ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_support = eip1559_support
        self.token = token
        self.explorer = explorer
        self.decimals = decimals

    def __repr__(self):
        return f'{self.name}'


BeraChainRPC = Network(
    name='BeraChain',
    rpc=[
        'https://bartio.rpc.berachain.com'
    ],
    chain_id=80084,
    eip1559_support=True,
    token='BERA',
    explorer='https://bartio.beratrail.io/'
)

EthereumRPC = Network(
    name='Ethereum',
    rpc=[
        'https://eth.drpc.org'
    ],
    chain_id=1,
    eip1559_support=False,
    token='ETH',
    explorer='https://etherscan.io/'
)

ScrollRPC = Network(
    name='Scroll',
    rpc=[
        'https://rpc.scroll.io',
        'https://rpc.ankr.com/scroll',
    ],
    chain_id=534352,
    eip1559_support=False,
    token='ETH',
    explorer='https://scrollscan.com/'
)

ArbitrumRPC = Network(
    name='Arbitrum',
    rpc=[
        'https://arb1.arbitrum.io/rpc',
    ],
    chain_id=42161,
    eip1559_support=False,
    token='ETH',
    explorer='https://arbiscan.io/',
)

PolygonRPC = Network(
    name='Polygon',
    rpc=[
        'https://polygon-rpc.com',
    ],
    chain_id=137,
    eip1559_support=False,
    token='MATIC',
    explorer='https://polygonscan.com/',
)

AvalancheRPC = Network(
    name='Avalanche',
    rpc=[
        'https://avalanche.drpc.org'
    ],
    chain_id=43114,
    eip1559_support=False,
    token='AVAX',
    explorer='https://snowtrace.io/',
)

Arbitrum_novaRPC = Network(
    name='Arbitrum Nova',
    rpc=[
        'https://rpc.ankr.com/arbitrumnova',
        'https://arbitrum-nova.publicnode.com',
        'https://arbitrum-nova.drpc.org',
        'https://nova.arbitrum.io/rpc'
    ],
    chain_id=42170,
    eip1559_support=False,
    token='ETH',
    explorer='https://nova.arbiscan.io/'
)

BaseRPC = Network(
    name='Base',
    rpc=[
        'https://mainnet.base.org',
    ],
    chain_id=8453,
    eip1559_support=False,
    token='ETH',
    explorer='https://basescan.org/'
)

LineaRPC = Network(
    name='Linea',
    rpc=[
        # 'https://linea.drpc.org',
        'https://rpc.linea.build'
    ],
    chain_id=59144,
    eip1559_support=False,
    token='ETH',
    explorer='https://lineascan.build/'
)

ZoraRPC = Network(
    name='Zora',
    rpc=[
        'https://rpc.zora.energy'
    ],
    chain_id=7777777,
    eip1559_support=False,
    token='ETH',
    explorer='https://zora.superscan.network/'
)

Polygon_ZKEVM_RPC = Network(
    name='Polygon zkEVM',
    rpc=[
        'https://1rpc.io/polygon/zkevm',
        'https://zkevm-rpc.com',
        'https://rpc.ankr.com/polygon_zkevm'
    ],
    chain_id=1101,
    eip1559_support=False,
    token='ETH',
    explorer='https://zkevm.polygonscan.com/'
)

BSC_RPC = Network(
    name='BNB Chain',
    rpc=[
        'https://binance.llamarpc.com',
    ],
    chain_id=56,
    eip1559_support=False,
    token='BNB',
    explorer='https://bscscan.com/'
)

MantaRPC = Network(
    name='Manta',
    rpc=[
        'https://pacific-rpc.manta.network/http'
        'https://1rpc.io/manta'
    ],
    chain_id=169,
    eip1559_support=False,
    token='ETH',
    explorer='https://pacific-explorer.manta.network/'
)

OptimismRPC = Network(
    name='Optimism',
    rpc=[
        # 'https://optimism.llamarpc.com',
        'https://mainnet.optimism.io',
        # 'https://optimism.drpc.org',
    ],
    chain_id=10,
    eip1559_support=False,
    token='ETH',
    explorer='https://optimistic.etherscan.io/',
)

zkSyncEraRPC = Network(
    name='zkSync',
    rpc=[
        'https://mainnet.era.zksync.io',
    ],
    chain_id=324,
    eip1559_support=False,
    token='ETH',
    explorer='https://era.zksync.network/',
)

StoryRPC = Network(
    name="Story",
    rpc=[
        "https://mainnet.storyrpc.io",
    ],
    chain_id=1514,
    eip1559_support=False,
    token="IP",
    explorer="https://www.okx.com/ru/web3/explorer/story/",
)

SolanaRPC = Network(
    name="Solana",
    rpc=[
        "https://mainnet.helius-rpc.com/?api-key=6ef7a874-4198-4317-b1c6-22f875ec7efc",
    ],
    chain_id=1151111081099710,
    eip1559_support=False,
    token="SOL",
    explorer="https://solscan.io/",
)
