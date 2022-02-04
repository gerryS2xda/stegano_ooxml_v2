import os
import sys
import time
from webapp.backend import encoderWR
from webapp.backend import encoderPP
from webapp.backend import encoderEX
from webapp.backend import decoderWR
from webapp.backend import decoderPP
from webapp.backend import decoderEX
from webapp.backend import utils

# Other configuration (necessario path completo perche' os.cwd = "webapp")
INPUT_FILES_DIR = "./backend/input_files"
WORKING_DIRECTORY_PATH = "./backend/working_directory"
OUTPUT_STEGO_DIRECTORY = "./backend/output_stego"

def run_encoder(input_file_name, message, password):

    # Check existence of input file
    path_input_file = INPUT_FILES_DIR + "/" + input_file_name
    if not os.path.exists(path_input_file):
        print("Il nome del file inserito non è presente")
        return False, ""

    # Check correct extension of input file
    input_file_extension = os.path.splitext(path_input_file)[1]  # Es. ".docx"
    if not utils.check_correct_extension_inputfile_webapp(input_file_extension):
        print("Tipo di file sconosciuto!! Richiesto file \".docx, .pptx, .xlsx\"")
        return False, ""

    # Extract file in working folder
    utils.extract_ooxml_input_file_in_working_directory(WORKING_DIRECTORY_PATH, path_input_file, input_file_name)

    # Init start execution time
    start_time = time.time()

    # Select type of encoding by type of input file (i.e. fname.docx -> use encoder for docx)
    path_file_extracted = WORKING_DIRECTORY_PATH + "/" + input_file_name + "/file_extracted"
    path_output_stego_file = ""
    if input_file_extension == ".docx":
        print("Esecuzione text split method per un documento Word...")
        path_output_stego_file = encoderWR.encoding(message, password, path_file_extracted, OUTPUT_STEGO_DIRECTORY)
    elif input_file_extension == ".pptx":
        print("Esecuzione text split method per una presentazione PowerPoint...")
        path_output_stego_file = encoderPP.encoding(message, password, path_file_extracted, OUTPUT_STEGO_DIRECTORY)
    elif input_file_extension == ".xlsx":
        print("Esecuzione text split method per una cartella di fogli di lavoro Excel...")
        path_output_stego_file = encoderEX.encoding(message, password, path_file_extracted, OUTPUT_STEGO_DIRECTORY)

    # Stop execution time and print
    execution_time = time.time() - start_time
    print("Tempo di esecuzione dell'encoder: " + execution_time.__str__() + " secondi")

    # Remove input file folder with extracted file from "working_directory"
    utils.remove_directory(WORKING_DIRECTORY_PATH + "/" + input_file_name)

    return True, path_output_stego_file

def run_decoder(input_stegofile_name, password_dec):

    # Check existence of input file
    path_input_file = INPUT_FILES_DIR + "/" + input_stegofile_name
    if not os.path.exists(path_input_file):
        print("Il nome del file steganografato inserito non è presente")
        return False, ""

    # Check correct extension of input file
    input_file_extension = os.path.splitext(path_input_file)[1]  # Es. ".docx"
    if not utils.check_correct_extension_inputfile_webapp(input_file_extension):
        print("Tipo di file sconosciuto!! Richiesto file \".docx, .pptx, .xlsx\"")
        return False, ""

    # Extract file in working folder
    utils.extract_ooxml_input_file_in_working_directory(WORKING_DIRECTORY_PATH, path_input_file, input_stegofile_name)

    # Init start execution time
    start_time = time.time()

    # Message to extract
    message = ""

    # Select type of decoding by type of input file (i.e. fname.docx -> use decoder for docx)
    path_file_extracted = WORKING_DIRECTORY_PATH + "/" + input_stegofile_name + "/file_extracted"
    if input_file_extension == ".docx":
        print("Esecuzione text split method per estrazione di un testo segreto da un documento Word...")
        message = decoderWR.decoding(password_dec, path_file_extracted)
    elif input_file_extension == ".pptx":
        print("Esecuzione text split method per estrazione di un testo segreto da una presentazione PowerPoint...")
        message = decoderPP.decoding(password_dec, path_file_extracted)
    elif input_file_extension == ".xlsx":
        print("Esecuzione text split method per per estrazione di un testo segreto da cartella di fogli di lavoro Excel...")
        message = decoderEX.decoding(password_dec, path_file_extracted)

    # Stop execution time and print
    execution_time = time.time() - start_time
    print("Tempo di esecuzione del decoder: " + execution_time.__str__() + " secondi")

    # Remove input file folder with extracted file from "working_directory"
    utils.remove_directory(WORKING_DIRECTORY_PATH + "/" + input_stegofile_name)

    return True, message
