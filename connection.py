import asyncio
import threading

from flask_socketio import emit

from config import Config
from telegram_bot import TelegramBot, fire_and_forget
from bsc_blockchain import BSCBlockchain
from user import User


class Connection:
    user = None
    blockchain: BSCBlockchain = None
    telegram = None


    def __init__(self, app):
        self.tg_loop = asyncio.new_event_loop()
        self.app = app

    @staticmethod
    def response(response: str, content: dict = None, success: bool = True) -> bool:
        content['success'] = success
        emit(response + '_response', content)
        return success

    def login(self, message):

        if self.user is None:
            user = User(message['phone_number'], message['password'])
            if user.config is False:
                self.response('login', {'error': 'Password is incorrect.'}, False)
            else:
                mnemonic = user.config['mnemonic']
                mnemonic = True if mnemonic is not None else None
                self.response('login',
                              {'phone_number': user.config['phone_number'], 'mnemonic': mnemonic, 'success': True})
                self.user = user
                self.check_login()
                if mnemonic:
                    self.init_modules()
        else:
            self.response('login',
                          {'data': 'already', 'success': True})
            self.check_login()

    def check_login(self) -> bool:
        if self.user is not None:
            data: dict = self.user.config
            self.response('user_info',
                          {'data': data})
            if self.telegram is not None:
                self.telegram_connect()
            return True
        else:
            self.response('user_info',
                          {'error': 'Login first'}, False)
        return False

    def set_mnemonic(self, message):
        if type(message['mnemonic']) == str and len(message['mnemonic'].split(' ')) == 12:
            self.user.config['mnemonic'] = message['mnemonic']
            self.user.save()
            self.user.config['mnemonic'] = message['mnemonic']
            self.user.generate_wallets()
            self.init_modules()
            self.refresh_wallet()
        else:
            self.response('mnemonic',
                          {
                              'error': 'Mnemonics must consist of 12 words.'}, success=False)

    def telegram_connect(self):
        if self.tg_loop is None:
            self.tg_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.tg_loop)
        if self.telegram is not None:
            self.telegram.client.disconnect()
            self.telegram.client = None
            self.telegram = None

        # Telegram requires blockchain and bot connection
        if self.blockchain is not None and self.telegram is None:
            self.telegram = TelegramBot(self.user, self.blockchain, self.tg_loop, self)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                loop = None
                asyncio.run(self.telegram.listen())
            if loop and loop.is_running():
                print('Async event loop already running. Adding coroutine to the event loop.')
                loop.create_task(self.telegram.listen())

        elif self.blockchain is not None and self.telegram is not None:
            self.telegram.blockchain = self.blockchain
            asyncio.run(self.telegram.listen())
        else:
            emit('telegram_connect_response',
                 {'success': False,
                  'data': 'First <b>connect to blockchain</b> and/or <b>add bot token</b> to start telegram connection. '
                          'Telegram connection has not established'})

    # Initializes modules if not already initializes:
    # blockchain, telegram connection (inside of blockchain), and user info from database
    def init_modules(self):
        if 'mnemonic' in self.user.config and self.user.config['mnemonic'] != 'empty':
            if self.blockchain is None:
                self.blockchain = BSCBlockchain(self.user)
            # wallets = []
            # for wallet in self.blockchain.wallets:
            #     wallets.append({
            #         'address': wallet.address,
            #         'balance': str(wallet.balance),
            #         'nonce': wallet.nonce
            #     })
            # self.response('wallet',
            #      {'wallets': wallets, 'blockchain': self.blockchain.blockchain_info()})
        else:
            pass
            # self.response('wallet',
            #               {'error': 'Mnemonic is not set.'}, False)

    def refresh_wallet(self):
        print("Refreshing wallets using mnemonic:", self.user.config['mnemonic'])
        if self.user and 'mnemonic' in self.user.config and self.user.config['mnemonic'] != 'empty':
            if self.blockchain is None:
                self.blockchain = BSCBlockchain(self.user)
            wallets = []
            for wallet in self.blockchain.wallets:
                wallet.refresh_nonce()
                wallet.refresh_balance()
                wallets.append({
                    'address': wallet.address,
                    'balance': str(wallet.balance),
                    'nonce': wallet.nonce
                })
            self.blockchain.symbol_price()
            self.response('wallet',
                          {'wallets': wallets, 'blockchain': self.blockchain.blockchain_info()})

        else:
            self.response('wallet',
                          {'error': 'Mnemonic is not set.'}, False)

    def log_out(self):
        self.user = None
        self.blockchain = None
        if self.telegram is not None:
            self.telegram.client.disconnect()
            self.telegram.client = None
            self.telegram = None
        if self.tg_loop is not None:
            self.tg_loop.close()
            self.tg_loop = None

    def disconnect_telegram(self):
        if self.tg_loop is None:
            self.tg_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.tg_loop)
        if self.telegram is not None:
            self.telegram.client.disconnect()
            self.telegram.client = None
            self.telegram = None
        self.tg_loop.close()
        self.tg_loop = None
