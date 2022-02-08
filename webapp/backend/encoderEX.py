import os
import shutil
import zipfile
import sys
from lxml import etree
import copy
from backend import utils, impercettibilityEX

#Constant for XML SpreadSheetML element
PREFIX_EXCEL_PROC = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SHARED_STRING_TABLE_TAG = PREFIX_EXCEL_PROC + "sst" #root element
STRING_ITEM_TAG = PREFIX_EXCEL_PROC + "si"
RUN_ELEMENT_TAG = PREFIX_EXCEL_PROC + "r"
RUN_ELEMENT_PROPERTY_TAG = PREFIX_EXCEL_PROC + "rPr"
TEXT_TAG = PREFIX_EXCEL_PROC + "t"
CHARSET_TAG = PREFIX_EXCEL_PROC + "charset"  #marker split tag

# Assegna gli interi 3 e 4 alternati all'attributo "val" di <charset> sulla base del valore attuale
def set_charset_value(val_prec):
    if val_prec == 3:
        return 4
    return 3

# Merge di tutti i possibili "run element" che presentano le stesse caratteristiche (numero elementi XML figli)
def merge_possible_run_elements(string_item):
     run_property_elements = []
     #Cerca gli "run element property" (<rPr>) nel paragrafo e memorizzali in un array
     for node in string_item.findall("./" + RUN_ELEMENT_TAG + "/" + RUN_ELEMENT_PROPERTY_TAG):
         if node.getparent().find("./" + TEXT_TAG) != None:
             run_property_elements.append(node)
     i = 0
     for node in run_property_elements:
        mismatch = False
        j = i + 1
        #check sul numero degli elementi. Se non hanno lo stesso numero di elementi -> no merge
        if j < len(run_property_elements) and len(run_property_elements[i]) != len(run_property_elements[j]):
            continue

        # Merge dei possibili "Run element" sulla base degli elementi presenti in ciascun <rPr>
        while mismatch != True and j < len(run_property_elements):
            for child_of_node in node:
                child_of_node_j = run_property_elements[j].find("./" + child_of_node.tag)
                if child_of_node_j == None or (child_of_node.tag != CHARSET_TAG and (len(child_of_node_j.keys()) != len(child_of_node.keys()))):
                    mismatch = True
                    break
            #merge nodi fino al j - 1 elemento
            if mismatch == True:
                x = i + 1
                while x < j:
                    #append node i + 1 to base node
                    node = string_item.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if node == None: # se il base_node non ha il text element, esci dal ciclo
                        break
                    base_node = string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if base_node == None: # se il base_node non ha il text element, esci dal ciclo
                        break
                    base_node.text = base_node.text + node.text
                    x += 1
                x = i + 1
                while x < j:
                    #rimuovo elemento successivo al nodo merge
                    run_property_elements.remove(run_property_elements[i + 1])
                    string_item.remove(string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 2).__str__() + "]"))
                    x += 1
            #se sono arrivato alla fine dei nodi del paragrafo --> tutti i nodi hanno gli stessi attributi
            elif (j == len(run_property_elements) - 1):
                x = i + 1
                while x <= j:
                    #append  node i + 1 to base node
                    node = string_item.find("./" + RUN_ELEMENT_TAG + "[" + (x + 1).__str__() + "]" + "/" + TEXT_TAG)
                    if node == None:
                        break
                    #NEW DA TESTARE COMPLETO
                    if string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG) == None:
                        string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]").append(etree.Element(TEXT_TAG))
                        string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG).text = node.text
                    else:
                        base_node = string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 1).__str__() + "]" + "/" + TEXT_TAG)
                        base_node.text = base_node.text + node.text
                    x += 1
                x = i + 1
                while x <= j:
                    #rimuovo elemento successivo al nodo merge
                    run_property_elements.remove(run_property_elements[i + 1])
                    string_item.remove(string_item.find("./" + RUN_ELEMENT_TAG + "[" + (i + 2).__str__() + "]"))
                    x += 1
            else:
                j += 1

        if j == len(run_property_elements):
            break
        i +=1

# Verifica se vi è spazio per effettuare un'altra iniezione nel run corrente di base
def check_if_available_space(index, string_item, information_to_encode_bits, offset_run_elem, count, charset_val):
    count_zero = 0
    j = index
    while information_to_encode_bits[j % len(information_to_encode_bits)] == "0":
        j += 1
        count_zero += 1
    if count < count_zero + 1:
        node = string_item.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]")
        charset_tag = node.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG)
        if charset_tag != None:
            charset_val_actual = int(charset_tag.get("val")) # leggi il "val" di charset dell'ultimo nuovo "run"
            if(charset_val_actual != charset_val): # se il valore attuale di "val" è diverso da quello atteso, mantieni il valore attuale
                charset_val = charset_val_actual    # ... necessario perché il charset dell'ultimo nuovo "run" potrebbe avere il valore già corretto
            node.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG).set("val", charset_val.__str__())
        else:
            etree.SubElement(node.find("./" + RUN_ELEMENT_PROPERTY_TAG), CHARSET_TAG)
            node.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG).set("val", charset_val.__str__())
        return False
    return True

# Crea il file ".xlsx" contenente "sharedStrings.xml" steganografato
def createFileStego(tree, path_file_extracted, output_stego_directory_path):
    input_file_name = os.path.splitext(os.path.split(os.path.split(path_file_extracted)[0])[1])[0]  # no estensione file
    tree.write(output_stego_directory_path + "/sharedStrings.xml")
    shutil.copytree(path_file_extracted, output_stego_directory_path + "/file_extracted")
    shutil.copy(output_stego_directory_path + "/sharedStrings.xml", output_stego_directory_path + "/file_extracted/xl")
    zf = zipfile.ZipFile(output_stego_directory_path + "/stego.zip", "w", zipfile.ZIP_DEFLATED)
    for dirname, subdirs, files in os.walk(output_stego_directory_path + "/file_extracted"):
        for filename in files:
            path = ""
            if dirname == (output_stego_directory_path + "/file_extracted"):
                path = filename
            else:
                path = dirname.split(output_stego_directory_path + "/file_extracted")[1] + "/" + filename
            zf.write(os.path.join(dirname, filename), path)
    zf.close()
    # Check if file exists before to rename zip file
    if os.path.exists(output_stego_directory_path + '/' + input_file_name + '_stego.xlsx'):
        os.remove(output_stego_directory_path + '/' + input_file_name + '_stego.xlsx')
    os.rename(output_stego_directory_path + '/stego.zip', output_stego_directory_path + '/' + input_file_name + '_stego.xlsx')
    os.remove(output_stego_directory_path + '/sharedStrings.xml')
    shutil.rmtree(output_stego_directory_path + '/file_extracted')

    path_output_stego_file = output_stego_directory_path + '/' + input_file_name + '_stego.xlsx'
    return path_output_stego_file

# Applicazione del metodo dello split in cui si incapsula il testo segreto in binario in "sharedStrings.xml" usando string item e run element
def encoding(message, password, path_file_extracted, output_stego_directory_path):
    # Step 1 -> Leggi il codice dal file "xl/sharedStrings.xml", relativo al workbook D
    tree = etree.parse(path_file_extracted + '/xl/sharedStrings.xml')
    root = tree.getroot()

    # Step 2 -> Cifra il testo segreto H mediante l’algoritmo AES-CBC, usando la chiave simmetrica
    encrypted = utils.encrypt(password, message)
    print("TESTO SEGRETO CIFRATO: " + encrypted.__str__())

    # Step 3 -> Aggiungi alla fine del testo cifrato il carattere di divisione "%"
    information_to_encode_bits = utils.text_to_binary(encrypted.decode('utf-8')) + utils.text_to_binary(
        utils.MAGIC_CHAR_SPLIT)

    # Inizializzazione di un contatore di caratteri e di inclusione
    total_counter_characters = 0
    total_counter_inclusion = 0
    count_txt_tag_base = 0 # for testing
    count_txt_tag = 0 # for testing
    print("INIEZIONE IN CORSO .....")

    # Step 4 -> Estrai tutti gli string item <si> presenti in P
    string_items = root.findall("./" + STRING_ITEM_TAG)
    i = 0
    for si in string_items:
        charset_val = 3
        # Step 5 - > IF (<si> in P non è seguito da <r>) THEN aggiungilo
        if si.find("./" + RUN_ELEMENT_TAG) == None:
            text_tag_si = si.find("./" + TEXT_TAG)
            run_element = etree.Element(RUN_ELEMENT_TAG)
            charset_tag = etree.Element(CHARSET_TAG)
            charset_tag.set("val", charset_val.__str__())
            rpr = etree.Element(RUN_ELEMENT_PROPERTY_TAG)
            rpr.append(charset_tag)
            run_element.insert(0, rpr) # aggiungi tag <rPr> in prima posizione prima di altri tag altrimenti non vengono applicate le proprietà
            run_element.append(text_tag_si)
            si.append(run_element)

        # Step 6 -> IF (2 o più elementi <r> consecutivi in P hanno gli stessi attributi) THEN unisci gli elementi consecutivi <r>.;
        merge_possible_run_elements(si)

        # Step 7 -> Estrai elemento <r> in R e i corrispondenti "text element" <t> in T
        run_elements = si.findall("./" + RUN_ELEMENT_TAG)

        # Inizializzazione contatori per tenere traccia dei run
        index_run_element = 1
        offset_run_elem = 1  # run da saltare rispetto a quelli di base correnti

        while index_run_element <= len(run_elements):
            # Considera solo i run con il text element
            if run_elements[index_run_element-1].find("./" + TEXT_TAG) == None:
                index_run_element +=1
                offset_run_elem += 1
                continue
            count_txt_tag_base += 1

            # Computa valore da assegnare all'attributo "val" di <charset> usato come marker split
            charset_val = set_charset_value(charset_val)

            # Step 8 -> Inizializza il contatore N=1 per accumulare il numero di caratteri da dividere.
            # Successivamente, conta il numero di caratteri in T e memorizzali nella variabile C.
            N = 1
            txt_elem_tag = run_elements[index_run_element - 1].find("./" + TEXT_TAG)
            count = len(txt_elem_tag.text)
            total_counter_characters += count

            # Se il run element corrente non contiene tag <rPr>, si crea e aggiunge tale tag
            if run_elements[index_run_element - 1].find("./" + RUN_ELEMENT_PROPERTY_TAG) == None:
                rpr = etree.Element(RUN_ELEMENT_PROPERTY_TAG)
                rpr.append(etree.Element(CHARSET_TAG))
                rpr.find("./" + CHARSET_TAG).set("val", charset_val.__str__())
                run_elements[index_run_element - 1].insert(0, rpr) # aggiungi tag <rPr> prima del testo
            # Altrimenti, se non contiene il tag <charset> usato come marker di split -> aggiungilo a <rPr>
            elif run_elements[index_run_element - 1].find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG) == None:
                    run_elements[index_run_element - 1].find("./" + RUN_ELEMENT_PROPERTY_TAG).append(etree.Element(CHARSET_TAG))
                    run_elements[index_run_element - 1].find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG).set("val", charset_val.__str__())
            else: # Se già contiene il tag <charset>, leggi il suo "val" e usalo per aggiornare il prossimo
                charset_val = int(run_elements[index_run_element - 1].find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG).get("val"))

            while count >= 1:
                charset_val = set_charset_value(charset_val)
                # Check if enough space to inject information coded remain
                if(check_if_available_space(i, si, information_to_encode_bits, offset_run_elem, count, charset_val) == False):
                    break

                # Step 10 -> Leggi un bit da "information_to_encode_bits" in modo circolare e decrementa "count"
                # Caso a) Se il bit è 0, allora incrementa N
                if(information_to_encode_bits[i % len(information_to_encode_bits)]) == "0":
                    N += 1
                # Caso b)
                elif si.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]" + "/" + TEXT_TAG) != None:
                    txt_elem_tag = si.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]" + "/" + TEXT_TAG)
                    text = txt_elem_tag.text
                    new_run_elem = copy.copy(si.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]"))

                    # Step 11 -> Aggiungi o modifica il marker di split rappresentato dal tag <charset> con il relativo attributo val posto come figlio del tag <rPr>.
                    charset_tag = new_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG)
                    if charset_tag != None:
                        charset_val_old = int(charset_tag.get("val")) # il nuovo run viene copiato dal precedente e quindi occorre modificato il "val" di charset se presente
                        new_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG).set("val", set_charset_value(charset_val_old).__str__())
                    else: # Aggiungi tag <charset> all'elemento <rPr>
                        new_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG).insert(1, etree.Element(CHARSET_TAG))
                        new_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG).set("val", charset_val.__str__())

                    txt_elem_tag.text = text[0:N]
                    new_run_elem.find("./" + TEXT_TAG).text = text[N:]

                    # Aggiungi l'attributo "xml:space = preserve" per preservare lo spazio nel tag <t>
                    txt_elem_tag.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    new_run_elem.find("./" + TEXT_TAG).set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

                    # Aggiungi un nuovo <r> e setta il tag <t>
                    si.insert(si.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]").getparent().index(si.find("./" + RUN_ELEMENT_TAG + "[" + (offset_run_elem).__str__() + "]")) + 1, new_run_elem)
                    offset_run_elem += 1
                    if len(text[N:]) == 0: # anche se <t> è vuoto, il decoder lo ignora dall'estrazione
                        new_run_elem.find("./" + TEXT_TAG).text = ""

                    N = 1
                    count_txt_tag += 1
                i += 1
                count -= 1
                # Step 11 -> Ritorna allo step 9 finché C è >= 1
            index_run_element += 1
            offset_run_elem += 1
            # Step 12 -> Ripeti dallo step 7 allo step 11 finché tutti gli elementi <r> in P non sono stati risolti
        # Step 13 -> Ripeti dallo step 4 allo step 12 finché tutti gli "string item" in P non sono stati risolti
    # Verifica se il file dato in input ha la capacità di contenere la rappresentazione in bit del testo segreto cifrato
    total_counter_inclusion = i
    total_complete_repeat_secret_text = total_counter_inclusion // len(information_to_encode_bits)  # numero di volte in cui il testo segreto è stato incapsulato
    # Se il numero di bit del cifrato da iniettare è superiore alla capacità del documento di am-mettere lo split del contenuto testuale -> annulla codifica
    if len(information_to_encode_bits) > total_counter_inclusion:
        utils.remove_directory(os.path.split(path_file_extracted)[0])
        sys.exit("La capacità di inclusione del documento non è sufficiente per incapsulare il testo segreto!!\nFine!")

    # Stampa le statistiche in merito al numero di parole, inclusioni, bit da codificare e altro per il testing
    utils.printStatistics(total_counter_characters, total_counter_inclusion, information_to_encode_bits, total_complete_repeat_secret_text)
    count_txt_tag += count_txt_tag_base
    print("sharedStrings.xml statistics: <t> di base: " + count_txt_tag_base.__str__() + "; dopo: " + count_txt_tag.__str__())

    # Prima di creare il file steganografato, aggiungi la formattazione delle celle usate dalla tabella (se presente) alla SST per fixare parte dell'impercettibilità
    tree_sst = impercettibilityEX.apply_cell_table_style_into_sst(path_file_extracted, tree)
    # Aggiungi la formattazione a livello di cella presente in styles.xml alla SST per fixare l'impercettibilità
    tree_sst = impercettibilityEX.apply_cell_styles_into_sst(path_file_extracted, tree_sst)

    # Crea il file steganografato
    path_output_stego_file = createFileStego(tree_sst, path_file_extracted, output_stego_directory_path)
    print("Il file .xlsx steganografato è stato salvato nella directory \"" + output_stego_directory_path + "\"")
    return path_output_stego_file
