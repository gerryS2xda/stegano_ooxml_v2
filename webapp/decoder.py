from lxml import etree
from webapp import utils

#CONSTS
PREFIX_WORD_PROC = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PARAGRAPH_TAG = PREFIX_WORD_PROC + "p"
RUN_ELEMENT_TAG = PREFIX_WORD_PROC + "r"
RUN_ELEM_PROPERTY_TAG = PREFIX_WORD_PROC + "rPr"
BODY_TAG = PREFIX_WORD_PROC + "body"
TEXT_TAG = PREFIX_WORD_PROC + "t"
SZCS_TAG = PREFIX_WORD_PROC + "szCs"


def decoding(password):
    message = ""
    tree = etree.parse('stego/file_extracted/word/document.xml')
    root = tree.getroot()

    paragraphs = root.findall("./" + BODY_TAG + "/" + PARAGRAPH_TAG)
    #step 3 ->Estrai paragrafo <w:p> in P;
    for paragraph in paragraphs:
        #step 4 -> extract a run element <w:r> ... </w:r> to R, and the text element <w:t> ... </w:t> in the run element to T
        run_elements = paragraph.findall("./" + RUN_ELEMENT_TAG)
        i_run_elements = 0
        while i_run_elements < len(run_elements):
            curr_run_elem = run_elements[i_run_elements]
            #print(curr_run_elem.find("./" + TEXT_TAG).text)
            mismatch = False
            if i_run_elements + 1 < len(run_elements) and curr_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG) != None and curr_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + SZCS_TAG).get(PREFIX_WORD_PROC + "val") != "0":
                next_run_elem = run_elements[i_run_elements + 1]
                j = i_run_elements + 1
                curr_property_elements = curr_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG)
                # check if tag RPR is empty
                #step 6 -> Confronta gli attributi dell’elemento R con il suo successore R+1
                if curr_property_elements != None:
                    for child_curr_property_elem in curr_property_elements:
                        child_next_property_elem = next_run_elem.find("./" + RUN_ELEM_PROPERTY_TAG + "/" + child_curr_property_elem.tag)
                        # mismatch
                        if child_next_property_elem == None  or (child_curr_property_elem.tag != SZCS_TAG and child_next_property_elem.attrib != child_curr_property_elem.attrib) == True:
                            mismatch=True
                            break
                # case (A) -> if they have same attributes except the splitting mark, record the number of characters in the current text element to K, and add K-1 "0" to M (message) and "1" at the end
                if(mismatch == False and curr_run_elem.find("./" + TEXT_TAG).text != None):
                    text_tag = curr_run_elem.find("./" + TEXT_TAG).text
                    message += ("0" * (len(text_tag) -1 ))
                    message += ("1")
                # case (B) -> record the number of characters in the current text element to K, and add K-1 "0" to M (message)
                elif curr_run_elem.find("./" + TEXT_TAG).text != None:
                    text_tag = curr_run_elem.find("./" + TEXT_TAG).text
                    message += ("0" * (len(text_tag) - 1))

        #step 6 -> repeat step 2 to step 5 until all paragraph elements have been addressed
            i_run_elements += 1

    #step 11 -> Estrai il testo segreto H da M.
    string_enc = "".join(chr(int("".join(map(str,message[i:i+8])),2)) for i in range(0,len(message),8))
    split_duplicate = string_enc.split(utils.MAGIC_CHAR_SPLIT)
    string_dec = ""
    for p in split_duplicate:
        try:
            string_dec += utils.decrypt(password, p).decode('utf-8')
        except:
            #print("l'ultima duplicazione del testo segreto non può essere decifrata poichè incompleta --> " + p)
            continue
    return string_dec










