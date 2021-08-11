from base64 import urlsafe_b64encode
import hashlib
from cryptography.fernet import Fernet

SALT = "1234567891234567".encode('utf-8')
MAGIC_CHAR_SPLIT = "%"

def text_to_binary(ENCODED_INFORMATION):
    string = bytes.decode(str.encode(ENCODED_INFORMATION))
    bits_arr = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8,'0') for i in string])))
    return ''.join(str(e) for e in bits_arr)


def encrypt(password,text):
    key = hashlib.scrypt(bytes(password, 'utf-8'), salt=SALT, n=16384, r=8, p=1, dklen=32)
    key_encoded = urlsafe_b64encode(key)
    cipher_suite = Fernet(key_encoded)
    return cipher_suite.encrypt(bytes(text, 'utf-8'))


def decrypt(password,text_enc):
    key = hashlib.scrypt(bytes(password, 'utf-8'), salt=SALT, n=16384, r=8, p=1, dklen=32)
    key_encoded = urlsafe_b64encode(key)
    cipher_suite = Fernet(key_encoded)
    return cipher_suite.decrypt(text_enc.encode('utf-8'))

def principal_period(s):
    i = (s+s).find(s, 1, -1)
    return None if i == -1 else s[:i]