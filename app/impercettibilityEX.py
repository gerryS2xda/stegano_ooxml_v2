import os
from lxml import etree
import copy

# Constant for XML SpreadSheetML element
PREFIX_EXCEL_PROC = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Constant for XML Worksheet
WORKSHEET_ROOT_TAG = PREFIX_EXCEL_PROC + "worksheet" # root element of sheetX.xml
SHEETDATA_TAG = PREFIX_EXCEL_PROC + "sheetData"
ROW_ELEMENT_TAG = PREFIX_EXCEL_PROC + "row"
CELL_ELEMENT_TAG = PREFIX_EXCEL_PROC + "c"
CELL_TYPEDATA_ATTRIBUTE = "t"
CELL_INDEXSTYLE_ATTRIBUTE = "s"
CELL_VALUE_ELEMENT_TAG = PREFIX_EXCEL_PROC + "v"

# Constant for XML Styles
STYLESHEET_ROOT_TAG = PREFIX_EXCEL_PROC + "styleSheet"
CELLXFS_ELEMENT_TAG = PREFIX_EXCEL_PROC + "cellXfs"
XF_ELEMENT_TAG = PREFIX_EXCEL_PROC + "xf"
XF_APPLYFONT_ATTRIBUTE = "applyFont"
XF_FONTID_ATTRIBUTE = "fontId"
FONTS_ELEMENT_TAG = PREFIX_EXCEL_PROC + "fonts"
FONT_ELEMENT_TAG = PREFIX_EXCEL_PROC + "font"
FONTNAME_STYLE_TAG = PREFIX_EXCEL_PROC + "name"

# Constant for XML Shared String Table
SHARED_STRING_TABLE_TAG = PREFIX_EXCEL_PROC + "sst" # root element of sharedStrings.xml
STRING_ITEM_TAG = PREFIX_EXCEL_PROC + "si"
RUN_ELEMENT_TAG = PREFIX_EXCEL_PROC + "r"
RUN_ELEMENT_PROPERTY_TAG = PREFIX_EXCEL_PROC + "rPr"
TEXT_TAG = PREFIX_EXCEL_PROC + "t"
FONTNAME_RPR_TAG = PREFIX_EXCEL_PROC + "rFont"
CHARSET_TAG = PREFIX_EXCEL_PROC + "charset"  # marker split tag

# Applicazione formattazione a livello di cella presente in styles.xml nella Shared String Table (sharedStrings.xml)
def apply_cell_styles_into_sst(path_file_xlsx_extracted, tree_sst_input):

    # LETTURA FILE XML INTERESSATI
    # Leggi il contenuto del file "styles.xml"
    tree_style = etree.parse(path_file_xlsx_extracted + "/xl/styles.xml")

    # Leggi il contenuto del file "sharedStrings.xml", se non viene già passato in input
    if tree_sst_input == None:
        tree_sst = etree.parse(path_file_xlsx_extracted + "/xl/sharedStrings.xml")
    else:
        tree_sst = tree_sst_input

    # Step 1 -> Estrai tutti i fogli di lavoro (sheetX.xml) dalla directory "worksheet" del workbook S
    sheets = os.listdir(path_file_xlsx_extracted + "/xl/worksheets")
    for sheet in sheets:  # Rimuovi tutti i nomi dei file che sono diversi da "slideX.xml"
        if sheet.find("sheet") == -1:
            sheets.remove(sheet)

    # Per ciascun sheet estratto
    for sheet in sheets:
        # Step 2 -> Leggi il contenuto del file XML indicato da "sheet"
        tree_sheet = etree.parse(path_file_xlsx_extracted + "/xl/worksheets/" + sheet)
        root = tree_sheet.getroot() # get <worksheet> element

        # Step 3 -> Posizionati nella sezione "Sheet Data" e ed estrai tutte le righe di celle (tag <row>)
        rows = root.findall("./" + SHEETDATA_TAG + "/" + ROW_ELEMENT_TAG)
        for row in rows: # per ciascun riga tra tutte quelle presenti nel sheet
            # Step 4 -> # Estrai tutte le celle presenti nella riga "row"
            cells = row.findall("./" + CELL_ELEMENT_TAG)
            i = -1
            for cell in cells: # per ciascuna cella tra tutte quelli presenti nella riga "row"
                i+=1
                # Verifica se la cella ammette come tipo di contenuto una shared string e se considera lo stile in styles.xml
                if cell.get(CELL_TYPEDATA_ATTRIBUTE) != "s":
                    continue
                if cell.get(CELL_INDEXSTYLE_ATTRIBUTE) == None:
                    continue
                # Step 5 -> Memorizza in una variabile il valore dell'attributo "s" (Index Style) di <c> e in un'altra il contenuto della cella in <v>
                cell_index_style_value = int(cell.get(CELL_INDEXSTYLE_ATTRIBUTE))
                cell_value = int(cell.find("./" + CELL_VALUE_ELEMENT_TAG).text) # estrae l'indice della string item (<si>) presente in SST

                # Step 6-7-8 -> Estrai la formattazione del contenuto testuale della cella sezionata presente in styles.xml
                font = extract_cell_style_from_styles_xmlfile(tree_style, cell_index_style_value)
                if font == None: # se alla cella selezionata non viene applicata la formattazione del contenuto testuale
                    continue # ... passa alla cella successiva

                # Step 9-10-11 -> Aggiungi la formattazione estratta al/ai run presenti nello string item della SST indicato dal valore di <v> della cella <c>
                apply_fontstyle_into_string_in_sst(tree_sst, cell_value, font)
            # Step 12 -> Ripeti dallo step 4 allo step 11 finché tutte le celle <c> nella riga "row" non sono state risolte
            i+=1
        # Step 13 -> Ripeti dallo step 3 allo step 12 finché tutte le righe "rows" utilizzate nel foglio di lavoro "sheet" non sono state risolte
    # Step 14 -> Ripeti dallo step 2 allo step 13 finché non sono stati esaminati tutti i fogli di lavoro presenti nella directory worksheet del xlsx steganografato

    if tree_sst_input == None: # se la SST non viene passata in input, scrivi la nuova SST nel file "sharedStrings.xml"
        tree_sst.write("stego/sharedStrings.xml")

    # Applicata la formattazione alla SST, restituisci il nuovo contenuto di "tree_sst" da scrivere poi in "sharedStrings.xml"
    return tree_sst

# Estrai la formattazione del contenuto testuale della cella sezionata presente in styles.xml, se presente
def extract_cell_style_from_styles_xmlfile(tree_style, cell_index_style_value):

    root_style = tree_style.getroot() # get <styleSheet> element

    # Step 7 -> Considera il tag <cellXfs> ed estrai tutti i suoi figli <xf> che descrivono formattazione delle celle
    xfs = root_style.findall("./" + CELLXFS_ELEMENT_TAG + "/" + XF_ELEMENT_TAG)

    # Step 8 -> Seleziona l'elemento <xf> indicato dall'attributo s di cella su cui si sta lavorando ed estrai lo style
    xf = xfs[cell_index_style_value]
    # Verifica se <xf> selezionato contiene l'attributo "applyFont" settato a 1
    if xf.get(XF_APPLYFONT_ATTRIBUTE) == None or xf.get(XF_APPLYFONT_ATTRIBUTE) != "1":
        return None # alla cella non viene applicata formattazione del contenuto testuale
    # Estrai tutti gli elementi figli di <font> e seleziona quello indicato dall'attributo "fontId" di <xf> selezionato
    fonts = root_style.findall("./" + FONTS_ELEMENT_TAG + "/" + FONT_ELEMENT_TAG)
    font = fonts[int(xf.get(XF_FONTID_ATTRIBUTE))]

    # Sostituisci il tag <name> con <rFont> per la compatibilità dello style con <rPr> (Run Property) della SST
    if font.find("./" + FONTNAME_STYLE_TAG) != None:
        font_name_val = font.find("./" + FONTNAME_STYLE_TAG).get("val")
        rfont_tag = etree.Element(FONTNAME_RPR_TAG)
        rfont_tag.set("val", font_name_val)
        font.replace(font.find("./" + FONTNAME_STYLE_TAG), rfont_tag)

    return font # Restituisci l'elemento <font> che contiene lo style della cella selezionata

# Aggiungi la formattazione estratta al/ai run presenti nello string item della SST indicato dal valore di <v> della cella <c>
def apply_fontstyle_into_string_in_sst(tree_sst, cell_value, font):

    root_sst = tree_sst.getroot() # get <sst> element

    # Step 10 -> Estrai tutti gli string item <si> presenti in <sst>
    string_items = root_sst.findall("./" + STRING_ITEM_TAG)

    # Step 11 -> Seleziona l'elemento <si> indicato dal contenuto della cella (tag <v>) dato in input
    string_item = string_items[cell_value]
    # Aggiungi il run (tag <r>) seguito dal testo e proprietà se non è presente in "string_item"
    if string_item.find("./" + RUN_ELEMENT_TAG) == None:
        text_tag_si = string_item.find("./" + TEXT_TAG)
        run_element = etree.Element(RUN_ELEMENT_TAG)
        rpr = etree.Element(RUN_ELEMENT_PROPERTY_TAG)
        run_element.insert(0, rpr)  # aggiungi tag <rPr> in prima posizione prima di altri tag altrimenti non vengono applicate le proprietà
        run_element.append(text_tag_si)
        string_item.append(run_element)
    # Altrimenti, per ciascun run (tag <r>) presente nel <si> selezionato...
    # ... aggiungi il contenuto dell'elemento <font> estratto da style nelle proprietà del run (<rPr)
    run_elements = string_item.findall("./" + RUN_ELEMENT_TAG) # Estrai tutti i run presenti in "string_item"...
    font_children_tags = font.getchildren()  # prendi tutti gli elementi figli di <font>...
    for run in run_elements: # ... per ciascun run
        for element_tag in font_children_tags:  # ... aggiungi i figli di "font", se non sono presenti
            if run.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + element_tag.tag) == None:
                run.find("./" + RUN_ELEMENT_PROPERTY_TAG).append(element_tag)
        new_run = copy.copy(run) # usa la copia per risolvere problema di non modifica dei riferimenti (distacca run modificato da "string_item")
        string_item.replace(run, new_run) # rimpiazza il run corrente nel "string_item" con il nuovo run
