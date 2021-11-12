from lxml import etree
from app import utils

#Constant for XML WordProcessing element
PREFIX_WORD_PROC = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PARAGRAPH_TAG = PREFIX_WORD_PROC + "p"
RUN_ELEMENT_TAG = PREFIX_WORD_PROC + "r"
RUN_ELEM_PROPERTY_TAG = PREFIX_WORD_PROC + "rPr"
BODY_TAG = PREFIX_WORD_PROC + "body"
TEXT_TAG = PREFIX_WORD_PROC + "t"
SZCS_TAG = PREFIX_WORD_PROC + "szCs"

def decoding(password, path_filename_to_extract):
    message = ""
    # Step 1 -> Leggi il codice dal file "document.xml", relativo al documento D
    tree = etree.parse(path_filename_to_extract)
    root = tree.getroot()

    # Step 2 -> Estrai un paragrafo <w:p> in P alla volta
    paragraphs = root.findall("./" + BODY_TAG + "/" + PARAGRAPH_TAG)
    for paragraph in paragraphs:
        # Step 3 -> Estrai un elemento run <w:r>⋯ </w:r> in R e l'elemento di testo <w:t>⋯ </w:t> dell’elemento R in T.
        run_elements = paragraph.findall("./" + RUN_ELEMENT_TAG)
        i_run_elements = 0
        while i_run_elements < len(run_elements):
            curr_run_elem = run_elements[i_run_elements]
            mismatch = False
            if i_run_elements + 1 < len(run_elements) and curr_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) != None and curr_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).get(PREFIX_WORD_PROC + "val") != "0":
                next_run_elem = run_elements[i_run_elements + 1]
                curr_property_elements = curr_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG)
                # check if tag RPR is empty
                if curr_property_elements != None:
                    # Step 5 -> Confronta gli attributi dell’elemento R con il suo successore R+1
                    for child_curr_property_elem in curr_property_elements:
                        child_next_property_elem = next_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + child_curr_property_elem.tag)
                        # mismatch
                        if child_next_property_elem == None  or (child_curr_property_elem.tag != SZCS_TAG and (len(child_next_property_elem.keys()) != len(child_curr_property_elem.keys()))):
                            mismatch = True
                            break
                # case (A) -> if they have same attributes except the splitting mark, record the number of characters in the current text element to K, and add K-1 "0" to M (message) and "1" at the end
                if(mismatch == False and curr_run_elem.find("./" + TEXT_TAG).text != None):
                    text_tag = curr_run_elem.find("./" + TEXT_TAG).text
                    message += ("0" * (len(text_tag) -1 ))
                    message += "1"
                # case (B) -> record the number of characters in the current text element to K, and add K-1 "0" to M (message)
                elif curr_run_elem.find("./" + TEXT_TAG).text != None:
                    text_tag = curr_run_elem.find("./" + TEXT_TAG).text
                    message += ("0" * (len(text_tag) - 1))

            # Step 6 -> Ripeti dallo step 3 allo step 5 finché tutti gli elementi <r> in P non sono stati risolti
            i_run_elements += 1
        # Step 7 -> Ripeti dallo step 2 allo step 6 finché tutti i paragrafi in P non sono stati risolti

    # Step 8 -> Estrai il testo segreto H da M.
    string_enc = "".join(chr(int("".join(map(str, message[i:i+8])), 2)) for i in range(0, len(message), 8))
    split_duplicate = string_enc.split(utils.MAGIC_CHAR_SPLIT)
    print("TESTO DECIFRATO: ")
    for p in split_duplicate:
        try:
            print(utils.decrypt(password, p))
        except:
            print("una duplicazione del testo segreto non può essere decifrata poichè incompleta --> " + p)
            continue

#Main
if __name__ == '__main__':
    path_filename_to_extract = "stego/document.xml"
    password = input("inserisci la password per decifrare il testo: ")

    decoding(password, path_filename_to_extract)

    exit(0)









