# system imports
import asyncio
import json
import threading
import time

# library imports
import requests
from eth_typing import ChecksumAddress
from flask_socketio import emit
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput, ContractLogicError
from web3.types import Wei

# project imports
from config import Config
from user import User
from wallet import Wallet

def fire_and_forget(coro):
    """
    Run an asynchronous function in a new event loop on a separate thread.
    """
    _loop = asyncio.new_event_loop()
    threading.Thread(target=_loop.run_forever, daemon=True).start()
    _loop.call_soon_threadsafe(asyncio.create_task, coro)

class BSCBlockchain:
    """
    A class to interact with the Binance Smart Chain (BSC) and other EVM-compatible blockchains.
    """

    # Application binary interfaces (ABIs)
    token_abi: dict = json.load(open('./data/token_abi.json'))
    pair_abi: dict = json.load(open('./data/pair_abi.json'))
    uni_router_abi: dict = json.load(open('./data/uni_router.json'))
    uni_factory_abi: dict = json.load(open('./data/uni_factory.json'))
    TJ_router_abi: dict = json.load(open('data/TJ_router.json'))
    TJ_factory_abi: dict = json.load(open('data/TJ_factory.json'))
    doge_router_abi: dict = json.load(open('data/doge_router.json'))
    doge_factory_abi: dict = json.load(open('data/doge_factory.json'))
    etc_router_abi: dict = json.load(open('data/etc_router.json'))
    etc_factory_abi: dict = json.load(open('data/etc_factory.json'))

    def __init__(self, user: User):
        self.user = user
        self.network = self._network()
        self.web3 = self.web3_provider()
        self.router = self._router()
        self.factory = self._factory()
        self.router_address = self._router_address()
        self.symbol_price()
        self.wallets: list = []
        self.update_wallets()

    def user_data(self) -> dict:
        """
        Retrieve user data from the configuration.
        """
        return self.user.config

    def web3_provider(self) -> Web3:
        """
        Initialize and return a Web3 provider.
        """
        if self.user.exists(self.network + '_rpc'):
            return Web3(Web3.HTTPProvider(self.user.config[self.network + '_rpc']))
        else:
            return Web3(Web3.HTTPProvider(Config.provider_addresses[self.network]))

    def _network(self) -> str:
        """
        Determine the active network from the user's configuration.
        """
        print("Current Network: ", self.user.config['active'])
        return self.user.config['active']

    def _router(self) -> Contract:
        """
        Initialize and return the router contract based on the active network.
        """
        if self.network in ['BSC', 'CRONOS', 'MILKOMEDA', 'BSC_testnet', 'METIS', 'ETH', 'ETH_goerli']:
            return self.web3.eth.contract(self._router_address(), abi=self.uni_router_abi)
        if self.network == 'AVAX':
            return self.web3.eth.contract(address=self._router_address(), abi=self.TJ_router_abi)
        if self.network == 'DOGECHAIN':
            return self.web3.eth.contract(self._router_address(), abi=self.doge_router_abi)
        if self.network == 'ETC':
            return self.web3.eth.contract(self._router_address(), abi=self.etc_router_abi)

    def _router_address(self) -> ChecksumAddress:
        """
        Get the checksum address of the router.
        """
        return Web3.to_checksum_address(Config.dex_addresses[self.network + '_router_ca'])

    def _factory_address(self) -> ChecksumAddress:
        """
        Get the checksum address of the factory.
        """
        return Web3.to_checksum_address(Config.dex_addresses[self.network + '_factory_ca'])

    def _factory(self) -> Contract:
        """
        Initialize and return the factory contract based on the active network.
        """
        if self.network in ['BSC', 'CRONOS', 'MILKOMEDA', 'BSC_testnet', 'METIS', 'ETH', 'ETH_goerli']:
            return self.web3.eth.contract(self._factory_address(), abi=self.uni_factory_abi)
        if self.network == 'AVAX':
            return self.web3.eth.contract(address=self._factory_address(), abi=self.TJ_factory_abi)
        if self.network == 'DOGECHAIN':
            return self.web3.eth.contract(self._factory_address(), abi=self.doge_factory_abi)
        if self.network == 'ETC':
            return self.web3.eth.contract(self._factory_address(), abi=self.etc_factory_abi)

    def blockchain_info(self):
        """
        Return a dictionary containing blockchain information.
        """
        network = self.network
        factory = str(self._factory_address())
        if network == 'AVAX':
            return {
                'network': 'AVAX',
                'symbol': 'AVAX',
                'price': self.coin_price,
                'scanner': 'https://snowtrace.io/',
                'scanner_name': 'SnowTrace',
                'RPC': 'https://api.avax.network/ext/bc/C/rpc',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WAVAX
            }
        if network == 'METIS':
            return {
                'network': 'METIS',
                'symbol': 'METIS',
                'price': self.coin_price,
                'scanner': 'https://andromeda-explorer.metis.io/',
                'scanner_name': 'Andromeda Explorer',
                'RPC': 'https://andromeda.metis.io/?owner=1088',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WMETIS
            }
        if network == 'BSC_testnet':
            return {
                'network': 'BSC (testnet)',
                'symbol': 'BNB (test)',
                'price': self.coin_price,
                'scanner': 'https://testnet.bscscan.com/',
                'scanner_name': 'BSCScan',
                'RPC': 'https://data-seed-prebsc-1-s1.binance.org:8545/',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WBNB_testnet
            }
        if network == 'MILKOMEDA':
            return {
                'network': 'Milkomeda Cardano (C1)',
                'symbol': 'MilkADA',
                'price': self.coin_price,
                'scanner': 'https://explorer-mainnet-cardano-evm.c1.milkomeda.com/',
                'scanner_name': 'Milkomeda Explorer',
                'RPC': 'https://rpc-mainnet-cardano-evm.c1.milkomeda.com',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WADA
            }
        if network == 'DOGECHAIN':
            return {
                'network': 'Dogechain',
                'symbol': 'wDOGE',
                'price': self.coin_price,
                'scanner': 'https://explorer.dogechain.dog/',
                'scanner_name': 'Dogechain',
                'RPC': 'https://rpc02-sg.dogechain.dog',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WDOGE
            }
        if network == 'ETC':
            return {
                'network': 'Ethereum Classic',
                'symbol': 'ETC',
                'price': self.coin_price,
                'scanner': 'https://blockscout.com/etc/mainnet/',
                'scanner_name': 'Blockscout ETC',
                'RPC': 'https://www.ethercluster.com/etc',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WETC
            }
        if network == 'ETH':
            return {
                'network': 'Ethereum',
                'symbol': 'ETH',
                'price': self.coin_price,
                'scanner': 'https://etherscan.io/',
                'scanner_name': 'Etherscan',
                'RPC': 'https://mainnet.infura.io/v3/21e89a8be898460398da1ccdf240653b',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WETH
            }
        if network == 'ETH_goerli':
            return {
                'network': 'Ethereum Goerli',
                'symbol': 'GörliETH',
                'price': self.coin_price,
                'scanner': 'https://goerli.etherscan.io/',
                'scanner_name': 'Etherscan (Görli)',
                'RPC': 'https://goerli.infura.io/v3/21e89a8be898460398da1ccdf240653b',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WETH_goerli
            }
        if network == 'CRONOS':
            return {
                'network': 'CRONOS',
                'symbol': 'CRO',
                'price': self.coin_price,
                'scanner': 'https://cronoscan.com/',
                'scanner_name': 'Cronoscan',
                'RPC': 'https://mmf-rpc.xstaking.sg/',
                'router': self.router_address,
                'factory': factory,
                'token': Config.WBNB_testnet
            }
        return {
            'network': 'BSC',
            'symbol': 'BNB',
            'price': self.coin_price,
            'scanner': 'https://bscscan.com/',
            'scanner_name': 'BSCScan',
            'RPC': 'https://bsc-dataseed.binance.org/',
            'router': self.router_address,
            'factory': factory,
            'token': Config.WBNB
        }

    def update_wallets(self):
        """
        Update the list of wallets from the user's configuration.
        """
        self.wallets = []
        for i in range(int(self.user.config['buy']['wallets'])):
            self.wallets.append(Wallet(self.web3, self.user.config['wallets'][i][0], self.user.config['wallets'][i][1]))

    def get_decimals(self, token_ca: str) -> int:
        """
        Get the number of decimals for a token contract.
        """
        token = self.web3.eth.contract(address=self.web3.to_checksum_address(token_ca), abi=self.token_abi)
        decimals = token.functions.decimals().call()
        return decimals

    def get_symbol(self, token_ca: str) -> str:
        """
        Get the symbol of a token contract.
        """
        token = self.web3.eth.contract(address=self.web3.to_checksum_address(token_ca), abi=self.token_abi)
        symbol = token.functions.symbol().call()
        return symbol

    def get_name(self, token_ca: str) -> str:
        """
        Get the name of a token contract.
        """
        token = self.web3.eth.contract(address=self.web3.to_checksum_address(token_ca), abi=self.token_abi)
        name = token.functions.name().call()
        return name

    def check_allowance(self, wallet: Wallet, token_ca: str) -> bool:
        """
        Check if the router is allowed to spend tokens from the wallet.
        """
        token = self.web3.eth.contract(address=Web3.to_checksum_address(token_ca), abi=self.token_abi)
        allowance = token.functions.allowance(wallet.address, self.router_address).call()
        return bool(allowance)

    async def approve(self, wallet: Wallet, token_ca: str, check_balance=False):
        """
        Approve the router to spend tokens from the wallet.
        """
        token = self.web3.eth.contract(address=self.web3.to_checksum_address(token_ca), abi=self.token_abi)
        if token.functions.allowance(wallet.address, self.router_address).call():
            emit('approve_response', {
                'data': 'Token is already approved',
                'success': False
            })
            return False

        if check_balance:
            balance = token.functions.balanceOf(wallet.address).call()
            if balance <= 0:
                emit('approve_response', {
                    'data': f"Balance check active. No balance found for wallet: {wallet.address}",
                    'success': False
                })
                return False

        max_amount = self.web3.toWei(2 ** 64 - 1, 'ether')
        if 'ETH' in self.network:
            max_amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935

        tx = token.functions.approve(self.router_address, max_amount).buildTransaction({
            'from': wallet.address,
            'nonce': wallet.refresh_nonce(),
            'gasPrice': self.gas_price('approve'),
            'gas': 100000,
            'chainId': Config.chain_id[self.network]
        })
        try:
            signed_tx = self.web3.eth.account.signTransaction(tx, wallet.privateKey)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            wallet.nonce += 1
            emit('approve_response', {
                'tx': str(Web3.toHex(tx_hash)),
                'wallet': wallet.address,
                'success': True
            })
            return self.tx_link(Web3.toHex(tx_hash))
        except ValueError as err:
            if 'nonce' in err.args[0]['message'] or 'replacement' in err.args[0]['message']:
                emit('approve_response', {
                    'data': f"Nonce error. Trying to repeat approve: {wallet.address}",
                    'success': False
                })

    async def buy(self, wallet: Wallet, buy_amount: float, token_contract: str, nonce: int = None):
        """
        Execute a buy order for a specified token contract.
        """
        token_contract = Web3.to_checksum_address(token_contract)
        router = self.router

        if nonce is None:
            nonce = wallet.nonce

        # Build transaction input
        if self.network == 'AVAX':
            tx = router.functions.swapExactAVAXForTokens(
                0,
                [self.coin(), token_contract],
                wallet.address,
                (int(time.time()) + 60)
            )
        elif self.network == 'DOGECHAIN':
            tx = router.functions.swapExactWDOGEForTokens(
                0,
                [self.coin(), token_contract],
                wallet.address,
                (int(time.time()) + 60)
            )
        elif self.network == 'ETC':
            tx = router.functions.swapExactETCForTokens(
                0,
                [self.coin(), token_contract],
                wallet.address,
                (int(time.time()) + 60)
            )
        else:
            tx = router.functions.swapExactETHForTokens(
                0,
                [self.coin(), token_contract],
                wallet.address,
                (int(time.time()) + 60)
            )

        gas = 1000000 if self.network == 'CRONOS' else 1600000
        tx_input = {
            'from': wallet.address,
            'value': Web3.toWei(buy_amount, 'ether'),
            'gasPrice': self.gas_price('buy'),
            'gas': gas,
            'nonce': nonce,
            'chainId': Config.chain_id[self.network],
        }

        tx = tx.buildTransaction(tx_input)
        if not Config.buy_enabled:
            emit('buy_response', {
                'tx': '0x162469063ab5c534fe1ae26513394d7ba7a495f3e69da5077452dcf4c6768793',
                'amount': buy_amount,
                'wallet': wallet.address,
                'success': True
            })
            return False
        try:
            signed_txn = self.web3.eth.account.sign_transaction(tx, private_key=wallet.privateKey)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            wallet.nonce += 1
            emit('buy_response', {
                'tx': str(Web3.toHex(tx_hash)),
                'amount': buy_amount,
                'wallet': wallet.address,
                'success': True
            })
        except ValueError as err:
            if 'gas too low' in err.args[0]['message']:
                emit('buy_response', {
                    'data': f"<br>Buy failed: Transaction rejected, gas too low.<br>Node response:<br>{err.args[0]['message']}",
                    'success': False
                })
            elif 'funds' in err.args[0]['message']:
                emit('buy_response', {
                    'data': f"<br>Buy failed: insufficient funds. Wallet:<br>{wallet.address}",
                    'success': False
                })
            else:
                emit('buy_response', {
                    'data': f"Unknown error on buy. Node response:<br>{err.args[0]['message']}",
                    'success': False
                })

    async def calculate_sell_gas(self, token_contract):
        """
        Calculate the gas required for a sell order and emit the result.
        """
        text_output = ''
        deadline = int(time.time()) + 60
        token = self.web3.eth.contract(Web3.to_checksum_address(token_contract), abi=self.token_abi)
        totalSupply = int(token.functions.totalSupply().call() / 100)

        router = self.router
        tx_input = {
            'from': self.wallets[0].address,
            'nonce': self.wallets[0].refresh_nonce(),
            'gasPrice': self.gas_price('sell'),
        }

        if self.network == 'AVAX':
            tx = router.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                totalSupply, 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                self.wallets[0].address, deadline)
        elif self.network == 'DOGECHAIN':
            tx = router.functions.swapExactTokensForWDOGESupportingFeeOnTransferTokens(
                totalSupply, 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                self.wallets[0].address, deadline)
        elif self.network == 'ETC':
            tx = router.functions.swapExactTokensForETCSupportingFeeOnTransferTokens(
                totalSupply, 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                self.wallets[0].address, deadline)
        else:
            tx = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                totalSupply, 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                self.wallets[0].address, deadline)

        print(tx)
        # Estimate gas fee
        try:
            tx_input['gas'] = int(self.web3.eth.estimate_gas(tx.buildTransaction(tx_input)) * 2)
            emit('sell_gas_response', {'data': tx_input['gas'], 'success': False})
        except ValueError as err:
            if 'gas too low' in err.args:
                text_output += f"<br>Sell failed: Transaction rejected, gas too low.<br>Node response:<br>{str(err)}"
            if 'insufficient' in err.args:
                text_output += f"<br>Sell failed: insufficient funds. Wallet:<br>{self.wallets[0].address}"
            else:
                text_output += f"Unknown error. Node response:<br>{str(err)}"
            emit('sell_gas_response', {'data': text_output, 'success': False})

    async def sell(self, wallet: Wallet, token_contract: str):
        """
        Execute a sell order for a specified token contract.
        """
        text_output = ''
        deadline = int(time.time()) + 60
        token = self.web3.eth.contract(Web3.to_checksum_address(token_contract), abi=self.token_abi)
        balance = token.functions.balanceOf(wallet.address).call()
        if balance <= 0:
            emit('sell_response', {
                'data': f"There is no balance in the wallet. Wallet:<br>{wallet.address}",
                'wallet': wallet.address,
                'success': False
            })
            return

        router = self.router
        tx_input = {
            'from': wallet.address,
            'nonce': wallet.refresh_nonce(),
            'gasPrice': self.gas_price('sell'),
            'chainId': Config.chain_id[self.network]
        }

        if self.network == 'AVAX':
            tx = router.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                int(balance), 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                wallet.address, deadline)
        elif self.network == 'DOGECHAIN':
            tx = router.functions.swapExactTokensForWDOGESupportingFeeOnTransferTokens(
                int(balance), 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                wallet.address, deadline)
        elif self.network == 'ETC':
            tx = router.functions.swapExactTokensForETCSupportingFeeOnTransferTokens(
                int(balance), 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                wallet.address, deadline)
        else:
            tx = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                int(balance), 1,
                [Web3.to_checksum_address(token_contract), self.coin()],
                wallet.address, deadline)

        print(tx)
        # Estimate gas fee
        try:
            tx_input['gas'] = int(self.web3.eth.estimate_gas(tx.buildTransaction(tx_input)) * 3.5)
        except ValueError as err:
            if 'gas too low' in err.args:
                text_output += f"<br>Buy failed: Transaction rejected, gas too low.<br>Node response:<br>{err.args}"
            if 'insufficient' in err.args:
                text_output += f"<br>Buy failed: insufficient funds. Wallet:<br>{wallet.address}"
            else:
                text_output += f"Unknown error. Node response:<br>{err.args}"
            emit('sell_response', {'data': text_output, 'success': False})
            return
        if tx_input['gas'] > 10000000:
            text_output += f"Sell failed: Absurd gas fee calculated. Probably because the token is a scam. Calculated gas: {tx_input['gas']} \n"
            emit('sell_response', {'data': text_output, 'success': False})
            return
        tx = tx.buildTransaction(tx_input)
        try:
            signed_tx = self.web3.eth.account.sign_transaction(tx, wallet.privateKey)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            wallet.nonce += 1
            emit('sell_response', {
                'data': 'Token sell completed',
                'tx': str(Web3.toHex(tx_hash)),
                'wallet': wallet.address,
                'success': True
            })
        except ValueError as err:
            if 'gas too low' in err.args[0]['message']:
                text_output += f"<br>Buy failed: Transaction rejected, gas too low.<br>Node response:<br>{err.args[0]['message']}"
            else:
                text_output += f"Unknown error. Node response:<br>{err.args[0]['message']}"
            emit('sell_response', {'data': text_output, 'success': False})

    def gas_price(self, fx='all') -> Wei:
        """
        Get the gas price for a specific function type.
        """
        user_data = self.user_data()
        if fx in user_data['gas'] and user_data['gas'][fx] is not None and self.web3.eth.gas_price < Web3.toWei(user_data['gas'][fx], 'gwei'):
            return Web3.toWei(user_data['gas'][fx], 'gwei')
        else:
            if fx in ['buy', 'sell'] and 'ETH' in self.network:
                print("Gas automatically set to priority to make buy possible")
                return Web3.toWei(self.web3.eth.gas_price * 1.1, 'wei')
            else:
                return self.web3.eth.gas_price

    def get_token_from_lp(self, lp_address):
        """
        Get the token address from a liquidity pool address.
        """
        try:
            pair = self.web3.eth.contract(Web3.to_checksum_address(lp_address), abi=self.pair_abi)
            pair_0 = pair.functions.token0().call()
            if pair_0 == self.coin():
                return pair.functions.token1().call()
            else:
                return pair_0
        except (ValueError, BadFunctionCallOutput):
            return False

    def get_mcap(self, token_contract: ChecksumAddress):
        """
        Calculate the market capitalization of a token.
        """
        factory = self.factory
        token = self.web3.eth.contract(Web3.to_checksum_address(token_contract), abi=self.token_abi)
        try:
            balance_loop = token.functions.balanceOf(Config.DEAD).call()
            token_supply = token.functions.totalSupply().call()
            print(self.coin(), token_contract)
            lp_address = factory.functions.getPair(self.coin(), token_contract).call()
        except (ContractLogicError, BadFunctionCallOutput):
            return f'Found address is not a contract: {str(token_contract)}'
        if lp_address == Config.BLACKHOLE:
            return "LP not found for token-BNB pair."
        pair = self.web3.eth.contract(Web3.to_checksum_address(lp_address), abi=self.pair_abi)
        pair_size = pair.functions.getReserves().call()
        try:
            print("TOKEN 0", pair.functions.token0().call(), str(token_contract), pair.functions.token0().call() == str(token_contract))
            if pair.functions.token0().call() == str(token_contract):
                price_as_bnb = Web3.from_wei(pair_size[1], 'ether') / pair_size[0]
                pair_size = Web3.from_wei(pair_size[1], 'ether')
            else:
                price_as_bnb = Web3.from_wei(pair_size[0], 'ether') / pair_size[1]
                pair_size = Web3.from_wei(pair_size[0], 'ether')
                print(price_as_bnb, token_supply, balance_loop)
        except ZeroDivisionError:
            price_as_bnb = 1
        mcap = float(price_as_bnb * (token_supply - balance_loop)) * self.coin_price
        if isinstance(pair_size, list):
            return "No LP found for pair"
        if pair_size < 0.9:
            return "LP is lower than 0.9 BNB. Huge loss expected, not proceeding to buy."
        return {'market_cap': mcap, 'LP_size': pair_size, 'coin_price': mcap / (token_supply - balance_loop)}

    def coin(self) -> ChecksumAddress:
        """
        Get the wrapped coin address for the active network.
        """
        network_coin_map = {
            'BSC_testnet': Config.WBNB_testnet,
            'AVAX': Config.WAVAX,
            'METIS': Config.WMETIS,
            'CRONOS': Config.WCRO,
            'MILKOMEDA': Config.WADA,
            'DOGECHAIN': Config.WDOGE,
            'ETC': Config.WETC,
            'ETH': Config.WETH,
            'ETH_goerli': Config.WETH_goerli
        }
        return Web3.to_checksum_address(network_coin_map.get(self.network, Config.WBNB))

    def tx_link(self, tx_hash: str) -> str:
        """
        Generate a transaction link for the specified transaction hash.
        """
        network_link_map = {
            'BSC_testnet': 'https://testnet.bscscan.com/tx/',
            'AVAX': 'https://snowtrace.io/tx/',
            'CRONOS': 'https://cronoscan.com/tx/',
            'MILKOMEDA': 'https://explorer-mainnet-cardano-evm.c1.milkomeda.com/tx/',
            'DOGECHAIN': 'https://explorer.dogechain.dog/',
            'ETC': 'https://blockscout.com/etc/mainnet/tx/',
            'ETH': 'https://etherscan.io/tx/',
            'ETH_goerli': 'https://goerli.etherscan.io/tx/',
        }
        base_url = network_link_map.get(self.network, 'https://bscscan.com/tx/')
        return base_url + tx_hash

    async def transfer_bnb(self, from_wallet: Wallet, to_wallet, amount: float):
        """
        Transfer BNB from one wallet to another.
        
        Args:
            from_wallet (Wallet): The wallet to transfer BNB from.
            to_wallet (Union[Wallet, str]): The wallet or address to transfer BNB to.
            amount (float): The amount of BNB to transfer.
        
        Returns:
            str: The transaction link if the transfer is successful.
        """
        receiver = to_wallet.address if isinstance(to_wallet, Wallet) else to_wallet
        if amount > 0.0001:
            tx = {
                'nonce': from_wallet.nonce,
                'from': from_wallet.address,
                'to': receiver,
                'value': Web3.toWei(amount, 'ether'),
                'gasPrice': self.gas_price('transfer'),
                'gas': 21000,
                'chainId': Config.chain_id[self.network]
            }
            print("Transfer value: " + str(Web3.toWei(amount, 'ether')) + ' Gas: ' + str(self.gas_price('transfer')),
                  '\nTotal: ' + str(int(Web3.toWei(amount, 'ether')) + int(self.gas_price('transfer'))))
            signed_tx = self.web3.eth.account.signTransaction(tx, from_wallet.privateKey)
            try:
                tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
                from_wallet.nonce += 1
                emit('transfer_response', {
                    'tx': str(Web3.toHex(tx_hash)),
                    'success': True,
                    'from': from_wallet.address,
                    'to': receiver
                })
                return self.tx_link(Web3.toHex(tx_hash))
            except ValueError as err:
                emit('transfer_response', {
                    'data': str(err),
                    'success': False,
                    'from': from_wallet.address,
                    'to': receiver
                })
        else:
            emit('transfer_response', {
                'data': 'Amount is so low: ' + from_wallet.address,
                'success': False
            })

    async def distribute_balance(self, amount: float):
        """
        Distribute a specified amount of BNB to all wallets.

        Args:
            amount (float): The amount of BNB to distribute.
        """
        for wallet in self.wallets:
            if wallet.address != self.wallets[0].address:
                asyncio.ensure_future(self.transfer_bnb(self.wallets[0], wallet, amount))

    async def collect_to_main_wallet(self):
        """
        Collect BNB from all wallets to the main wallet.
        """
        for wallet in self.wallets:
            if wallet.address != self.wallets[0].address:
                amount = wallet.refresh_balance() - Web3.from_wei(21000 * self.gas_price('transfer'), 'ether')
                print(amount)
                if amount >= Web3.from_wei(21000 * self.gas_price('transfer'), 'ether'):
                    await self.transfer_bnb(wallet, self.wallets[0], amount)

    def symbol_price(self) -> float:
        """
        Retrieve and set the price of the network's native coin.

        Returns:
            float: The price of the network's native coin.
        """
        price_endpoints = {
            'BSC': ('0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16', lambda r: r[1] / r[0]),
            'CRONOS': ('0xa68466208F1A3Eb21650320D2520ee8eBA5ba623', lambda r: r[1] / r[0] * 10 ** 12),
            'MILKOMEDA': ('0xB56964a0617b2b760C8B6D8040e99cda29D5203b', lambda r: r[1] / r[0] * 10 ** 12),
            'DOGECHAIN': ('https://sochain.com//api/v2/get_price/DOGE/USD', lambda r: float(r['data']['prices'][1]['price'])),
            'ETC': ('https://blockscout.com/etc/mainnet/api?module=stats&action=coinprice', lambda r: float(r['result']['coin_usd'])),
            'ETH': ('https://api.etherscan.io/api?module=stats&action=ethprice&apikey=HMZ1XAGM1HY26X8TS5QS6KNRBFZ3Q3R66U', lambda r: float(r['result']['ethusd'])),
            'ETH_goerli': ('https://api.etherscan.io/api?module=stats&action=ethprice&apikey=HMZ1XAGM1HY26X8TS5QS6KNRBFZ3Q3R66U', lambda r: float(r['result']['ethusd'])),
            'BSC_testnet': ('0x85EcDcdd01EbE0BfD0Aba74B81Ca6d7F4A53582b', lambda r: r[0] / r[1]),
            'METIS': ('0xDd7dF3522a49e6e1127bf1A1d3bAEa3bc100583B', lambda r: r[1] / r[0] * 10 ** 12),
            'default': ('0xeD8CBD9F0cE3C6986b22002F03c6475CEb7a6256', lambda r: r[1] / r[0] * 10 ** 12)
        }

        endpoint, price_calc = price_endpoints.get(self.network, price_endpoints['default'])
        if self.network in ['DOGECHAIN', 'ETC', 'ETH', 'ETH_goerli']:
            resp = requests.get(url=endpoint)
            data = resp.json()
            coin_price = price_calc(data)
        else:
            pair = self.web3.eth.contract(Web3.to_checksum_address(endpoint), abi=self.pair_abi)
            reserves = pair.functions.getReserves().call()
            coin_price = price_calc(reserves)

        self.coin_price = coin_price
        return coin_price
