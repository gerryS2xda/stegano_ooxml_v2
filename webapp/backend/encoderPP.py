import os
import shutil
import zipfile
import sys
from lxml import etree
import copy 
import random
from webapp.backend import utils

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

# Computa un valore casuale da assegnare escludendo quello che viene passato in input
def random_num_except(except_num):
    numbers = list(range(1, 1900))
    if int(except_num) > 0:
        numbers.remove(int(except_num))
    return random.choice(numbers)

# Merge di tutti i possibili "run element" che presentano le stesse caratteristiche (numero attributi e elementi XML figli)
def merge_possible_run_elements(paragraph):
    # Cerca gli "run element property" (<a:rPr>) nel paragrafo e memorizzali in un array
    run_property_elements = []
    for node in paragraph.findall("./" + RUN_ELEMENT_TAG + "/" + RUN_ELEMENT_PROPERTY_TAG):
        if node.getparent().find("./" + TEXT_ELEMENT_TAG) != None:
            run_property_elements.append(node)

    i = 0
    for node in run_property_elements:
        mismatch = False
        j = i + 1
        # check sul numero degli attributi ed elementi. Se non hanno lo stesso numero di attributi o di elementi -> no merge
        if j < len(run_property_elements) and \
                ((len(run_property_elements[i].keys()) != len(run_property_elements[j].keys())) or (
                        len(run_property_elements[i]) != len(run_property_elements[j]))):
            continue

        # Merge dei possibili "Run element" sulla base degli elementi presenti in ciascun <a:rPr>
        while mismatch != True and j < len(run_property_elements):
            # Verifica che se "node i" ha gli stessi attributi di "node j", controlla se anche gli elementi al suo interno hanno le stesse caratteristiche
            if len(node.keys()) == len(run_property_elements[j].keys()):
                for child_of_node in node:  # per ogni tag figlio presente in <a:rPr>
                    child_of_node_j = run_property_elements[j].find("./" + child_of_node.tag)
                    if child_of_node_j == None or (len(child_of_node_j.keys()) != len(child_of_node.keys())):
                        mismatch = True
                        break
            else:
                mismatch = True

            # merge nodi fino al j - 1 elemento
            if mismatch == True:  # Se si è verificato un mismatch, fai il merge fino a questo punto
                x = i + 1
                while x < j:
                    # append "node i + 1" to "base node"
                    node = paragraph.find(
                        "./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
                    if node == None:  # se il nodo i + 1 non ha il text element, esci dal ciclo
                        break
                    base_node = paragraph.find(
                        "./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
                    if base_node == None:  # se il base_node non ha il text element, esci dal ciclo
                        break
                    base_node.text = base_node.text + node.text
                    x += 1
                x = i + 1
                while x < j:
                    # rimuovo elemento successivo al nodo merge
                    run_property_elements.remove(run_property_elements[i + 1])
                    paragraph.remove(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 2).__str__() + "]"))
                    x += 1
            # se sono arrivato alla fine dei nodi del paragrafo --> tutti i nodi hanno gli stessi attributi
            elif (j == len(run_property_elements) - 1):
                x = i + 1
                while x <= j:
                    # append  node i + 1 to base node
                    node = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
                    if node == None:
                        break
                    # NEW DA TESTARE COMPLETO
                    if paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG) == None:
                        paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]").append(etree.Element(TEXT_ELEMENT_TAG))
                        paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG).text = node.text
                    else:
                        base_node = paragraph.find( "./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_ELEMENT_TAG)
                        base_node.text = base_node.text + node.text
                    x += 1
                x = i + 1
                while x <= j:
                    # rimuovo elemento successivo al nodo merge
                    run_property_elements.remove(run_property_elements[i + 1])
                    paragraph.remove(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (i + 2).__str__() + "]"))
                    x += 1
            else:
                j += 1

        if j == len(run_property_elements):
            break
        i += 1

# Verifica se vi è spazio per effettuare un'altra iniezione nel run corrente di base
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

# Crea il file "slideX.xml" steganografato e aggiungilo in "stego/file_extracted"
def createSlideStego(tree, slide_filename, output_stego_directory_path):
    tree.write(output_stego_directory_path + "/" + slide_filename)
    shutil.copy(output_stego_directory_path + "/" + slide_filename, output_stego_directory_path + "/file_extracted/ppt/slides")
    os.remove(output_stego_directory_path + '/' + slide_filename)

# Crea il file ".pptx" contenente le slide steganografate
def createFileStego(path_file_extracted, output_stego_directory_path):
    input_file_name = os.path.splitext(os.path.split(os.path.split(path_file_extracted)[0])[1])[0]  # no estensione file
    zf = zipfile.ZipFile(output_stego_directory_path + "/stego.zip", "w", zipfile.ZIP_DEFLATED)
    for dirname, subdirs, files in os.walk(output_stego_directory_path + "/file_extracted"):
        for filename in files:
            path= ""
            if dirname == (output_stego_directory_path + "/file_extracted"):
                path = filename
            else:
                path = dirname.split(output_stego_directory_path + "/file_extracted")[1] + "/" + filename
            zf.write(os.path.join(dirname, filename), path)
    zf.close()
    # Check if file exists before to rename zip file
    if os.path.exists(output_stego_directory_path + '/' + input_file_name + '_stego.pptx'):
        os.remove(output_stego_directory_path + '/' + input_file_name + '_stego.pptx')
    os.rename(output_stego_directory_path + '/stego.zip', output_stego_directory_path + '/' + input_file_name + '_stego.pptx')
    shutil.rmtree(output_stego_directory_path + '/file_extracted')

    path_output_stego_file = output_stego_directory_path + '/' + input_file_name + '_stego.pptx'
    return path_output_stego_file

# Applicazione del metodo dello split in cui si incapsula il testo segreto in binario in una slide usando paragrafo e run element
def encoding(message, password, path_file_extracted, output_stego_directory_path):
    # Step 1 -> Cifra il testo segreto H mediante l’algoritmo AES-CBC, usando la chiave simmetrica
    encrypted = utils.encrypt(password, message)
    print(encrypted)

    # Step 2 -> Aggiungi alla fine del testo cifrato il carattere di divisione "%".
    information_to_encode_bits = utils.text_to_binary(encrypted.decode("utf-8")) + utils.text_to_binary(
        utils.MAGIC_CHAR_SPLIT)

    # Inizializzazione di un contatore di caratteri e di caratteri usati per inclusione
    total_counter_characters = 0
    total_counter_inclusion = 0
    i = 0 # conta i caratteri usati per l'incapsulamento dei bit
    count_txt_tag_base = 0  # for testing
    count_txt_tag = 0  # for testing

    # Inizializza il file .pptx steganografato copiando il contenuto originale in "stego/file_extracted"
    if os.path.exists("stego/file_extracted"):
        shutil.rmtree('./stego/file_extracted')
    shutil.copytree(path_file_extracted, "stego/file_extracted")

    # Step 3 -> Per ciascuna slide presente nella directory "ppt/slides" della presentazione D
    slides = os.listdir(path_file_extracted + "/ppt/slides")
    for slide in slides:    # Rimuovi tutti i nomi dei file che sono diversi da "slideX.xml"
        if slide.find("slide") == -1:
            slides.remove(slide)

    for slide in slides:
        #print("INIEZIONE IN CORSO in " + slide + "...")

        # Step 4 -> Leggi il codice dal file "slides/slideX.xml"
        tree = etree.parse(path_file_extracted + "/ppt/slides/" + slide)
        root = tree.getroot()  #get <p:sld> element

        # Step 5 -> Estrai tutti gli shape <p:sp> presenti in SP
        shapes = root.findall("./" + CONTENT_SLIDE_TREE_TAG + "/" + SHAPE_TREE_TAG + "/" + SHAPE_TAG)
        for shape in shapes:
            # Step 6 -> Verifica se shape contiene un txbody tag
            txBody = shape.find("./" + TEXT_BODY_TAG)
            if txBody == None:
                continue

            # Step 7 -> Estrai paragrafo <a:p> in P
            paragraphs = txBody.findall("./" + PARAGRAPH_TAG)
            for paragraph in paragraphs:
                # Step 8 -> IF (2 o più elementi <a:r> consecutivi in P hanno gli stessi attributi) THEN unisci gli elementi consecutivi <a:r>;
                merge_possible_run_elements(paragraph)

                # Step 9 -> Estrai elemento <a:r> in R e i relativi <a:t> (text element) in T
                run_elements = paragraph.findall("./" + RUN_ELEMENT_TAG)

                # Inizializzazione contatori per tenere traccia dei run
                index_run_element = 1
                offset_run_element = 1  # run da saltare rispetto a quelli di base correnti

                bmk_attr_val_prec = 0
                while index_run_element <= len(run_elements):
                    # Considera solo <a:r> con text element
                    if run_elements[index_run_element-1].find("./" + TEXT_ELEMENT_TAG) == None:
                        index_run_element += 1
                        offset_run_element += 1
                        continue
                    count_txt_tag_base += 1

                    # Computa valore da assegnare all'attributo "bmk" di <a:rPr> usato come marker split
                    bmk_attr_val_prec = random_num_except(bmk_attr_val_prec)

                    # Step 10 -> Inizializza il contatore N=1 per accumulare il numero di caratteri da dividere.
                    # Successivamente, conta il numero di caratteri in T, e memorizzali nella variabile C.
                    N = 1
                    txt_elem_tag = run_elements[index_run_element-1].find("./" + TEXT_ELEMENT_TAG)
                    count = len(txt_elem_tag.text)
                    total_counter_characters += count

                    # Se il run element corrente non contiene tag <a:rPr>, si creare e aggiunge tale tag
                    if run_elements[index_run_element-1].find("./" + RUN_ELEMENT_PROPERTY_TAG) == None:
                        rpr = etree.Element(RUN_ELEMENT_PROPERTY_TAG)
                        rpr.set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, bmk_attr_val_prec.__str__()) #aggiungi attributo "bmk"
                        run_elements[index_run_element-1].insert(0, rpr) # aggiungi tag <a:rPr> prima del testo (necessario altrimenti non vengono applicate le proprietà)
                    # Altrimenti, se non contiene l'attributo "RPR_ATTRIBUTE_FOR_MARKER_SPLIT", aggiungilo a <a:rPr>
                    elif run_elements[index_run_element-1].find("./" + RUN_ELEMENT_PROPERTY_TAG).get(RPR_ATTRIBUTE_FOR_MARKER_SPLIT) == None:
                        run_elements[index_run_element-1].find("./" + RUN_ELEMENT_PROPERTY_TAG).set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, bmk_attr_val_prec.__str__()) #aggiungi attributo "bmk"

                    while count >= 1:
                        # Check if enough space to inject information coded remain
                        if(check_if_available_space(i, paragraph, information_to_encode_bits, offset_run_element, count) == False):
                            break

                        # Step 11 -> Leggi un bit da "information_to_encode_bits" in modo circolare e decrementa "count"
                        # Caso a) Se il bit è 0, allora incrementa N
                        if information_to_encode_bits[i % len(information_to_encode_bits)] == "0":
                            N +=1
                        # Caso b)
                        elif (paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]/" + TEXT_ELEMENT_TAG)) != None:
                            txt_elem_tag = paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]/" + TEXT_ELEMENT_TAG)
                            text = txt_elem_tag.text
                            new_run_element = copy.copy(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]"))

                            # Step 12 -> Aggiungi o modifica l’attributo bmk al tag <a:rPr> usato come marker di split
                            new_run_element.find("./" + RUN_ELEMENT_PROPERTY_TAG).set(RPR_ATTRIBUTE_FOR_MARKER_SPLIT, (random_num_except(bmk_attr_val_prec)).__str__())

                            # Aggiungi un nuovo <r> e setta il tag <t>
                            txt_elem_tag.text = text[0:N]
                            new_run_element.find("./" + TEXT_ELEMENT_TAG).text = text[N:]
                            paragraph.insert(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]").getparent().index(paragraph.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_element).__str__() + "]")) + 1, new_run_element)
                            offset_run_element += 1
                            if len(text[N:]) == 0:  # anche se <a:t> è vuoto, il decoder lo ignora dall'estrazione
                                new_run_element.find("./" + TEXT_ELEMENT_TAG).text = ""
                            # optimization -> remove tree.write("stego/document.xml")
                            N = 1
                            count_txt_tag += 1
                        i += 1
                        count -= 1
                        # Step 13 -> Ritorna allo step 11 finché C è >= 1
                    index_run_element += 1
                    offset_run_element += 1
                    # Step 14 -> Ripeti dallo step 9 allo step 13 finché tutti gli elementi <a:r> in P non sono stati risolti
                # Step 15 -> Ripeti dallo step 7 allo step 14 finché tutti i paragrafi P non sono stati risolti
            # Step 16 -> Ripeti dallo step 5 allo step 15 finché tutti gli shape SP non sono stati risolti
        # Crea il file "slideX.xml" steganografato
        createSlideStego(tree, slide, output_stego_directory_path)
        # Step 17 -> Ripeti dallo step 4 allo step 16 finché non sono state considerate tutte le slide

    # Verifica se il file dato in input ha la capacità di contenere la rappresentazione in bit del testo segreto cifrato
    total_counter_inclusion = i
    total_complete_repeat_secret_text = total_counter_inclusion // len(information_to_encode_bits)  # numero di volte in cui il testo segreto è stato incapsulato
    # Se il numero di bit del cifrato da iniettare è superiore alla capacità del documento di ammettere lo split del contenuto testuale -> annulla codifica
    if len(information_to_encode_bits) > total_counter_inclusion:
        utils.remove_directory(os.path.split(path_file_extracted)[0])
        sys.exit("La capacità di inclusione del documento non è sufficiente per incapsulare il testo segreto!!\nFine!")

    # Stampa le statistiche in merito al numero di parole, inclusioni, bit da codificare e altro per il testing
    utils.printStatistics(total_counter_characters, total_counter_inclusion, information_to_encode_bits, total_complete_repeat_secret_text)
    count_txt_tag += count_txt_tag_base
    print("directory \"slides\" statistics: <a:t> di base: " + count_txt_tag_base.__str__() + "; dopo: " + count_txt_tag.__str__())

    # Crea il file ".pptx" contenente il testo segreto
    path_output_stego_file = createFileStego(path_file_extracted, output_stego_directory_path)
    print("Il file .pptx steganografato è stato salvato nella directory \"" + output_stego_directory_path + "\"")
    return path_output_stego_file
