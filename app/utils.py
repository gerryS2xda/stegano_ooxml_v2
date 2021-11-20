import os
import shutil
from zipfile import ZipFile
import sys
from base64 import urlsafe_b64encode
import hashlib
from cryptography.fernet import Fernet

FILE_EXTENSION_ACCEPTED = [".docx", ".pptx", ".xlsx"]
SALT = "1234567891234567".encode('utf-8')
MAGIC_CHAR_SPLIT = "%"

# Cryptography utils
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

# Files and directory utils
# Verifica se il file posto in input è un file MS-Office (.docx, .pptx, .xlsx)
def check_correct_extension_inputfile(input_file_extension):
    isFileExtensionCorrect = False
    for ext in FILE_EXTENSION_ACCEPTED:
        if input_file_extension == ext:
            isFileExtensionCorrect = True
            break
    if not isFileExtensionCorrect:
        sys.exit("Tipo di file sconosciuto!! Richiesto file \".docx, .pptx, .xlsx\"")

# Extract OOXML input file in "working folder/nome_input_file/file_extracted"
def extract_ooxml_input_file_in_working_directory(path_working_directory, path_input_file, input_file_name):
    if not os.path.exists(path_working_directory):  # se non è la presente la working directory -> creala
        os.mkdir(path_working_directory)
    os.rename(path_input_file, path_input_file + ".zip")  # rinomina in zip file input temporaneamente per estrazione
    with ZipFile(path_input_file + ".zip", "r") as input_file_zip:
        print("Estrazione file in corso...")
        if not os.path.exists(path_working_directory + "/" + input_file_name):
            os.mkdir(path_working_directory + "/" + input_file_name)
        if not os.path.exists(path_working_directory + "/" + input_file_name + "/file_extracted"):
            os.mkdir(path_working_directory + "/" + input_file_name + "/file_extracted")
        input_file_zip.extractall(path_working_directory + "/" + input_file_name + "/file_extracted")
    input_file_zip.close()
    os.rename(path_input_file + ".zip", path_input_file)

def remove_directory(path_dir_to_remove):
    if os.path.exists(path_dir_to_remove):
        shutil.rmtree(path_dir_to_remove)