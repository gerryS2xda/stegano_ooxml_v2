from lxml import etree
from app import utils
import os

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

# Esecuzione algoritmo di decodifica che estrae e decifra il testo segreto cifrato presente nel file steganografato S dato in input
def decoding(password, path_file_extracted):
    message = ""
    # Step 1 -> Per ciascuna slide presente nella directory "ppt/slides" della presentazione steganografata S
    slides = os.listdir(path_file_extracted + "/ppt/slides")
    for slide in slides:  # Rimuovi tutti i nomi dei file che sono diversi da "slideX.xml"
        if slide.find("slide") == -1:
            slides.remove(slide)

    for slide in slides:
        print("Estrazione testo segreto da " + slide + "...")
        # Step 2 -> Leggi il codice dal file "slides/slideX.xml", relativo al presentazione steganografata S
        tree = etree.parse(path_file_extracted + "/ppt/slides/" + slide)
        root = tree.getroot() #get <p:sld> element

        # Step 3 -> Estrai tutti gli shape <p:sp> presenti in SP
        shapes = root.findall("./" + CONTENT_SLIDE_TREE_TAG + "/" + SHAPE_TREE_TAG + "/" + SHAPE_TAG)
        for shape in shapes:
            # Step 4 -> Verifica se shape contiene un txBody tag
            txBody = shape.find("./" + TEXT_BODY_TAG)
            if txBody == None:
                continue

            # Step 5 -> Estrai paragrafo <a:p> in P
            paragraphs = txBody.findall("./" + PARAGRAPH_TAG)
            for paragraph in paragraphs:
                # Step 6 -> Estrai un elemento run <a:r> in R e considera solo quelli con il text element <a:t> ponendoli in T.
                run_elements = paragraph.findall("./" + RUN_ELEMENT_TAG)

                i_run_elements = 0
                while i_run_elements < len(run_elements):
                    curr_run_elem = run_elements[i_run_elements]
                    if curr_run_elem.find("./" + TEXT_ELEMENT_TAG) == None:  # estrai soltanto quei run che hanno un text element
                        i_run_elements += 1
                        continue

                    mismatch = False
                    bmk_attr_rPr_tag = curr_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG).get(RPR_ATTRIBUTE_FOR_MARKER_SPLIT)
                    if ((i_run_elements + 1) < len(run_elements)) and (bmk_attr_rPr_tag != None) and (bmk_attr_rPr_tag != "0"):
                        next_run_elem = run_elements[i_run_elements + 1]
                        curr_property_elements = curr_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG)
                        # check if tag RPR is present
                        if curr_property_elements != None:
                            # Step 8 -> Confronta gli attributi dell’elemento R e suoi relativi figli con il suo successore R+1 e suoi relativi figli
                            next_run_property_elements = next_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG)
                            if len(curr_property_elements.keys()) == len(next_run_property_elements.keys()):
                                for child_curr_property_elem in curr_property_elements:
                                    child_next_property_elem = next_run_property_elements.find("./" + child_curr_property_elem.tag)
                                    # mismatch
                                    if (child_next_property_elem == None) or (len(child_next_property_elem.keys()) != len(child_curr_property_elem.keys())):
                                        mismatch = True
                                        break
                            else:
                                mismatch = True

                        # case (A) -> if they have same attributes except the splitting mark, record the number of characters in the current text element to K, and add K-1 "0" to M (message) and "1" at the end
                        if (mismatch == False) and (curr_run_elem.find("./" + TEXT_ELEMENT_TAG).text != None):
                            text_tag = curr_run_elem.find("./" + TEXT_ELEMENT_TAG).text
                            message += ("0" * (len(text_tag) - 1))
                            message += "1"
                        # case (B) -> record the number of characters in the current text element to K, and add K-1 "0" to M (message)
                        elif curr_run_elem.find("./" + TEXT_ELEMENT_TAG).text != None:
                            text_tag = curr_run_elem.find("./" + TEXT_ELEMENT_TAG).text
                            message += ("0" * (len(text_tag) - 1))
                    # Step 9 -> Ripeti dallo step 6 allo step 8 finché tutti gli elementi <a:r> in P non sono stati risolti
                    i_run_elements += 1
                # Step 10 -> Ripeti dallo step 5 allo step 9 finché tutti i paragrafi P non sono stati risolti
            # Step 11 -> Ripeti dallo step 3 allo step 9 finché tutti gli shape SP non sono stati risolti.
        # Step 12 -> Ripeti dallo step 2 allo step 11 finché non sono state considerate tutte le slide

    #step 13 -> Estrai il testo segreto H da M.
    string_enc = "".join(chr(int("".join(map(str, message[i:i+8])), 2)) for i in range(0, len(message), 8))
    split_duplicate = string_enc.split(utils.MAGIC_CHAR_SPLIT)
    print("TESTO DECIFRATO: ")
    for p in split_duplicate:
        try:
            print(utils.decrypt(password, p))
        except:
            print("Una duplicazione del testo segreto non può essere decifrata poichè incompleta --> " + p)
            continue
