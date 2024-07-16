import requests
from web3 import Web3


class Wallet:

    balance: int
    nonce: int


    def __init__(self, web3: Web3, address: str, private_key: str):
        self.web3 = web3
        self.privateKey = private_key
        self.address = address
        self.refresh_nonce()
        self.refresh_balance()

    def refresh_nonce(self) -> int:
        try:
            self.nonce = self.web3.eth.get_transaction_count(self.address)
        except requests.exceptions.ConnectionError:
            pass
        return self.nonce

    def refresh_balance(self) -> float:
        try:
            self.balance = self.web3.from_wei(self.web3.eth.get_balance(self.address), 'ether')
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.HTTPError as e:
            print(e)
            pass
        return self.balance
