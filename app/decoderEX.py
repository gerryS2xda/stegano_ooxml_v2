from lxml import etree
from app import utils

#Constant for XML SpreadSheetML element
PREFIX_EXCEL_PROC = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SHARED_STRING_TABLE_TAG = PREFIX_EXCEL_PROC + "sst" #root element
STRING_ITEM_TAG = PREFIX_EXCEL_PROC + "si"
RUN_ELEMENT_TAG = PREFIX_EXCEL_PROC + "r"
RUN_ELEMENT_PROPERTY_TAG = PREFIX_EXCEL_PROC + "rPr"
TEXT_TAG = PREFIX_EXCEL_PROC + "t"
CHARSET_TAG = PREFIX_EXCEL_PROC + "charset"  #marker split tag

# Esecuzione algoritmo di decodifica che estrae e decifra il testo segreto cifrato presente nel file steganografato S dato in input
def decoding(password, path_file_extracted):
    message = ""
    # Step 1 -> Leggi il codice dal file "xl/sharedStrings.xml" relativo al workbook S
    tree = etree.parse(path_file_extracted + '/xl/sharedStrings.xml')
    root = tree.getroot() # get <sst> element

    # Step 2 -> Estrai un "string item" <si> alla volta
    string_items = root.findall("./" + STRING_ITEM_TAG)
    i = 0
    for si in string_items:
        # Step 3 -> Estrai un elemento run <r>⋯ </r> in R e l'elemento di testo <t>⋯ </t> dell’elemento R in T.
        run_elements = si.findall("./" + RUN_ELEMENT_TAG)
        i_run_elements = 0
        while i_run_elements < len(run_elements):
            curr_run_elem = run_elements[i_run_elements]
            mismatch = False
            charset_tag = curr_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + CHARSET_TAG)
            if ((i_run_elements + 1) < len(run_elements)) and (charset_tag != None) and (charset_tag.get("val") != "0"): # nella codifica si considera solo i charset con "val" diverso da 0
                next_run_elem = run_elements[i_run_elements + 1]
                curr_property_elements = curr_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG)
                # check if tag RPR is present
                if curr_property_elements != None:
                    # step 5 -> Confronta gli attributi dell’elemento R con il suo successore R+1
                    next_run_property_elements = next_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG)
                    for child_curr_property_elem in curr_property_elements:
                        child_next_property_elem = next_run_property_elements.find("./" + child_curr_property_elem.tag)
                        # mismatch
                        if (child_next_property_elem == None) or ((child_curr_property_elem.tag != CHARSET_TAG) and (len(child_next_property_elem.keys()) != len(child_curr_property_elem.keys()))):
                            mismatch = True
                            break

                # case (A) -> if they have same attributes except the splitting mark, record the number of characters in the current text element to K, and add K-1 "0" to M (message) and "1" at the end
                if (mismatch == False) and (curr_run_elem.find("./" + TEXT_TAG).text != None):
                    text_tag = curr_run_elem.find("./" + TEXT_TAG).text
                    message += ("0" * (len(text_tag) - 1))
                    message += "1"
                # case (B) -> record the number of characters in the current text element to K, and add K-1 "0" to M (message)
                elif curr_run_elem.find("./" + TEXT_TAG).text != None:
                    text_tag = curr_run_elem.find("./" + TEXT_TAG).text
                    message += ("0" * (len(text_tag) - 1))

            # Step 6 -> Ripeti dallo step 3 allo step 5 finché tutti gli elementi <r> in P non sono stati risolti
            i_run_elements += 1
        # Step 7 -> Ripeti dallo step 2 allo step 6 finché tutti gli "string item"in P non sono stati risolti

    #step 8 -> Estrai il testo segreto H da M.
    string_enc = "".join(chr(int("".join(map(str, message[i:i+8])), 2)) for i in range(0, len(message), 8))
    split_duplicate = string_enc.split(utils.MAGIC_CHAR_SPLIT)
    print("TESTO DECIFRATO: ")
    for p in split_duplicate:
        try:
            print(utils.decrypt(password, p))
        except:
            print("una duplicazione del testo segreto non può essere decifrata poichè incompleta --> " + p)
            continue
