import os
import shutil
import zipfile
from distutils.dir_util import copy_tree

from lxml import etree
import copy
import random
from app import utils

#Constant for XML WordProcessingML element
PREFIX_WORD_PROC = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PARAGRAPH_TAG = PREFIX_WORD_PROC + "p"
RUN_ELEMENT_TAG = PREFIX_WORD_PROC + "r"
RUN_ELEM_PROPERTY_TAG = PREFIX_WORD_PROC + "rPr"
VANISH_ELEM_TAG = PREFIX_WORD_PROC + "vanish"
BODY_TAG = PREFIX_WORD_PROC + "body"
TEXT_TAG = PREFIX_WORD_PROC + "t"
SZCS_TAG = PREFIX_WORD_PROC + "szCs"


def random_num_except(except_num):
    numbers = list(range(1, 1900))
    if int(except_num) > 0:
        numbers.remove(int(except_num))
    return random.choice(numbers)

def merge_possible_run_elements(paragraph):
     run_property_elements = []
     #ricerca run elements nel paragrafo
     for node in paragraph.findall("./" + RUN_ELEMENT_TAG + "/" + RUN_ELEM_PROPERTY_TAG):
         if node.getparent().find("./" + TEXT_TAG) != None:
             run_property_elements.append(node)
     i = 0
     for node in run_property_elements:
        mismatch = False
        j = i + 1
        #check sul numero degli elementi. Se non hanno lo stesso numero di elementi -> no merge
        if  j < len(run_property_elements) and len(run_property_elements[i]) !=  len(run_property_elements[j]):
            continue

        while mismatch != True and j < len(run_property_elements):
            for child_of_node in node:
                child_of_node_j = run_property_elements[j].find("./"  + child_of_node.tag)
                if child_of_node_j == None or (child_of_node.tag != SZCS_TAG and child_of_node_j.attrib != child_of_node.attrib):
                    mismatch = True
                    break
            #merge nodi fino al j - 1 elemento
            if mismatch == True:
                x = i + 1
                while x < j:
                    #append  node i + 1 to base node
                    node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if node == None:
                        break
                    base_node =  paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG)
                    base_node.text = base_node.text + node.text
                    x += 1
                x = i + 1
                while x < j:
                    #rimuovo elemento successivo al nodo merge
                    run_property_elements.remove(run_property_elements[i + 1])
                    paragraph.remove(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 2).__str__() + "]"))
                    x += 1
            #se sono arrivato alla fine dei nodi del paragrafo --> tutti i nodi hanno gli stessi attributi
            elif (j == len(run_property_elements) - 1):
                x = i + 1
                while x <= j:
                    #append  node i + 1 to base node
                    node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if node == None:
                        break
                    #NEW DA TESTARE COMPLETO
                    if paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG) == None:
                        paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]").append(etree.Element(TEXT_TAG))
                        paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG).text = node.text
                    else:
                        base_node =  paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG)
                        base_node.text = base_node.text + node.text
                    x += 1
                x = i + 1
                while x <= j:
                    #rimuovo elemento successivo al nodo merge
                    run_property_elements.remove(run_property_elements[i + 1])
                    paragraph.remove(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 2).__str__() + "]"))
                    x += 1
            else:
                j += 1

        if(j== len(run_property_elements)):
            break
        i +=1



def check_if_available_space(index,paragraph,information_to_encode_bits,offset_run_elem,count):
    count_zero = 0
    j = index
    while information_to_encode_bits[j % len(information_to_encode_bits)] == "0":
        j += 1
        count_zero += 1
    if count < count_zero + 1:
        node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]")
        if node.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) != None:
            node.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", "0")
        else:
            etree.SubElement(node, SZCS_TAG)
            node.find("./" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", "0")
        return False
    return True


def printStat(total_counter_characters, total_counter_inclusion, information_to_encode_bits):
    print("CAPACITA' TOTALE :" + total_counter_characters.__str__())
    print("CAPACITA' INCLUSIONE:" + total_counter_inclusion.__str__())
    print("MINIMO DI BITS DA INIETTARE: " + len(information_to_encode_bits).__str__())

def createFileStego(tree,name_file):
    tree.write("stego/document.xml")
    copy_tree("input/" + name_file + "/file_extracted", "stego/file_extracted")
    shutil.copy("stego/document.xml", "stego/file_extracted/word")
    zf = zipfile.ZipFile("stego/stego.zip", "w",zipfile.ZIP_DEFLATED)
    for dirname, subdirs, files in os.walk("./stego/file_extracted"):
        for filename in files:
            path=""
            if dirname == "./stego/file_extracted":
                path = filename
            else:
                path = dirname.split("./stego/file_extracted")[1] + "/" + filename
            zf.write(os.path.join(dirname, filename),path)
    zf.close()
    # Check if file exists before to rename zip file
    if (os.path.exists('./stego/stego.docx')):
        os.remove('./stego/stego.docx')
    os.rename('./stego/stego.zip', './stego/stego.docx')
    #os.remove('./stego/document.xml')
    shutil.rmtree('./stego/file_extracted')
    return "stego/stego.zip"

def encoding(message, password, path_file_extracted):
    # step 1 -> Leggi il codice dal file "document.xml", relativo al documento D
    tree = etree.parse("input/" + path_file_extracted + '/file_extracted/word/document.xml')
    root = tree.getroot()

    # step 2 -> Cifra il testo segreto H mediante l’algoritmo AES-CBC, usando la chiave simmetrica
    encrypted = utils.encrypt(message, password)
    print(encrypted)

    # step 3 -> aggiungi alla fine del testo cifrato il carattere di divisione "%"
    information_to_encode_bits = utils.text_to_binary(encrypted.decode('utf-8')) + utils.text_to_binary(
        utils.MAGIC_CHAR_SPLIT)

    # Inizializzazione di un contatore di caratteri e di inclusione
    total_counter_characters = 0
    total_counter_inclusion = 0
    print("INIEZIONE IN CORSO .....")
    paragraphs = root.findall("./" + BODY_TAG + "/" + PARAGRAPH_TAG)
    i = 0
    # step 14 -> Ripeti step 6 - step 13 finché tutti gli elementi <w:r> in P  non sono stati risolti;
    for paragraph in paragraphs:
        #step 5 -> IF (2 o più elementi <w:r> consecutivi in P hanno gli stessi attributi) THEN unisci gli elementi consecutivi <w:r>.;
        merge_possible_run_elements(paragraph)

        run_elements = []
        for node in paragraph.findall("./" + RUN_ELEMENT_TAG):
            if node.find("./" + TEXT_TAG) != None:
                run_elements.append(node)
        i_run_elements = 1
        offset_run_elem = 1

        # aggiungo tutti i nodi != RUN_ELEMENT_TAG e li memorizzo in un array
        arr_childs_par_to_save = []
        for child_paragraph in paragraph.findall("./"):
            if child_paragraph.tag != RUN_ELEMENT_TAG:
                arr_childs_par_to_save.append(child_paragraph)
                #paragraph.remove(child_paragraph)
        szcs_val_prec = 0
        #step 14 -> risolvi tutti gli elementi <w:r> in P
        while i_run_elements <= len(run_elements):
            szcs_val_prec = random_num_except(szcs_val_prec)
            # step8 -> Inizializza il contatore N=1 per accumulare il numero di caratteri da dividere. Successivamente, conta il numero di caratteri in T, e memorizzali nella variabile C.
            N = 1
            total_counter_characters += len(run_elements[i_run_elements - 1].find("./" + TEXT_TAG).text)

            tag_element = run_elements[i_run_elements - 1].find("./" + TEXT_TAG)
            # se non contiene il tag rpr lo aggiungo al run element corrente
            if run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG) == None:
                rpr = etree.Element(RUN_ELEM_PROPERTY_TAG)
                rpr.append(etree.Element(SZCS_TAG))
                rpr.find("./" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", szcs_val_prec.__str__())
                run_elements[i_run_elements - 1].append(rpr)
            # se non contiene il tag szCS lo aggiungo al run element corrente
            elif run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) == None:
                    run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG).append(etree.Element(SZCS_TAG))
                    run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", szcs_val_prec.__str__())

            # step 8 -> Inizializza il contatore N=1 per accumulare il numero di caratteri da dividere. Successivamente, conta il numero di caratteri in T, e memorizzali nella variabile C.
            count = len(tag_element.text)
            #step 12 -> Ritorna allo step 9 fino a quando C >= 1;
            while count >=1:
                #check if enough space to inject information coded remain
                if(check_if_available_space(i, paragraph, information_to_encode_bits, offset_run_elem,count) == False):
                    break
                #step 9,10,11
                # case a
                if(information_to_encode_bits[i % len(information_to_encode_bits)]) == "0":
                    N += 1
                #case b
                elif paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]" + "/" + TEXT_TAG) != None:
                    tag_element = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]" + "/" + TEXT_TAG)
                    text = tag_element.text
                    new_run_elem = copy.copy(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]"))
                    # step 8 -> Modify the splitting mark <w:szCs> in the run elements alternatively.
                    if new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) != None:
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val",random_num_except(szcs_val_prec).__str__())
                    #aggiungo tag SZCS all'elemento rpr
                    else:
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG).insert(1,etree.Element(SZCS_TAG))
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", random_num_except(szcs_val_prec).__str__())

                    tag_element.text = text[0:N]
                    new_run_elem.find("./" + TEXT_TAG).text = text[N:]
                    #aggiungo space preserve
                    tag_element.set("{http://www.w3.org/XML/1998/namespace}space","preserve")
                    new_run_elem.find("./" + TEXT_TAG).set("{http://www.w3.org/XML/1998/namespace}space","preserve")
                    paragraph.insert(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]").getparent().index(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]")) + 1,new_run_elem)
                    offset_run_elem += 1
                    if len(text[N:]) == 0 and new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + VANISH_ELEM_TAG) == None:
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG).append(etree.Element(VANISH_ELEM_TAG))
                        new_run_elem.find("./" + TEXT_TAG).text = " "
                    # optimization -> remove tree.write("stego/document.xml")
                    N = 1
                i += 1
                count -= 1

                # step 7 -> Go to step 6 until the value of C is one.
            i_run_elements += 1
            offset_run_elem += 1
    total_counter_inclusion = i
    printStat(total_counter_characters, total_counter_inclusion, information_to_encode_bits)
    createFileStego(tree, path_file_extracted)
    print("Il file .docx steganografato è stato salvato nella directory stego")


if __name__ == '__main__':
    # Read input file to apply Steganographic method (es. ./word/document.xml)
    path_file_extracted = input("Inserisci il file da steganografare:")

    # Message to hide
    message = input("Inserisci il testo da nascondere:")

    # Insert passphrase to generate symmectric key for encrypt/decrypt
    password = input("Inserisci password per cifrare il testo:")

    encoding(message, password, path_file_extracted)
    exit(0)




