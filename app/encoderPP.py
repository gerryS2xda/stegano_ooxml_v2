import os
import shutil
import zipfile
import sys
from distutils.dir_util import copy_tree
from lxml import etree
import copy 
import random
from app import utils

#Constant for XML PresentationML element
PREFIX_POWERPOINT_PROC = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
CONTENT_SLIDE_TREE_TAG = PREFIX_POWERPOINT_PROC + "cSld"
SHAPE_TREE_TAG = PREFIX_POWERPOINT_PROC + "spTree"
SHAPE_TAG = PREFIX_POWERPOINT_PROC + "sp"
TEXT_BODY_TAG = PREFIX_POWERPOINT_PROC + "txBody"
#Constant for XML DrawingML element
PREFIX_DRAWING_ML = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PARAGRAPH_TAG = PREFIX_DRAWING_ML + "p"
RUN_ELEMENT_TAG = PREFIX_DRAWING_ML + "r"
TEXT_ELEMENT_TAG = PREFIX_DRAWING_ML + "t"
RUN_ELEMENT_PROPERTY_TAG = PREFIX_DRAWING_ML + "rPr"
RPR_ATTRIBUTE_FOR_MARKER_SPLIT = "bmk"

#Computa un valore casuale da assegnare escludendo quello che viene passato in input
def random_num_except(except_num):
    numbers = list(range(1, 1900))
    if int(except_num) > 0:
        numbers.remove(int(except_num))
    return random.choice(numbers)

#Merge di tutti i possibili "run element" che presentano le stesse caratteristiche (numero attributi e elementi XML figli) 
def merge_possible_run_elements(paragraph):
    #Cerca gli "run element property" (<a:rPr>) nel paragrafo e memorizzali in un array
    run_property_elements = []
    for node in paragraph.findall("./" + RUN_ELEMENT_TAG + "/" + RUN_ELEMENT_PROPERTY_TAG):
        if node.getparent().find("./" + TEXT_ELEMENT_TAG) != None:
            run_property_elements.append(node)
            
    i = 0
    for node in run_property_elements:
        mismatch = False
        j = i + 1
        #check sul numero degli attributi ed elementi. Se non hanno lo stesso numero di attributi o di elementi -> no merge
        if  j < len(run_property_elements) and \
                ((len(run_property_elements[i].keys()) !=  len(run_property_elements[j].keys())) or (len(run_property_elements[i]) !=  len(run_property_elements[j]))):
            continue
        
        #Merge dei possibili "Run element" sulla base degli elementi presenti in ciascun <a:rPr>
        while mismatch != True and j < len(run_property_elements):
            #Verifica che se "node i" ha gli stessi attributi di "node j", controlla se anche gli elementi al suo interno hanno le stesse caratteristiche
            if len(node.keys()) == len(run_property_elements[j].keys()):
                for child_of_node in node: #per ogni tag figlio presente in <a:rPr>
                    child_of_node_j = run_property_elements[j].find("./"  + child_of_node.tag)
                    if child_of_node_j == None or (len(child_of_node_j.keys()) != len(child_of_node.keys())):
                        mismatch = True
                        break
            else: 
                mismatch = True
            
            #merge nodi fino al j - 1 elemento
            if mismatch == True: #Se si è verificato un mismatch, fai il merge fino a questo punto
                x = i + 1
                while x < j:
                    #append "node i + 1" to "base node"
                    node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
                    if node == None:
                        break
                    base_node =  paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
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
                    node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
                    if node == None:
                        break
                    #NEW DA TESTARE COMPLETO
                    if paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG) == None:
                        paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]").append(etree.Element(TEXT_ELEMENT_TAG))
                        paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG).text = node.text
                    else:
                        base_node =  paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
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

        if j == len(run_property_elements):
            break
        i += 1

def check_if_available_space(index, paragraph, information_to_encode_bits, offset_run_elem, count):
    count_zero = 0
    j = index
    while information_to_encode_bits[j % len(information_to_encode_bits)] == "0":
        j += 1
        count_zero += 1
    if count < count_zero + 1:
        node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]")
        node.find("./" + RUN_ELEMENT_PROPERTY_TAG).set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, "0")
        return False
    return True

def printStatistics(total_counter_characters, total_counter_inclusion, information_to_encode_bits, total_complete_repeat_segret_text):
    print("Capacità totale (# caratteri contenuto testuale): " + total_counter_characters.__str__())
    print("Capacità di inclusione (# caratteri usati): " + total_counter_inclusion.__str__())
    print("Numero minimo di bits da iniettare per testo segreto: " + len(information_to_encode_bits).__str__())
    print("Numero di volte in cui il testo segreto è stato iniettato: " + total_complete_repeat_segret_text.__str__())

def createFileStego(tree, path_file_extracted):
    tree.write("stego/slide1.xml")
    copy_tree(path_file_extracted, "stego/file_extracted")
    shutil.copy("stego/slide1.xml", "stego/file_extracted/ppt/slides")
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
    if (os.path.exists('./stego/stego.pptx')):
        os.remove('./stego/stego.pptx')
    os.rename('./stego/stego.zip', './stego/stego.pptx')
    #os.remove('./stego/slide1.xml')
    shutil.rmtree('./stego/file_extracted')
    return "stego/stego.zip"

#Applicazione del metodo dello split in cui si incapsula il testo segreto in binario in una slide usando paragrafo e run element
def encoding(message, password, path_file_extracted):
    #Step 1 -> Leggi il codice dal file "slides/slide1.xml", relativo al documento D
    tree = etree.parse(path_file_extracted + "/ppt/slides/slide1.xml")
    root = tree.getroot()  #get <p:sld> element
    
    #Step 2 -> Cifra il testo segreto H mediante l’algoritmo AES-CBC, usando la chiave simmetrica
    encrypted = utils.encrypt(password, message)
    
    #Step 3 -> Aggiungi alla fine del testo cifrato il carattere di divisione "%".
    information_to_encode_bits = utils.text_to_binary(encrypted.decode("utf-8")) + utils.text_to_binary(utils.MAGIC_CHAR_SPLIT)

    # Inizializzazione di un contatore di caratteri e di inclusione
    total_counter_characters = 0
    total_counter_inclusion = 0
    print("INIEZIONE IN CORSO .....")
    
    # Step 4 -> Estrai tutti gli shape <p:sp> presenti in SP
    shapes = root.findall("./" + CONTENT_SLIDE_TREE_TAG + "/" + SHAPE_TREE_TAG + "/" + SHAPE_TAG)
    i = 0

    for shape in shapes:
        #Step 5 -> Verifica se shape contiene un txbody tag
        txBody = shape.find("./" + TEXT_BODY_TAG)
        if txBody == None:
            continue

        #Step 6 -> Estrai paragrafo <a:p> in P
        paragraphs = txBody.findall("./" + PARAGRAPH_TAG)
        for paragraph in paragraphs:
            #Step 7 -> IF (2 o più elementi <a:r> consecutivi in P hanno gli stessi attributi) THEN unisci gli elementi consecutivi <a:r>; 
            merge_possible_run_elements(paragraph)
            
            #Step 8 -> Estrai elemento <a:r> in R e i relativi <a:t> (text element) in T
            run_elements = []
            for run_element in paragraph.findall("./" + RUN_ELEMENT_TAG):
                txt_tag = run_element.find("./" + TEXT_ELEMENT_TAG)
                #Se il run element ha un "text element" allora lo puoi estrarre
                if txt_tag != None:
                    run_elements.append(run_element)

            index_run_element = 1
            offset_run_element = 1
            bmk_attr_val_prec = 0
            while index_run_element <= len(run_elements):
                # Computa valore da assegnare all'attributo "bmk" di <a:rPr> usato come marker split
                bmk_attr_val_prec = random_num_except(bmk_attr_val_prec)

                # Step 9 -> Inizializza il contatore N=1 per accumulare il numero di caratteri da dividere.
                # Successivamente, conta il numero di caratteri in T, e memorizzali nella variabile C.
                N = 1
                txt_elem_tag = run_elements[index_run_element-1].find("./" + TEXT_ELEMENT_TAG)
                count = len(txt_elem_tag.text)
                total_counter_characters += count
                
                # Se il run element corrente non contiene tag <a:rPr>, si creare e aggiunge tale tag
                if run_elements[index_run_element-1].find("./" + RUN_ELEMENT_PROPERTY_TAG) == None:
                    rpr = etree.Element(RUN_ELEMENT_PROPERTY_TAG)
                    rpr.set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, bmk_attr_val_prec.__str__()) #aggiungi attributo "bmk"
                    run_elements[index_run_element-1].append(rpr)
                # Altrimenti, se non contiene l'attributo "RPR_ATTRIBUTE_FOR_MARKER_SPLIT", aggiungilo a <a:rPr>
                elif run_elements[index_run_element-1].find("./" + RUN_ELEMENT_PROPERTY_TAG).get(RPR_ATTRIBUTE_FOR_MARKER_SPLIT) == None:
                    run_elements[index_run_element-1].find("./" + RUN_ELEMENT_PROPERTY_TAG).set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, bmk_attr_val_prec.__str__()) #aggiungi attributo "bmk"

                while count >= 1:
                    # Check if enough space to inject information coded remain
                    if(check_if_available_space(i, paragraph, information_to_encode_bits, offset_run_element, count) == False):
                        break

                    # Step 10 -> Leggi un bit da "information_to_encode_bits" in modo circolare e decrementa "count"
                    # Caso a) Se il bit è 0, allora incrementa N
                    if information_to_encode_bits[i % len(information_to_encode_bits)] == "0":
                        N +=1
                    # Caso b)
                    elif (paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]/" + TEXT_ELEMENT_TAG)) != None:
                        txt_elem_tag = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]/" + TEXT_ELEMENT_TAG)
                        text = txt_elem_tag.text
                        new_run_element = copy.copy(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]"))
                        
                        # Step 11 -> Aggiungi o modifica l’attributo bmk al tag <a:rPr> usato come marker di split
                        new_run_element.find("./" + RUN_ELEMENT_PROPERTY_TAG).set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, (random_num_except(bmk_attr_val_prec)).__str__())

                        # Aggiungi un nuovo <r> e setta il tag <t>
                        txt_elem_tag.text = text[0:N]
                        new_run_element.find("./" + TEXT_ELEMENT_TAG).text = text[N:]
                        paragraph.insert(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]").getparent().index(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]")) + 1, new_run_element)
                        offset_run_element += 1
                        if len(text[N:]) == 0: # necessario altrimenti crea un text element vuoto (<a:t/>) che viene rimosso quando si salva il file
                            new_run_element.find("./" + TEXT_ELEMENT_TAG).text = " "
                        # optimization -> remove tree.write("stego/document.xml")
                        N = 1
                    i+=1
                    count -= 1
                    # Step 12 -> Ritorna allo step 10 finché C è >= 1
                index_run_element += 1
                offset_run_element += 1
                # Step 13 -> Ripeti dallo step 8 allo step 12 finché tutti gli elementi <a:r> in P non sono stati risolti
            # Step 14 -> Ripeti dallo step 6 allo step 13 finché tutti i paragrafi P non sono stati risolti
        # Step 15 -> Ripeti dallo step 4 allo step 14 finché tutti gli shape SP non sono stati risolti
    # Verifica se il file dato in input ha la capacità di contenere la rappresentazione in bit del testo segreto cifrato
    total_counter_inclusion = i
    total_complete_repeat_segret_text = total_counter_inclusion // len(information_to_encode_bits)  # numero di volte in cui il testo segreto è stato incapsulato
    # Se il numero di bit del cifrato da iniettare è superiore alla capacità del documento di ammettere lo split del contenuto testuale -> annulla codifica
    if len(information_to_encode_bits) > total_counter_inclusion:
        sys.exit("Non è stato possibile iniettare il testo segreto poichè presenta un numero di bits maggiori della capacità di inclusione!!\nFine!")

    # Stampa le statistiche in merito al numero di parole, inclusioni e bit da codificare
    printStatistics(total_counter_characters, total_counter_inclusion, information_to_encode_bits, total_complete_repeat_segret_text)

    #Crea il file ".pptx" contenente il testo segreto
    createFileStego(tree, path_file_extracted)
    print("Il file .pptx steganografato è stato salvato nella directory \"stego\"")
