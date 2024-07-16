import json
import os

from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from hdwallet.derivations import BIP44Derivation

from cipher import Cipher
from config import default_user_config


class User:
    _password: str = None
    _cipher: Cipher = None
    phone_number = None

    def __init__(self, phone_number: str, password: str):
        self.config = None
        self._cipher = Cipher(password)
        self._password = password
        self.phone_number = phone_number
        if os.path.isfile(f'users/{phone_number}.json'):
            self.config = self._load_encrypted(f'users/{phone_number}.json') # returns False if password is wrong
        else:
            open(f'users/{phone_number}.json', 'x').close()
            config = default_user_config
            config['phone_number'] = phone_number
            config['mnemonic'] = 'empty'
            self.config = config
            self.save()

    def _load_encrypted(self, file: str):
        f = open(file, "r")
        content = json.loads(f.read())
        content['mnemonic'] = self._cipher.decrypt(content['mnemonic'].encode("utf-8"))
        if content['mnemonic'] is not False:
            print("User info read from encrypted file: " + content['phone_number'])
        else:
            print("User password incorrect.")
            return False
        f.close()
        return content

    def save(self):
        print('User config changed, new settings saved.')
        # save settings
        f = open(f'users/{self.phone_number}.json', "w")
        config = self.config
        mnemonic = config['mnemonic']
        config['mnemonic'] = self._cipher.encrypt(self.config['mnemonic']).decode()
        print('Mnemonic saved: ', config['mnemonic'])
        content = f.write(json.dumps(config))
        config['mnemonic'] = mnemonic
        f.close()


    def generate_wallets(self):
        wallets = []
        mnemonic: str = self.config['mnemonic']
        derivations: int = 20
        # Initialize Ethereum mainnet BIP44HDWallet
        bip44_hdwallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)
        # Get Ethereum BIP44HDWallet from mnemonic
        print("Mnemonic to create derivational wallets: ", mnemonic)
        bip44_hdwallet.from_mnemonic(
            mnemonic=mnemonic, language="english"
        )
        bip44_hdwallet.clean_derivation()
        # Get Ethereum BIP44HDWallet information's from address index
        for address_index in range(derivations):
            # Derivation from Ethereum BIP44 derivation path
            bip44_derivation: BIP44Derivation = BIP44Derivation(
                cryptocurrency=EthereumMainnet, account=0, change=False, address=address_index
            )
            # Drive Ethereum BIP44HDWallet
            bip44_hdwallet.from_path(path=bip44_derivation)
            # Print address_index, path, address and private_key
            print(f"Derivasyonlar türetildi: ({address_index}) {bip44_hdwallet.address()}")
            wallet = [bip44_hdwallet.address(), bip44_hdwallet.private_key()]
            wallets.append(wallet)
            # Clean derivation indexes/paths
            bip44_hdwallet.clean_derivation()
        self.config['wallets'] = wallets
        self.save()

    def exists(self, key) -> bool:
        if key not in self.config:
            return False
        if self.config[key] is None:
            return False
        return bool(self.config[key])

