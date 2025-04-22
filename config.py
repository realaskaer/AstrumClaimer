from dev import GeneralSettings
from utils.tools import get_accounts_data

TOTAL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

HYPERLANE_ABI = [{'inputs': [{'internalType': 'address', 'name': 'token_', 'type': 'address'}, {'internalType': 'bytes32', 'name': 'merkleRoot_', 'type': 'bytes32'}, {'internalType': 'uint256', 'name': 'endTime_', 'type': 'uint256'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'inputs': [], 'name': 'AlreadyClaimed', 'type': 'error'}, {'inputs': [], 'name': 'ClaimWindowFinished', 'type': 'error'}, {'inputs': [], 'name': 'EndTimeInPast', 'type': 'error'}, {'inputs': [], 'name': 'InvalidProof', 'type': 'error'}, {'inputs': [], 'name': 'NoWithdrawDuringClaim', 'type': 'error'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'uint256', 'name': 'index', 'type': 'uint256'}, {'indexed': False, 'internalType': 'address', 'name': 'account', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'Claimed', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'previousOwner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'newOwner', 'type': 'address'}], 'name': 'OwnershipTransferred', 'type': 'event'}, {'inputs': [{'internalType': 'uint256', 'name': 'index', 'type': 'uint256'}, {'internalType': 'address', 'name': 'account', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}, {'internalType': 'bytes32[]', 'name': 'merkleProof', 'type': 'bytes32[]'}], 'name': 'claim', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'endTime', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'index', 'type': 'uint256'}], 'name': 'isClaimed', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'merkleRoot', 'outputs': [{'internalType': 'bytes32', 'name': '', 'type': 'bytes32'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'owner', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'renounceOwnership', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'token', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'newOwner', 'type': 'address'}], 'name': 'transferOwnership', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'withdraw', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}]

MOVEMENT_ABI = {
    'claimer': [{"inputs":[{"internalType":"address","name":"target","type":"address"}],"name":"AddressEmptyCode","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"AddressInsufficientBalance","type":"error"},{"inputs":[{"internalType":"address","name":"implementation","type":"address"}],"name":"ERC1967InvalidImplementation","type":"error"},{"inputs":[],"name":"ERC1967NonPayable","type":"error"},{"inputs":[],"name":"FailedInnerCall","type":"error"},{"inputs":[],"name":"IncorrectFees","type":"error"},{"inputs":[],"name":"InvalidInitialization","type":"error"},{"inputs":[],"name":"InvalidProof","type":"error"},{"inputs":[],"name":"LeafUsed","type":"error"},{"inputs":[],"name":"NotInitializing","type":"error"},{"inputs":[],"name":"OutsideClaimableTimeRange","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},{"inputs":[],"name":"ReentrancyGuardReentrantCall","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"SafeERC20FailedOperation","type":"error"},{"inputs":[],"name":"TimeInactive","type":"error"},{"inputs":[],"name":"UUPSUnauthorizedCallContext","type":"error"},{"inputs":[{"internalType":"bytes32","name":"slot","type":"bytes32"}],"name":"UUPSUnsupportedProxiableUUID","type":"error"},{"inputs":[],"name":"UnsupportedOperation","type":"error"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"delegate","type":"address"}],"name":"ClaimDelegateSet","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"recipient","type":"address"},{"indexed":False,"internalType":"bytes32","name":"group","type":"bytes32"},{"indexed":False,"internalType":"bytes","name":"data","type":"bytes"}],"name":"Claimed","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint64","name":"version","type":"uint64"}],"name":"Initialized","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"implementation","type":"address"}],"name":"Upgraded","type":"event"},{"inputs":[],"name":"UPGRADE_INTERFACE_VERSION","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address[]","name":"recipients","type":"address[]"},{"internalType":"bytes32[][]","name":"proofs","type":"bytes32[][]"},{"internalType":"bytes32[]","name":"groups","type":"bytes32[]"},{"internalType":"bytes[]","name":"datas","type":"bytes[]"},{"internalType":"bytes[]","name":"extraDatas","type":"bytes[]"}],"name":"batchDelegateClaim","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"proof","type":"bytes32[]"},{"internalType":"bytes32","name":"group","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"name":"claim","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes","name":"data","type":"bytes"}],"name":"decodeLeafData","outputs":[{"components":[{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"claimableTimestamp","type":"uint256"},{"internalType":"uint256","name":"claimableAmount","type":"uint256"}],"internalType":"struct TokenTableMerkleDistributorData","name":"","type":"tuple"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"bytes32[]","name":"proof","type":"bytes32[]"},{"internalType":"bytes32","name":"group","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"name":"delegateClaim","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"bytes32","name":"group","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"encodeLeaf","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getClaimDelegate","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getClaimHook","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getDeployer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getRoot","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTime","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getToken","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner_","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"leaf","type":"bytes32"}],"name":"isLeafUsed","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"proxiableUUID","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"root","type":"bytes32"}],"name":"setBaseParams","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"delegate","type":"address"}],"name":"setClaimDelegate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"hook","type":"address"}],"name":"setClaimHook","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newImplementation","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"upgradeToAndCall","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"proof","type":"bytes32[]"},{"internalType":"bytes32","name":"leaf","type":"bytes32"}],"name":"verify","outputs":[],"stateMutability":"view","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"bytes","name":"","type":"bytes"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}],
    'fee_collector': [{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"target","type":"address"}],"name":"AddressEmptyCode","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"AddressInsufficientBalance","type":"error"},{"inputs":[],"name":"FailedInnerCall","type":"error"},{"inputs":[],"name":"FeesTooHigh","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"SafeERC20FailedOperation","type":"error"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"unlockerAddress","type":"address"},{"indexed":False,"internalType":"uint256","name":"bips","type":"uint256"}],"name":"CustomFeeSetBips","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"unlockerAddress","type":"address"},{"indexed":False,"internalType":"uint256","name":"fixedFee","type":"uint256"}],"name":"CustomFeeSetFixed","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"bips","type":"uint256"}],"name":"DefaultFeeSetBips","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"BIPS_PRECISION","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"MAX_FEE_BIPS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"defaultFeesBips","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"unlockerAddress","type":"address"},{"internalType":"uint256","name":"tokenTransferred","type":"uint256"}],"name":"getFee","outputs":[{"internalType":"uint256","name":"tokensCollected","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"unlockerAddress","type":"address"},{"internalType":"uint256","name":"bips","type":"uint256"}],"name":"setCustomFeeBips","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"unlockerAddress","type":"address"},{"internalType":"uint256","name":"fixedFee","type":"uint256"}],"name":"setCustomFeeFixed","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"bips","type":"uint256"}],"name":"setDefaultFeeBips","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdrawFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]
}

USENEXUS_ABI = {
    'router': [{'inputs': [{'internalType': 'uint8', 'name': '__decimals', 'type': 'uint8'}, {'internalType': 'address', 'name': '_mailbox', 'type': 'address'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'Approval', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'uint8', 'name': 'version', 'type': 'uint8'}], 'name': 'Initialized', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'previousOwner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'newOwner', 'type': 'address'}], 'name': 'OwnershipTransferred', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'uint32', 'name': 'origin', 'type': 'uint32'}, {'indexed': True, 'internalType': 'bytes32', 'name': 'recipient', 'type': 'bytes32'}, {'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'ReceivedTransferRemote', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'uint32', 'name': 'destination', 'type': 'uint32'}, {'indexed': True, 'internalType': 'bytes32', 'name': 'recipient', 'type': 'bytes32'}, {'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'SentTransferRemote', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'from', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'to', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'address', 'name': 'spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_account', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'decimals', 'outputs': [{'internalType': 'uint8', 'name': '', 'type': 'uint8'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'subtractedValue', 'type': 'uint256'}], 'name': 'decreaseAllowance', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '', 'type': 'uint32'}], 'name': 'destinationGas', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'domains', 'outputs': [{'internalType': 'uint32[]', 'name': '', 'type': 'uint32[]'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '_domain', 'type': 'uint32'}, {'internalType': 'bytes32', 'name': '_router', 'type': 'bytes32'}], 'name': 'enrollRemoteRouter', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32[]', 'name': '_domains', 'type': 'uint32[]'}, {'internalType': 'bytes32[]', 'name': '_addresses', 'type': 'bytes32[]'}], 'name': 'enrollRemoteRouters', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '_origin', 'type': 'uint32'}, {'internalType': 'bytes32', 'name': '_sender', 'type': 'bytes32'}, {'internalType': 'bytes', 'name': '_message', 'type': 'bytes'}], 'name': 'handle', 'outputs': [], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [], 'name': 'hook', 'outputs': [{'internalType': 'contract IPostDispatchHook', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'addedValue', 'type': 'uint256'}], 'name': 'increaseAllowance', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': '_totalSupply', 'type': 'uint256'}, {'internalType': 'string', 'name': '_name', 'type': 'string'}, {'internalType': 'string', 'name': '_symbol', 'type': 'string'}], 'name': 'initialize', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'interchainSecurityModule', 'outputs': [{'internalType': 'contract IInterchainSecurityModule', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'localDomain', 'outputs': [{'internalType': 'uint32', 'name': '', 'type': 'uint32'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'mailbox', 'outputs': [{'internalType': 'contract IMailbox', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'name', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'owner', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '_destinationDomain', 'type': 'uint32'}], 'name': 'quoteGasPayment', 'outputs': [{'internalType': 'uint256', 'name': '_gasPayment', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'renounceOwnership', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '_domain', 'type': 'uint32'}], 'name': 'routers', 'outputs': [{'internalType': 'bytes32', 'name': '', 'type': 'bytes32'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': 'domain', 'type': 'uint32'}, {'internalType': 'uint256', 'name': 'gas', 'type': 'uint256'}], 'name': 'setDestinationGas', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'components': [{'internalType': 'uint32', 'name': 'domain', 'type': 'uint32'}, {'internalType': 'uint256', 'name': 'gas', 'type': 'uint256'}], 'internalType': 'struct GasRouter.GasRouterConfig[]', 'name': 'gasConfigs', 'type': 'tuple[]'}], 'name': 'setDestinationGas', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_hook', 'type': 'address'}], 'name': 'setHook', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_module', 'type': 'address'}], 'name': 'setInterchainSecurityModule', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'symbol', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'totalSupply', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'from', 'type': 'address'}, {'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transferFrom', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'newOwner', 'type': 'address'}], 'name': 'transferOwnership', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '_destination', 'type': 'uint32'}, {'internalType': 'bytes32', 'name': '_recipient', 'type': 'bytes32'}, {'internalType': 'uint256', 'name': '_amountOrId', 'type': 'uint256'}], 'name': 'transferRemote', 'outputs': [{'internalType': 'bytes32', 'name': 'messageId', 'type': 'bytes32'}], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32', 'name': '_domain', 'type': 'uint32'}], 'name': 'unenrollRemoteRouter', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint32[]', 'name': '_domains', 'type': 'uint32[]'}], 'name': 'unenrollRemoteRouters', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}]
}

ERC20_ABI = [{'inputs': [{'internalType': 'string', 'name': '_name', 'type': 'string'}, {'internalType': 'string', 'name': '_symbol', 'type': 'string'}, {'internalType': 'uint256', 'name': '_initialSupply', 'type': 'uint256'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'Approval', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'from', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'to', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'address', 'name': 'spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'account', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'decimals', 'outputs': [{'internalType': 'uint8', 'name': '', 'type': 'uint8'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'subtractedValue', 'type': 'uint256'}], 'name': 'decreaseAllowance', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'addedValue', 'type': 'uint256'}], 'name': 'increaseAllowance', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'name', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint8', 'name': 'decimals_', 'type': 'uint8'}], 'name': 'setupDecimals', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'symbol', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'totalSupply', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'recipient', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'sender', 'type': 'address'}, {'internalType': 'address', 'name': 'recipient', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transferFrom', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}]

WETH_ABI = [{'inputs': [], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'Approval', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': '_account', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': '_amount', 'type': 'uint256'}], 'name': 'BridgeBurn', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'l1Token', 'type': 'address'}, {'indexed': False, 'internalType': 'string', 'name': 'name', 'type': 'string'}, {'indexed': False, 'internalType': 'string', 'name': 'symbol', 'type': 'string'}, {'indexed': False, 'internalType': 'uint8', 'name': 'decimals', 'type': 'uint8'}], 'name': 'BridgeInitialize', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': '_account', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': '_amount', 'type': 'uint256'}], 'name': 'BridgeMint', 'type': 'event'}, {'anonymous': False, 'inputs': [], 'name': 'EIP712DomainChanged', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'string', 'name': 'name', 'type': 'string'}, {'indexed': False, 'internalType': 'string', 'name': 'symbol', 'type': 'string'}, {'indexed': False, 'internalType': 'uint8', 'name': 'decimals', 'type': 'uint8'}], 'name': 'Initialize', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'uint8', 'name': 'version', 'type': 'uint8'}], 'name': 'Initialized', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'from', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'to', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'}, {'inputs': [], 'name': 'DOMAIN_SEPARATOR', 'outputs': [{'internalType': 'bytes32', 'name': '', 'type': 'bytes32'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'address', 'name': 'spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'account', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_from', 'type': 'address'}, {'internalType': 'uint256', 'name': '_amount', 'type': 'uint256'}], 'name': 'bridgeBurn', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '', 'type': 'address'}, {'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'name': 'bridgeMint', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'decimals', 'outputs': [{'internalType': 'uint8', 'name': '', 'type': 'uint8'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'subtractedValue', 'type': 'uint256'}], 'name': 'decreaseAllowance', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'deposit', 'outputs': [], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_to', 'type': 'address'}], 'name': 'depositTo', 'outputs': [], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [], 'name': 'eip712Domain', 'outputs': [{'internalType': 'bytes1', 'name': 'fields', 'type': 'bytes1'}, {'internalType': 'string', 'name': 'name', 'type': 'string'}, {'internalType': 'string', 'name': 'version', 'type': 'string'}, {'internalType': 'uint256', 'name': 'chainId', 'type': 'uint256'}, {'internalType': 'address', 'name': 'verifyingContract', 'type': 'address'}, {'internalType': 'bytes32', 'name': 'salt', 'type': 'bytes32'}, {'internalType': 'uint256[]', 'name': 'extensions', 'type': 'uint256[]'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'addedValue', 'type': 'uint256'}], 'name': 'increaseAllowance', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'string', 'name': 'name_', 'type': 'string'}, {'internalType': 'string', 'name': 'symbol_', 'type': 'string'}], 'name': 'initialize', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'l1Address', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'l2Bridge', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'name', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}], 'name': 'nonces', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'address', 'name': 'spender', 'type': 'address'}, {'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'deadline', 'type': 'uint256'}, {'internalType': 'uint8', 'name': 'v', 'type': 'uint8'}, {'internalType': 'bytes32', 'name': 'r', 'type': 'bytes32'}, {'internalType': 'bytes32', 'name': 's', 'type': 'bytes32'}], 'name': 'permit', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'symbol', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'totalSupply', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'from', 'type': 'address'}, {'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transferFrom', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': '_amount', 'type': 'uint256'}], 'name': 'withdraw', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_to', 'type': 'address'}, {'internalType': 'uint256', 'name': '_amount', 'type': 'uint256'}], 'name': 'withdrawTo', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'stateMutability': 'payable', 'type': 'receive'}]

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

ETH_MASK = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'

TOKENS_PER_CHAIN = {
    'Ethereum': {
        'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'ZRO': '0x6985884C4392D348587B19cb9eAAf157F13271cd',
        'USDC': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'USDT': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'TIA.n': '0x15b5D6B614242B118AA404528A7f3E2Ad241e4A4',
        'STG': '0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6',
        'USDV': '0x0E573Ce2736Dd9637A0b21058352e1667925C7a8',
        'MAV': '0x7448c7456a97769F6cD04F1E83A4a23cCdC46aBD',
        'HYPER': '0x93A2Db22B7c736B341C32Ff666307F4a9ED910F5',
        'ezETH': '0xbf5495Efe5DB9ce00f80364C8B423567e58d2110'
    },
    'Arbitrum': {
        "ETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "ZRO": "0x6985884C4392D348587B19cb9eAAf157F13271cd",
        'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        'USDC.e': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        'fUSDC': '0x4CFA50B7Ce747e2D61724fcAc57f24B748FF2b2A',
        'TIA.n': '0xD56734d7f9979dD94FAE3d67C7e928234e71cD4C',
        'STG': '0x6694340fc020c5E6B96567843da2df01b2CE1eb6',
        'USDV': '0x323665443CEf804A3b5206103304BD4872EA4253',
        'HYPER': '0xC9d23ED2ADB0f551369946BD377f8644cE1ca5c4',
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    'Manta': {
        "ETH": "0x0Dc808adcE2099A9F62AA87D9670745AbA741746",
        "WETH": "0x0Dc808adcE2099A9F62AA87D9670745AbA741746",
        'USDC': '0x09Bc4E0D864854c6aFB6eB9A9cdF58aC190D0dF9',
        'USDT': '0x201EBa5CC46D216Ce6DC03F6a759e8E766e956aE',
        'TIA.n': '0x6Fae4D9935E2fcb11fC79a64e917fb2BF14DaFaa',
    },
    'Polygon': {
        'MATIC': "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        'WMATIC': "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        'WETH': "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        'ZRO': "0x6985884C4392D348587B19cb9eAAf157F13271cd",
        'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        'STG': '0x2F6F07CDcf3588944Bf4C42aC74ff24bF56e7590',
        'USDV': '0x323665443CEf804A3b5206103304BD4872EA4253',
    },
    'BNB Chain': {
        'BNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
        'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
        'WETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
        'USDT': '0x55d398326f99059fF775485246999027B3197955',
        'ZRO': '0x6985884C4392D348587B19cb9eAAf157F13271cd',
        'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
        'ZBC': '0x37a56cdcD83Dce2868f721De58cB3830C44C6303',
        'STG': '0xB0D502E938ed5f4df2E681fE6E419ff29631d62b',
        'USDV': '0x323665443CEf804A3b5206103304BD4872EA4253',
        'MAV': '0xd691d9a68C887BDF34DA8c36f63487333ACfD103',
        'HYPER': '0xC9d23ED2ADB0f551369946BD377f8644cE1ca5c4',
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    "Avalanche": {
        'AVAX': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7',
        'WAVAX': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7',
        'WETH': '0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB',
        'ZRO': '0x6985884C4392D348587B19cb9eAAf157F13271cd',
        'USDC': '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',
        'USDC.e': '0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664',
        'USDT': '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7',
        'STG': '0x2F6F07CDcf3588944Bf4C42aC74ff24bF56e7590',
        'USDV': '0x323665443CEf804A3b5206103304BD4872EA4253',
    },
    'Arbitrum Nova': {
        "ETH": "0x722E8BdD2ce80A4422E880164f2079488e115365",
        "WETH": "0x722E8BdD2ce80A4422E880164f2079488e115365",
        "USDC": "0x750ba8b76187092B0D1E87E28daaf484d1b5273b",
        "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
    },
    'Blast': {
        "ETH": "0x4300000000000000000000000000000000000004",
        "WETH": "0x4300000000000000000000000000000000000004",
        "USDB": "0x4300000000000000000000000000000000000003",
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    'Zora': {
        "ETH": "0x4200000000000000000000000000000000000006",
        "WETH": "0x4200000000000000000000000000000000000006"
    },
    'Fantom': {
        'USDC': '0x28a92dde19D9989F39A49905d7C9C2FAc7799bDf',
        'STG': '0x2F6F07CDcf3588944Bf4C42aC74ff24bF56e7590',
    },
    "Optimism": {
        "ETH": "0x4200000000000000000000000000000000000006",
        "ZRO": "0x6985884C4392D348587B19cb9eAAf157F13271cd",
        "WETH": "0x4200000000000000000000000000000000000006",
        "OP": "0x4200000000000000000000000000000000000042",
        "USDC": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
        "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
        "USDC.e": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
        "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        'STG': '0x296F55F8Fb28E498B858d0BcDA06D955B2Cb3f97',
        'USDV': '0x323665443CEf804A3b5206103304BD4872EA4253',
        'HYPER': '0x9923DB8d7FBAcC2E69E87fAd19b886C81cd74979',
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    "Mode": {
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    "Polygon zkEVM": {
        'ETH': "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9",
        'WETH': "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9",
    },
    "zkSync": {
        "ETH": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",
        "WETH": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",
        'MAV': '0x787c09494Ec8Bcb24DcAf8659E7d5D69979eE508',
        "USDC": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
        "USDC.e": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
        "USDT": "0x493257fD37EDB34451f62EDf8D2a0C418852bA4C",
    },
    "Taiko": {
        "ETH": "0xA51894664A773981C6C112C43ce576f315d5b1B6",
        "WETH": "0xA51894664A773981C6C112C43ce576f315d5b1B6",
        "USDC": "0x07d83526730c7438048D55A4fc0b850e2aaB6f0b"
    },
    "Base": {
        "ETH": "0x4200000000000000000000000000000000000006",
        "WETH": "0x4200000000000000000000000000000000000006",
        'ZRO': '0x6985884C4392D348587B19cb9eAAf157F13271cd',
        'USDC': '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA',
        'USDC.e': '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA',
        'STG': '0xE3B53AF74a4BF62Ae5511055290838050bf764Df',
        'MAV': '0x64b88c73A5DfA78D1713fE1b4c69a22d7E0faAa7',
        'HYPER': '0xC9d23ED2ADB0f551369946BD377f8644cE1ca5c4',
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    "Linea": {
        "ETH": "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f",
        "WETH": "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f",
        "USDT": "0xA219439258ca9da29E9Cc4cE5596924745e12B93",
        "USDC": "0x176211869cA2b568f2A7D4EE941E073a821EE1ff",
        'STG': '0x808d7c71ad2ba3FA531b068a2417C63106BC0949',
        'ezETH': '0x2416092f143378750bb29b79eD961ab195CcEea5'
    },
    "Scroll": {
        "ETH": "0x5300000000000000000000000000000000000004",
        "WETH": "0x5300000000000000000000000000000000000004",
        "wrsETH": "0xa25b25548B4C98B0c7d3d27dcA5D5ca743d68b7F",
        "USDT": "0xf55BEC9cafDbE8730f096Aa55dad6D22d44099Df",
        "USDC": "0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4",
    },
    'Kava':{
        'USDT': '0x919C1c267BC06a7039e03fcc2eF738525769109c',
        'STG': '0x83c30eb8bc9ad7C56532895840039E62659896ea',
    },
    'Mantle': {
        'USDC': '0x09Bc4E0D864854c6aFB6eB9A9cdF58aC190D0dF9',
        'USDT': '0x201EBa5CC46D216Ce6DC03F6a759e8E766e956aE',
        'STG': '0x8731d54E9D02c286767d56ac03e8037C07e01e98',
    }
}

TOKEN_API_INFO = {
    'coingecko': {
        'COREDAO': 'coredaoorg',
        'JEWEL': 'defi-kingdoms',
        'SMR': 'shimmer',
        'TOMOE': 'tomoe',
        'ZBC': 'zebec-protocol'
    },
    'binance': [
        'ETH',
        'ASTR',
        'AVAX',
        'BNB',
        'WBNB',
        'CELO',
        'CFX',
        'FTM',
        'GETH'
        'ONE',
        'ZEN',
        'KAVA',
        'KLAY',
        'AGLD',
        'METIS',
        'GLMR',
        'MOVR',
        'MATIC',
        'WMATIC'
        'BEAM',
        'INJ',
        'WETH',
        'WETH.e',
        'STG',
        'MAV',
        'ARB',
        'OP',
        'TIA',
        'TIA.n',
        'NTRN',
        'ZRO',
        'SOL',
        'ezETH',
        'wrsETH'
    ],
    'gate': [
        'CANTO',
        'FUSE',
        'MNT',
        'MTR',
        'OKT',
        'TLOS',
        'TENET',
        'XPLA',
        'CORE'
    ],
    'stables': [
        'xDAI',
        'DAI',
        'USDT',
        'USDC',
        'USDC.e',
        'BUSD',
        'USDbC',
        'fUSDC',
        'USDB'
    ]
}

OKX_NETWORKS_NAME = {
    1                       : 'ETH-ERC20',
    2                       : 'ETH-Arbitrum One',
    3                       : 'ETH-Optimism',
    4                       : 'ETH-zkSync Era',
    5                       : 'ETH-Linea',
    6                       : 'ETH-Base',
    7                       : 'AVAX-Avalanche C-Chain',
    8                       : 'BNB-BSC',
    # 9                     : 'BNB-OPBNB',
    10                      : 'CELO-CELO',
    11                      : 'GLMR-Moonbeam',
    12                      : 'MOVR-Moonriver',
    13                      : 'METIS-Metis',
    14                      : 'CORE-CORE',
    15                      : 'CFX-CFX_EVM',
    16                      : 'KLAY-Klaytn',
    17                      : 'FTM-Fantom',
    18                      : 'POL-Polygon',
    19                      : 'USDT-Arbitrum One',
    20                      : 'USDT-Avalanche C-Chain',
    21                      : 'USDT-Optimism',
    22                      : 'USDT-Polygon',
    23                      : 'USDT-BSC',
    24                      : 'USDT-ERC20',
    25                      : 'USDC-Arbitrum One',
    26                      : 'USDC-Avalanche C-Chain',
    27                      : 'USDC-Optimism',
    28                      : 'USDC-Polygon',
    29                      : 'USDC-Optimism (Bridged)',
    30                      : 'USDC-Polygon (Bridged)',
    31                      : 'USDC-BSC',
    32                      : 'USDC-ERC20',
    # 33                      : 'STG-Arbitrum One',
    # 34                      : 'STG-BSC',
    # 35                      : 'STG-Avalanche C-Chain',
    # 36                      : 'STG-Fantom',
    # 37                      : 'USDV-BSC',
    38                       : 'ARB-Arbitrum One',
    # 39                      : "MAV-BASE",
    # 40                      : "MAV-ZKSYNCERA",
    41                      : "OP-Optimism",
    42                      : "INJ-INJ",
    43                      : "TIA-Celestia",
    # 44                      : "NTRN-NTRN",
    47                      : "SOL-Solana",
    48                      : "OKB-X Layer",
}

BINANCE_NETWORKS_NAME = {
    1                       : "ETH-ETH",
    2                       : "ETH-ARBITRUM",
    3                       : "ETH-OPTIMISM",
    4                       : "ETH-ZKSYNCERA",
    # 5                     : "ETH-LINEA",
    6                       : "ETH-BASE",
    7                       : 'AVAX-AVAXC',
    8                       : 'BNB-BSC',
    9                       : 'BNB-OPBNB',
    10                      : 'CELO-CELO',
    11                      : 'GLMR-Moonbeam',
    12                      : 'MOVR-Moonriver',
    # 13                    : 'METIS-METIS',
    # 14                    : 'CORE-CORE',
    15                      : 'CFX-CFX',
    16                      : 'KLAY-KLAYTN',
    17                      : 'FTM-FANTOM',
    18                      : 'POL-MATIC',
    19                      : 'USDT-ARBITRUM',
    20                      : 'USDT-AVAXC',
    21                      : 'USDT-OPTIMISM',
    22                      : 'USDT-MATIC',
    23                      : 'USDT-BSC',
    24                      : 'USDT-ETH',
    25                      : 'USDC-ARBITRUM',
    26                      : 'USDC-AVAXC',
    27                      : 'USDC-OPTIMISM',
    28                      : 'USDC-MATIC',
    # 29                    : 'USDC-Optimism (Bridged)',
    # 30                    : 'USDC-Polygon (Bridged)',
    31                      : 'USDC-BSC',
    32                      : 'USDC-ETH',
    33                      : 'STG-ARBITRUM',
    34                      : 'STG-BSC',
    35                      : 'STG-AVAXC',
    36                      : 'STG-FTM',
    # 37                      : 'USDV-BSC',
    38                      : 'ARB-ARBITRUM',
    39                      : "MAV-BASE",
    40                      : "MAV-ZKSYNCERA",
    41                      : "OP-OPTIMISM",
    42                      : "INJ-INJ",
    43                      : "TIA-TIA",
    44                      : "NTRN-NTRN",
    45                      : "ETH-MANTA",
    46                      : "ETH-BSC",
    47                      : "SOL-SOL",
}


CEX_WRAPPED_ID = {
     1                          : "Ethereum",
     2                          : "Arbitrum",
     3                          : "Optimism",
     4                          : "zkSync",
     5                          : "Linea",
     6                          : "Base",
     7                          : "Avalanche",
     8                          : "BNB Chain",
     9                          : "OpBNB",
     10                         : "Celo",
     11                         : "Moonbeam",
     12                         : "Moonriver",
     13                         : "Metis",
     14                         : "CoreDAO",
     15                         : "Conflux",
     16                         : "Klaytn",
     17                         : "Fantom",
     18                         : "Polygon",
     19                         : "Arbitrum",
     20                         : "Avalanche",
     21                         : "Optimism",
     22                         : "Polygon",
     23                         : "BNB Chain",
     24                         : "Ethereum",
     25                         : "Arbitrum",
     26                         : "Avalanche",
     27                         : "Optimism",
     28                         : "Polygon",
     29                         : "Optimism",
     30                         : "Polygon",
     31                         : "BNB Chain",
     32                         : "Ethereum",
     33                         : "Arbitrum",
     34                         : "BNB Chain",
     35                         : "Avalanche",
     36                         : "Fantom",
     37                         : "BNB Chain",
     38                         : "Arbtirum",
     39                         : "Base",
     40                         : "zkSync",
     41                         : "Optimism",
     42                         : "Injective",
     43                         : "Celestia",
     44                         : "Neutron",
     45                         : "Manta",
     46                         : "BNB Chain",
     47                         : "Solana",
     48                         : "xLayer",
}



CHAIN_NAME_FROM_ID = {
    42161: 'Arbitrum',
    42170: 'Arbitrum Nova',
    8453: 'Base',
    59144: 'Linea',
    169: 'Manta',
    56: 'BNB Chain',
    137: 'Polygon',
    10: 'Optimism',
    534352: 'Scroll',
    1101: 'Polygon zkEVM',
    324: 'zkSync',
    7777777: 'Zora',
    1: 'Ethereum',
    43114: 'Avalanche'
}

CHAIN_IDS = {
    'Arbitrum':  42161,
    'Arbitrum Nova':  42170,
    'Base':  8453,
    'Linea':  59144,
    'Manta':  169,
    'BNB Chain':  56,
    'Polygon':  137,
    'Optimism':  10,
    'Scroll': 534352,
    'Polygon zkEVM': 1101,
    'zkSync': 324,
    'Zora': 7777777,
    'Ethereum': 1,
    'Avalanche': 43114
}

IMAP_CONFIG = {
    'outlook.com': 'outlook.office365.com',
    'hotmail.com': 'imap-mail.outlook.com',
}

GeneralSettings.prepare_general_settings()
ACCOUNTS_DATA = get_accounts_data()


TITLE = """
 █████╗ ███████╗████████╗██████╗ ██╗   ██╗███╗   ███╗ ██████╗██╗      █████╗ ██╗███╗   ███╗███████╗██████╗ 
██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██║   ██║████╗ ████║██╔════╝██║     ██╔══██╗██║████╗ ████║██╔════╝██╔══██╗
███████║███████╗   ██║   ██████╔╝██║   ██║██╔████╔██║██║     ██║     ███████║██║██╔████╔██║█████╗  ██████╔╝
██╔══██║╚════██║   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║██║     ██║     ██╔══██║██║██║╚██╔╝██║██╔══╝  ██╔══██╗
██║  ██║███████║   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║╚██████╗███████╗██║  ██║██║██║ ╚═╝ ██║███████╗██║  ██║
╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
"""
