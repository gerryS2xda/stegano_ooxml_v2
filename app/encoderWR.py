import os
import shutil
import zipfile
import sys
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
BREAK_TAG = PREFIX_WORD_PROC + "br"

# Computa un valore casuale da assegnare escludendo quello che viene passato in input
def random_num_except(except_num):
    numbers = list(range(1, 1900))
    if int(except_num) > 0:
        numbers.remove(int(except_num))
    return random.choice(numbers)

# Merge di tutti i possibili "run element" che presentano le stesse caratteristiche (numero elementi XML figli)
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
        if j < len(run_property_elements) and len(run_property_elements[i]) != len(run_property_elements[j]):
            continue

        while mismatch != True and j < len(run_property_elements):
            for child_of_node in node:
                child_of_node_j = run_property_elements[j].find("./" + child_of_node.tag)
                if child_of_node_j == None or (child_of_node.tag != SZCS_TAG and (len(child_of_node_j.keys()) != len(child_of_node.keys()))):
                    mismatch = True
                    break
            #merge nodi fino al j - 1 elemento
            if mismatch == True:
                x = i + 1
                while x < j:
                    #append  node i + 1 to base node
                    node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if node == None: # se il nodo i + 1 non ha il text element, esci dal ciclo
                        break
                    base_node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if base_node == None: # se il base_node non ha il text element, esci dal ciclo
                        break
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

# Verifica se vi è spazio per effettuare un'altra iniezione nel run corrente di base
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

# Crea il file ".docx" contenente "document.xml" steganografato
def createFileStego(tree, path_file_extracted):
    input_file_name = os.path.splitext(os.path.split(os.path.split(path_file_extracted)[0])[1])[0] # no estensione file
    tree.write("stego/document.xml")
    copy_tree(path_file_extracted, "stego/file_extracted")
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
    if os.path.exists('./stego/' + input_file_name + '_stego.docx'):
        os.remove('./stego/' + input_file_name + '_stego.docx')
    os.rename('./stego/stego.zip', './stego/' + input_file_name + '_stego.docx')
    os.remove('./stego/document.xml')
    shutil.rmtree('./stego/file_extracted')

# Applicazione del metodo dello split in cui si incapsula il testo segreto in binario nel "document.xml" usando paragrafo e run element
def encoding(message, password, path_file_extracted):
    # step 1 -> Leggi il codice dal file "document.xml", relativo al documento D
    tree = etree.parse(path_file_extracted + "/word/document.xml")
    root = tree.getroot()
    # step 2 -> Cifra il testo segreto H mediante l’algoritmo AES-CBC, usando la chiave simmetrica
    encrypted = utils.encrypt(password, message)
    print(encrypted)
    # step 3 -> aggiungi alla fine del testo cifrato il carattere di divisione "%"
    information_to_encode_bits = utils.text_to_binary(encrypted.decode('utf-8')) + utils.text_to_binary(
        utils.MAGIC_CHAR_SPLIT)

    # Inizializzazione di un contatore di caratteri e di inclusione
    total_counter_characters = 0
    total_counter_inclusion = 0
    i = 0  # conta i caratteri usati per l'incapsulamento dei bit
    count_txt_tag_base = 0  # for testing
    count_txt_tag = 0  # for testing

    print("INIEZIONE IN CORSO .....")
    paragraphs = root.findall("./" + BODY_TAG + "/" + PARAGRAPH_TAG)
    # Step 4 -> Estrai tutti i paragrafi <w:p> presenti in P
    for paragraph in paragraphs:
        # step 5 -> IF (2 o più elementi <w:r> consecutivi in P hanno gli stessi attributi) THEN unisci gli elementi consecutivi <w:r>.;
        merge_possible_run_elements(paragraph)

        # Step 6 -> Estrai tutti gli elementi <w:r> in R e poi considera solo quelli con il text element
        run_elements = paragraph.findall("./" + RUN_ELEMENT_TAG)

        # Inizializzazione contatori per tenere traccia dei run
        i_run_elements = 1
        offset_run_elem = 1  # run da saltare rispetto a quelli di base correnti

        szcs_val_prec = 0
        while i_run_elements <= len(run_elements):
            # Considera solo <w:r> con text element
            if run_elements[i_run_elements-1].find("./" +  TEXT_TAG) == None:
                i_run_elements += 1
                offset_run_elem += 1
                continue
            count_txt_tag_base +=1

            # Computa valore da assegnare all'attributo "w:val" di <szCs> usato come marker split
            szcs_val_prec = random_num_except(szcs_val_prec)

            # Step 8 -> Inizializza il contatore N=1 per accumulare il numero di caratteri da dividere.
            # Successivamente, conta il numero di caratteri in T e memorizzali nella variabile C.
            N = 1
            txt_element_tag = run_elements[i_run_elements - 1].find("./" + TEXT_TAG)
            count = len(txt_element_tag.text)
            total_counter_characters += count

            # Se il run element corrente non contiene tag <w:rPr>, si crea e aggiunge tale tag
            if run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG) == None:
                rpr = etree.Element(RUN_ELEM_PROPERTY_TAG)
                rpr.append(etree.Element(SZCS_TAG))
                rpr.find("./" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", szcs_val_prec.__str__())
                run_elements[i_run_elements - 1].insert(0, rpr) # aggiungi tag <w:rPr> prima del testo (necessario altrimenti non vengono applicate le proprietà)
            # Altrimenti, se non contiene il tag <szCS> lo aggiungo al run element corrente
            elif run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) == None:
                    run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG).append(etree.Element(SZCS_TAG))
                    run_elements[i_run_elements - 1].find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val",szcs_val_prec.__str__())

            while count >= 1:
                # Check if enough space to inject information coded remain
                if(check_if_available_space(i,paragraph,information_to_encode_bits,offset_run_elem,count) == False):
                    break

                # Step 9 -> Leggi un bit da "information_to_encode_bits" in modo circolare e decrementa "count"
                # Caso a) Se il bit è 0, allora incrementa N
                if(information_to_encode_bits[i % len(information_to_encode_bits)]) == "0":
                    N += 1
                # Caso b
                elif paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]" + "/" + TEXT_TAG) != None:
                    tag_element = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]" + "/" + TEXT_TAG)
                    text = tag_element.text
                    new_run_elem = copy.copy(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]"))

                    # Rimuovi il tag <w:br> (Break) dal nuovo "run" se presente per evitare alterazione del testo
                    if new_run_elem.find("./" + BREAK_TAG) != None: # (da gestire in fase di decodifica)
                        new_run_elem.remove(new_run_elem.find("./" + BREAK_TAG))

                    # step 10 -> Modify the splitting mark <w:szCs> in the run elements alternatively.
                    if new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) != None:
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val",random_num_except(szcs_val_prec).__str__())
                    # Aggiungo tag <w:szCs> all'elemento <w:rPr>
                    else:
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG).insert(1,etree.Element(SZCS_TAG))
                        new_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).set(PREFIX_WORD_PROC + "val", random_num_except(szcs_val_prec).__str__())

                    tag_element.text = text[0:N]
                    new_run_elem.find("./" + TEXT_TAG).text = text[N:]
                    # Aggiungo space preserve
                    tag_element.set("{http://www.w3.org/XML/1998/namespace}space","preserve")
                    new_run_elem.find("./" + TEXT_TAG).set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    paragraph.insert(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]").getparent().index(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]")) + 1, new_run_elem)
                    offset_run_elem += 1
                    if len(text[N:]) == 0: # anche se <w:t> è vuoto, il decoder lo ignora dall'estrazione
                        new_run_elem.find("./" + TEXT_TAG).text = ""
                    # optimization -> remove tree.write("stego/document.xml")
                    N = 1
                    count_txt_tag += 1
                i += 1
                count -= 1
                # step 11 -> Ritorna allo step 9 fino a quando C >= 1;
            i_run_elements += 1
            offset_run_elem += 1
            # Step 12 -> Ripeti dallo step 6 allo step 11 finché tutti gli elementi <w:r> in P non sono stati risolti;
        # Step 13 -> Ripeti dallo step 4 allo step 12 finché tutti i paragrafi P non sono stati risolti.
    # Verifica se il file dato in input ha la capacità di contenere la rappresentazione in bit del testo segreto cifrato
    total_counter_inclusion = i
    total_complete_repeat_segret_text = total_counter_inclusion // len(information_to_encode_bits) # numero di volte in cui il testo segreto è stato incapsulato
    # Se il numero di bit del cifrato da iniettare è superiore alla capacità del documento di ammettere lo split del contenuto testuale -> annulla codifica
    if len(information_to_encode_bits) > total_counter_inclusion:
        utils.remove_directory(os.path.split(path_file_extracted)[0])
        sys.exit("Non è stato possibile iniettare il testo segreto poichè presenta un numero di bits maggiori della capacità di inclusione!!\nFine!")

    # Stampa le statistiche in merito al numero di parole, inclusioni, bit da codificare e altro per il testing
    utils.printStatistics(total_counter_characters, total_counter_inclusion, information_to_encode_bits, total_complete_repeat_segret_text)
    count_txt_tag += count_txt_tag_base
    print("document.xml statistics: <w:t> di base: " + count_txt_tag_base.__str__() + "; dopo: " + count_txt_tag.__str__())

    # Crea il file steganografato
    createFileStego(tree, path_file_extracted)
    print("il file .docx steganografato è stato salvato nella directory \"stego\"")


