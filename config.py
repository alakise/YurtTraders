from typing import Dict, Union

from web3 import Web3

default_user_config = {
    'phone_number': None,
    'mnemonic': None,
    'telegram': {
        'listen': 'https://t.me/group1*2x0.01*mcap=35000*any*alarm*multi'
                  'https://t.me/group2*1x0.05*honeypot*wallets=2*multi',
        'blacklist': 'welcome,hello,sitting,giveaway,presale,spots,verified,whitelist,winner',
        'whitelist': 'zero,0x,t.me,@',
    },
    'buy': {
        'audit': False,  # honeypot test
        'wallets': 2,  # how many wallets to buy
    },
    'gas': {
        'buy': 15,
        'sell': 7,
        'approve': 5,
        'all': 5
    },
    'active': 'BSC',
    'bot_token': '',
    'bscscan_api': 'YourApiToken',
    'etherscan_api': 'YourApiToken'
}


# -SETTINGS BELOW HERE IS AUTHORISED PERSONNEL ONLY- -DON'T CHANGE IT UNLESS YOU ARE SURE WHAT YOU ARE DOING-
class Config:
    apis = {

    
    }
    dex_addresses = {
        'BSC_router_ca': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
        'BSC_factory_ca': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
        'BSC_testnet_router_ca': '0xD99D1c33F9fC3444f8101754aBC46c52416550D1',
        'BSC_testnet_factory_ca': '0x6725F303b657a9451d8BA641348b6761A6CC7a17',
        'AVAX_router_ca': '0x60aE616a2155Ee3d9A68541Ba4544862310933d4',
        'AVAX_factory_ca': '0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10',
        'METIS_router_ca': '0x81b9FA50D5f5155Ee17817C21702C3AE4780AD09',
        'METIS_factory_ca': '0x2CdFB20205701FF01689461610C9F321D1d00F80',
        'CRONOS_router_ca': '0x145677FC4d9b8F19B5D56d1820c48e0443049a30',
        'CRONOS_factory_ca': '0xd590cC180601AEcD6eeADD9B7f2B7611519544f4',
        'MILKOMEDA_router_ca': '0x9D2E30C2FB648BeE307EDBaFDb461b09DF79516C',
        'MILKOMEDA_factory_ca': '0xD6Ab33Ad975b39A8cc981bBc4Aaf61F957A5aD29',
        'DOGECHAIN_router_ca': '0xa4EE06Ce40cb7e8c04E127c1F7D3dFB7F7039C81',
        'DOGECHAIN_factory_ca': '0xD27D9d61590874Bf9ee2a19b27E265399929C9C3',
        'ETC_router_ca': '0xEcBcF5C7aF4c323947CFE982940BA7c9fd207e2b',
        'ETC_factory_ca': '0x09fafa5eecbc11C3e5d30369e51B7D9aab2f3F53',
        'ETH_router_ca': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'ETH_factory_ca': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
        'ETH_goerli_router_ca': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'ETH_goerli_factory_ca': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',

    }
    # Wrapped token addresses
    WAVAX = '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7'
    WBNB = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
    WBNB_testnet = '0xae13d989dac2f0debff460ac112a837c89baa7cd'
    WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
    WETH_goerli = '0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6'
    WCELO = '0x471EcE3750Da237f93B8E339c536989b8978a438'
    WMETIS = '0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000'
    BLACKHOLE = '0x0000000000000000000000000000000000000000'
    DEAD = '0x000000000000000000000000000000000000dEaD'
    WCRO = '0x5C7F8A570d578ED84E63fdFA7b1eE72dEae1AE23'
    WADA = '0xAE83571000aF4499798d1e3b0fA0070EB3A3E3F9'
    WDOGE = '0xB7ddC6414bf4F5515b52D8BdD69973Ae205ff101'
    WETC = '0x82A618305706B14e7bcf2592D4B9324A366b6dAd'

    provider_addresses = {
        'BSC_testnet': 'https://data-seed-prebsc-1-s1.binance.org:8545/',
        'BSC': 'https://bsc-dataseed2.binance.org',
        'AVAX': 'https://api.avax.network/ext/bc/C/rpc',
        'ETH': 'https://mainnet.infura.io/v3/21e89a8be898460398da1ccdf240653b',
        'ETH_goerli': 'https://goerli.infura.io/v3/21e89a8be898460398da1ccdf240653b',
        'METIS': 'https://andromeda.metis.io/?owner=1088',
        'CRONOS': 'https://mmf-rpc.xstaking.sg/',
        'MILKOMEDA': 'https://rpc-mainnet-cardano-evm.c1.milkomeda.com',
        'DOGECHAIN': 'https://rpc02-sg.dogechain.dog',
        'ETC': 'https://www.ethercluster.com/etc'
    }

    version = "a New Hope"
    buy_enabled = True

    chain_id: dict = {
        'BSC': 56,
        'BSC_testnet': 97,
        'AVAX_testnet': 43113,
        'AVAX': 43114,
        'METIS': 1088,
        'CRONOS': 25,
        'MILKOMEDA': 2001,
        'DOGECHAIN': 2000,
        'ETH': 1,
        'ETH_goerli': 5
    }
