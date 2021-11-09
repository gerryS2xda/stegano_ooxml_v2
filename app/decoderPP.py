from lxml import etree
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


def decoding(password, path_filename_to_extract):
    message = ""
    #Step 1 -> Leggi il codice dal file "slides/slide1.xml", relativo al documento steganografato S
    tree = etree.parse(path_filename_to_extract)
    root = tree.getroot() #get <p:sld> element

    #Step 2 -> Estrai tutti gli shape <p:sp> presenti in SP
    shapes = root.findall("./" + CONTENT_SLIDE_TREE_TAG + "/" + SHAPE_TREE_TAG + "/" + SHAPE_TAG)
    for shape in shapes:
        #Step 3 -> Verifica se shape contiene un txBody tag
        txBody = shape.find("./" + TEXT_BODY_TAG)
        if txBody == None:
            continue

        #Step 4 -> Estrai paragrafo <a:p> in P
        paragraphs = txBody.findall("./" + PARAGRAPH_TAG)
        for paragraph in paragraphs:
            #Step 5 -> 	Estrai un elemento run <a: r>⋯ </ a: r> in R e l'elemento di testo <a: t>⋯ </ a: t> dell’elemento R in T.
            run_elements = paragraph.findall("./" + RUN_ELEMENT_TAG)
            i_run_elements = 0
            while i_run_elements < len(run_elements):
                curr_run_elem = run_elements[i_run_elements]
                mismatch = False
                bmk_attr_rPr_tag = curr_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG).get(RPR_ATTRIBUTE_FOR_MARKER_SPLIT)
                if ((i_run_elements + 1) < len(run_elements)) and (bmk_attr_rPr_tag != None) and (bmk_attr_rPr_tag != "0"):
                    next_run_elem = run_elements[i_run_elements + 1]
                    j = i_run_elements + 1
                    curr_property_elements = curr_run_elem.find("./" + RUN_ELEMENT_PROPERTY_TAG)
                    # check if tag RPR is present
                    if curr_property_elements != None:
                        # step 7 -> Confronta gli attributi dell’elemento R e suoi relativi figli con il suo successore R+1 e suoi relativi figli
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

            #step 6 -> repeat step 2 to step 5 until all paragraph elements have been addressed
                i_run_elements += 1

    #step 11 -> Estrai il testo segreto H da M.
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
    path_filename_to_extract = "stego/slide1.xml"
    password = input("inserisci la password per decifrare il testo: ")

    decoding(password, path_filename_to_extract)

    exit(0)









