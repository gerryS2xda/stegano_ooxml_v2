import os
import sys
import time
from app import encoderWR
from app import encoderPP
from app import encoderEX
from app import decoderWR
from app import decoderPP
from app import decoderEX
from app import utils

# Configuration
INPUT_FILES_DIR = "./input"
WORKING_DIRECTORY_PATH = "./working_directory"
OUTPUT_STEGO_DIRECTORY = "./stego"

if __name__ == '__main__':
    # Crea le directory di lavoro se non sono presenti
    if not os.path.exists(INPUT_FILES_DIR):
        os.mkdir(INPUT_FILES_DIR)
    if not os.path.exists(WORKING_DIRECTORY_PATH):
        os.mkdir(WORKING_DIRECTORY_PATH)
    if not os.path.exists(OUTPUT_STEGO_DIRECTORY):
        os.mkdir(OUTPUT_STEGO_DIRECTORY)

    # Select mode to operate
    print("Seleziona la modalità di esecuzione digitando: \"1\" - Encoder; \"2\" - Decoder;")
    mode = input("Digita: ")
    if mode == "1":
        # Encoder mode
        print("* * * * Encoder mode * * * *")
        # Read input file to apply Steganographic method (es. sample_file.docx, sample_file.pptx, sample_file.xlsx)
        input_file_name = input("Inserisci il nome del file (es. fname.docx) da steganografare (deve essere nella directory \""+ INPUT_FILES_DIR + "\"): ")

        # Check existence of input file
        path_input_file = INPUT_FILES_DIR + "/" + input_file_name
        if not os.path.exists(path_input_file):
            sys.exit("Il nome del file inserito non è presente nella directory \"input\"")

        # Check correct extension of input file
        input_file_extension = os.path.splitext(path_input_file)[1]
        utils.check_correct_extension_inputfile(input_file_extension)

        # Extract file in working folder
        utils.extract_ooxml_input_file_in_working_directory(WORKING_DIRECTORY_PATH, path_input_file, input_file_name)

        # Message to hide
        message = input("Inserisci testo segreto: ")

        # Insert passphrase to generate symmectric key for encrypt
        password = input("Inserisci password per la cifratura del testo: ")

        # Init start execution time
        start_time = time.time()

        # Select type of encoding by type of input file (i.e. fname.docx -> use encoder for docx)
        path_file_extracted = WORKING_DIRECTORY_PATH + "/" + input_file_name + "/file_extracted"
        if input_file_extension == ".docx":
            print("Esecuzione text split method per un documento Word...")
            encoderWR.encoding(message, password, path_file_extracted)
        elif input_file_extension == ".pptx":
            print("Esecuzione text split method per una presentazione PowerPoint...")
            encoderPP.encoding(message, password, path_file_extracted)
        elif input_file_extension == ".xlsx":
            print("Esecuzione text split method per una cartella di fogli di lavoro Excel...")
            encoderEX.encoding(message, password, path_file_extracted)

        # Stop execution time and print
        execution_time = time.time() - start_time
        print("Tempo di esecuzione dell'encoder: " + execution_time.__str__() + " secondi")

        # Remove input file folder with extracted file from "working_directory"
        utils.remove_directory(WORKING_DIRECTORY_PATH + "/" + input_file_name)
    elif mode == "2":
        # Decoder mode
        print("* * * * Decoder mode * * * *")
        # Read input file to extract segret message (es. sample_file_stego.docx, sample_file_stego.pptx, sample_file_stego.xlsx)
        input_file_name = input("Inserisci il nome del file steganografato (es. fname_stego.docx) presente nella directory \"stego\": ")

        # Check existence of input file
        path_input_file =  OUTPUT_STEGO_DIRECTORY + "/" + input_file_name
        if not os.path.exists(path_input_file):
            sys.exit("Il nome del file inserito non è presente nella directory \"" + OUTPUT_STEGO_DIRECTORY +"\"")

        # Check correct extension of input file
        input_file_extension = os.path.splitext(path_input_file)[1]
        utils.check_correct_extension_inputfile(input_file_extension)

        # Extract file in working folder
        utils.extract_ooxml_input_file_in_working_directory(WORKING_DIRECTORY_PATH, path_input_file, input_file_name)

        # Insert passphrase to generate symmectric key for decrypt
        password = input("Inserisci password per decifrare il testo segreto: ")

        # Init start execution time
        start_time = time.time()

        # Select type of encoding by type of input file (i.e. fname.docx -> use encoder for docx)
        path_file_extracted = WORKING_DIRECTORY_PATH + "/" + input_file_name + "/file_extracted"
        if input_file_extension == ".docx":
            print("Esecuzione text split method per estrazione di un testo segreto da un documento Word...")
            decoderWR.decoding(password, path_file_extracted)
        elif input_file_extension == ".pptx":
            print("Esecuzione text split method per estrazione di un testo segreto da una presentazione PowerPoint...")
            decoderPP.decoding(password, path_file_extracted)
        elif input_file_extension == ".xlsx":
            print("Esecuzione text split method per per estrazione di un testo segreto da cartella di fogli di lavoro Excel...")
            decoderEX.decoding(password, path_file_extracted)

        # Stop execution time and print
        execution_time = time.time() - start_time
        print("Tempo di esecuzione del decoder: " + execution_time.__str__() + " secondi")

        # Remove input file folder with extracted file from "working_directory"
        utils.remove_directory(WORKING_DIRECTORY_PATH + "/" + input_file_name)
    else:
        sys.exit("Input digitato non è valido!! Fine!")
    exit(0)
