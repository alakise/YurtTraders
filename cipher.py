import base64

from cryptography.fernet import Fernet, InvalidToken
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Cipher:

    def __init__(self, password: str):
        key = self._generate_key(password)
        self.__cipher_suite = Fernet(key)

    def encrypt(self, content: str):
        return self.__cipher_suite.encrypt(content.encode('utf-8'))

    def decrypt(self, content: bytes):
        print("Decrpyting user info...")
        try:
            return self.__cipher_suite.decrypt(content).decode()
        except InvalidToken:
            return False

    @staticmethod
    def _generate_key(password: str):
        salt = b'\x92\x96q+\xcbY\xbd\xf5,O\x8f\xadY\xa0\x11\x10'
        # derive
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode('utf-8'))
        return base64.urlsafe_b64encode(key)

