import os
import shutil
from zipfile import ZipFile
import sys
from app import encoderWR
from app import encoderPP
from app import encoderEX
from app import decoderWR
from app import decoderPP
from app import decoderEX
from app import utils

FILE_EXTENSION_ACCEPTED = [".docx", ".pptx", ".xlsx"]

if __name__ == '__main__':
    # Select mode to operate
    print("Seleziona la modalità di esecuzione digitando: \"1\" - Encoder; \"2\" - Decoder; \"3\" - Clean working directory")
    mode = input("Digita: ")
    if mode == "1":
        # Encoder mode
        print("* * * * Encoder mode * * * *")
        # Read input file to apply Steganographic method (es. sample_file.docx, sample_file.pptx, sample_file.xlsx)
        input_file_name = input("Inserisci il nome del file (es. fname.docx) da steganografare (deve essere nella directory \"input\"): ")

        # Check existence of input file
        path_input_file = "./test/" + input_file_name
        if not os.path.exists(path_input_file):
            sys.exit("Il nome del file inserito non è presente nella directory \"input\"")

        # Check correct extension of input file
        input_file_extension = os.path.splitext(path_input_file)[1]
        isFileExtensionCorrect = False
        for ext in FILE_EXTENSION_ACCEPTED:
            if input_file_extension == ext:
                isFileExtensionCorrect = True
                break
        if not isFileExtensionCorrect:
            sys.exit("Tipo di file sconosciuto!! Richiesto file \".docx, .pptx, .xlsx\"")

        # Extract file in working folder
        if not os.path.exists("./test/working_directory"): # se non è la presente la working directory -> creala
            os.mkdir("./test/working_directory")
        os.rename(path_input_file, path_input_file + ".zip") # rinomina in zip file input temporaneamente per estrazione
        with ZipFile(path_input_file + ".zip", "r") as input_file_zip:
            print("Estrazione file in corso...")
            if not os.path.exists("./test/working_directory/" + input_file_name):
                os.mkdir("./test/working_directory/" + input_file_name)
            if not os.path.exists("./test/working_directory/" + input_file_name + "/file_extracted"):
                os.mkdir("./test/working_directory/" + input_file_name + "/file_extracted")
            input_file_zip.extractall("./test/working_directory/" + input_file_name + "/file_extracted")
        input_file_zip.close()
        os.rename(path_input_file + ".zip", path_input_file)

        # Message to hide
        message = input("Inserisci testo segreto: ")

        # Insert passphrase to generate symmectric key for encrypt/decrypt
        password = input("Inserisci password per la cifratura del testo: ")

        # Select type of encoding by type of input file (i.e. fname.docx -> use encoder for docx)
        path_file_extracted = "./test/working_directory/" + input_file_name + "/file_extracted"
        if input_file_extension == FILE_EXTENSION_ACCEPTED[0]:
            print("Esecuzione text split method per un documento Word...")
            encoderWR.encoding(message, password, path_file_extracted)
        elif input_file_extension == FILE_EXTENSION_ACCEPTED[1]:
            print("Esecuzione text split method per una presentazione PowerPoint...")
            encoderPP.encoding(message, password, path_file_extracted)
        elif input_file_extension == FILE_EXTENSION_ACCEPTED[2]:
            print("Esecuzione text split method per una cartella di fogli di lavoro Excel...")
            encoderEX.encoding(message, password, path_file_extracted)
    elif mode == "2":
        # Decoder mode
        path_filename_to_extract = "stego/document.xml"
        password = input("inserisci la password per decifrare il testo: ")

        #decoding(password, path_filename_to_extract)
        exit(0)
    elif mode == "3":
        # Clean working directory
        if os.path.exists("./test/working_directory"):
            shutil.rmtree("./test/working_directory") # rimuovi l'intera directory
        else:
            print("\"working_directory\" è già vuota o non esiste!")
    else:
        sys.exit("Input digitato non è valido!! Fine!")
    exit(0)
