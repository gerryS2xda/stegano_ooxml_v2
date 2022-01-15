import os
import shutil
from zipfile import ZipFile
import sys
from base64 import urlsafe_b64encode
import hashlib
from cryptography.fernet import Fernet
import re

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

# Statistics (for testing)
# Stampa le statistiche in merito a caratteri totali del contenuto testuale, caratteri usati per inclusione, numero di bit testo segreto e quante volte è stato iniettato
def printStatistics(total_counter_characters, total_counter_inclusion, information_to_encode_bits, total_complete_repeat_segret_text):
    print("Capacità totale (# caratteri contenuto testuale): " + total_counter_characters.__str__())
    print("Capacità di inclusione (# caratteri usati): " + total_counter_inclusion.__str__())
    bit_rate = total_counter_inclusion / total_counter_characters
    print("Bit rate: " + bit_rate.__str__())
    print("Numero minimo di bits da iniettare per testo segreto: " + len(information_to_encode_bits).__str__())
    print("Numero di volte in cui il testo segreto è stato iniettato: " + total_complete_repeat_segret_text.__str__())


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

# Extract range of cells (es. "A3:O103") using by a table in a worksheet XML (Excel)
def extract_startend_row_column_cell_used_by_table(range_cell_table):
    x = range_cell_table.split(":") # es. ['A3', 'O103']
    row_start = int(re.findall(r'\d+', x[0])[0]) # es. 3
    row_end = int(re.findall(r'\d+', x[1])[0]) # es. 103
    col_start = re.findall(r'[A-Z]+', x[0])[0] # 'A'
    col_end = re.findall(r'[A-Z]+', x[1])[0] # 'O'

    return row_start, row_end, col_start, col_end