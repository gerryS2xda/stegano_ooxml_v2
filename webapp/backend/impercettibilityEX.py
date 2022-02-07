import os
from lxml import etree
import copy
from webapp.backend import utils

# External XML file to load (necessario path completo perche' os.cwd = "/webapp")
PRESET_TABLE_STYLE_XML_FILE_PATH = "./backend/external_xml/presetTableStyles.xml"

# Constant for XML SpreadSheetML element
PREFIX_EXCEL_PROC = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PREFIX_RELATIONSHIP_EXCEL_NAMESPACE = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL_ID_ATTRIBUTE = PREFIX_RELATIONSHIP_EXCEL_NAMESPACE + "id"

# Constant for XML Worksheet
WORKSHEET_ROOT_TAG = PREFIX_EXCEL_PROC + "worksheet" # root element of sheetX.xml
SHEETDATA_TAG = PREFIX_EXCEL_PROC + "sheetData"
ROW_ELEMENT_TAG = PREFIX_EXCEL_PROC + "row"
CELL_ELEMENT_TAG = PREFIX_EXCEL_PROC + "c"
CELL_TYPEDATA_ATTRIBUTE = "t"
CELL_INDEXSTYLE_ATTRIBUTE = "s"
CELL_VALUE_ELEMENT_TAG = PREFIX_EXCEL_PROC + "v"
TABLEPARTS_ELEMENT_TAG = PREFIX_EXCEL_PROC + "tableParts"
TABLEPART_ELEMENT_TAG = PREFIX_EXCEL_PROC + "tablePart"

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

# Constant for XML Relationship (.rels file)
PREFIX_RELATHIONSHIP_NAMESPACE = "{http://schemas.openxmlformats.org/package/2006/relationships}"
RELATIONSHIPS_ROOT_ELEMENT = PREFIX_RELATHIONSHIP_NAMESPACE + "Relationships"
RELATIONSHIP_ELEMENT_TAG = PREFIX_RELATHIONSHIP_NAMESPACE + "Relationship"
RELATIONSHIP_ID_ATTRIBUTE = "Id"
RELATIONSHIP_TARGET_ATTRIBUTE = "Target"

# Constant for XML Table SpreadSheetML
TABLE_ROOT_ELEMENT = PREFIX_EXCEL_PROC + "table"
TABLE_ROOT_ELEMENT_REF_ATTRIBUTE = "ref"
TABLESTYLEINFO_ELEMENT_TAG = PREFIX_EXCEL_PROC + "tableStyleInfo"
TABLESTYLEINFO_ELEMENT_NAME_ATTRIBUTE = "name"

# Constant for XML Preset Table Style
DXFS_PST_TAG = "dxfs"
DXF_PST_TAG = "dxf"
TABLESTYLES_PST_TAG = "tableStyles"
TABLESTYLE_PST_TAG = "tableStyle"
TABLESTYLEELEMENT_PST_TAG = "tableStyleElement"
FONT_PST_TAG = "font"

# Estrai la formattazione del contenuto testuale della cella sezionata presente in styles.xml, se presente
def extract_cell_style_from_styles_xmlfile(tree_style, cell_index_style_value):

    root_style = tree_style.getroot() # get <styleSheet> element

    # Considera il tag <cellXfs> ed estrai tutti i suoi figli <xf> che descrivono formattazione delle celle
    xfs = root_style.findall("./" + CELLXFS_ELEMENT_TAG + "/" + XF_ELEMENT_TAG)

    # Seleziona l'elemento <xf> indicato dall'attributo s di cella su cui si sta lavorando ed estrai lo style
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

    return list(font) # Restituisci la lista degli elementi figli di <font> che contiene lo style della cella selezionata

# Aggiungi la formattazione estratta al/ai run presenti nello string item della SST indicato dal valore di <v> della cella <c>
def apply_fontstyle_into_string_in_sst(tree_sst, cell_value, font_tag_child_list):

    root_sst = tree_sst.getroot() # get <sst> element

    # Estrai tutti gli string item <si> presenti in <sst>
    string_items = root_sst.findall("./" + STRING_ITEM_TAG)

    # Seleziona l'elemento <si> indicato dal contenuto della cella (tag <v>) dato in input
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
    for run in run_elements: # ... per ciascun run
        for element_tag in font_tag_child_list:  # ... aggiungi i figli di "font", se non sono presenti
            if run.find("./" + RUN_ELEMENT_PROPERTY_TAG + "/" + element_tag.tag) == None:
                run.find("./" + RUN_ELEMENT_PROPERTY_TAG).append(element_tag)
        new_run = copy.copy(run) # usa la copia per risolvere problema di non modifica dei riferimenti (distacca run modificato da "string_item")
        string_item.replace(run, new_run) # rimpiazza il run corrente nel "string_item" con il nuovo run


# Estrai le informazioni su una tabella indicata da "table_path" relative al nome dello stile e le celle usate
def extract_table_info_from_table_xml_file(path_file_xlsx_extracted, table_path):

    # Leggi il contenuto del file "tableX.xml" indicato da "table_path" ed estrai il root element
    table_filename = os.path.split(table_path)[1] # restituisce ad es. "table1.xml"
    tree_table = etree.parse(path_file_xlsx_extracted + "/xl/tables/" + table_filename)
    root_table_tag = tree_table.getroot()  # get <table> element

    # Estrai il valore dell'attributo "ref" di <table>
    range_cell_table = root_table_tag.get(TABLE_ROOT_ELEMENT_REF_ATTRIBUTE) # es. "A3:O103"

    # Verifica che se l'elemento <tableStyleInfo> è presente, allora estrai il valore dell'attributo "name"
    if root_table_tag.find("./" + TABLESTYLEINFO_ELEMENT_TAG) == None:
        return range_cell_table, None # rest. None se <tableStyleInfo> non è presente
    table_style_name = root_table_tag.find("./" + TABLESTYLEINFO_ELEMENT_TAG).get(TABLESTYLEINFO_ELEMENT_NAME_ATTRIBUTE)

    return range_cell_table, table_style_name # rest. range delle celle usate dalla tabella e il nome dello stile usato

# Estrai da "presetTableStyle" la formattazione del contenuto testuale (tag <font>) per la riga di intestazione e intera tabella dallo stile indicato da "table_style_name"
def extract_fonts_table_style_from_presettablestylexml(tree_preset_table_style, table_style_name):

    root_preset_table_style = tree_preset_table_style.getroot() # get <presetTableStyle> element

    # Seleziona l'elemento XML il cui nome è uguale a "table_style_name" e cioè <table_style_name>
    table_style_name_tag = root_preset_table_style.find("./" + table_style_name)

    # Estrai da "table_style_name_tag" l'elemento <tableStyle> il cui attributo "name" è uguale a "table_style_name"
    table_style_tag = table_style_name_tag.find("./" + TABLESTYLES_PST_TAG + "/" + TABLESTYLE_PST_TAG)

    # Dichiarazione variabili che conteranno il contenuto di <font> per la riga di intestazione e intera tabella
    font_style_headerrow = None
    font_style_wholetable = None

    # Estrai tutti i figli dell'elemento <dxfs> che definiscono la formattazione da applicare alle varie aree della tabella
    dxfs = table_style_name_tag.findall("./" + DXFS_PST_TAG + "/" + DXF_PST_TAG)

    # Estrai da <tableStyle> tutti gli elementi figli <tableStyleElement> selezionando quelli richiesti
    table_style_element_tags = table_style_tag.findall("./" + TABLESTYLEELEMENT_PST_TAG)
    for tag in table_style_element_tags:
        # Seleziona <tableStyleElement> il cui attributo "type" è uguale a "headerRow"
        if tag.get("type") == "headerRow":
            # Seleziona l'elemento <dxf> da "dxfs" indicato dall'attributo "dxfId" di <tableStyleElement> selezionato
            dxf = dxfs[int(tag.get("dxfId"))-1]
            # Verifica se <dxf> selezionato contiene l'elemento <font>
            if dxf.find("./" + FONT_PST_TAG) == None:
                continue # non viene applicata la formattazione del contenuto testuale alla riga di intestazione
            font_style_headerrow = dxf.find("./" + FONT_PST_TAG)
        # Seleziona <tableStyleElement> il cui attributo "type" è uguale a "wholeTable"
        elif tag.get("type") == "wholeTable":
            # Seleziona l'elemento <dxf> da "dxfs" indicato dall'attributo "dxfId" di <tableStyleElement> selezionato
            dxf = dxfs[int(tag.get("dxfId"))-1]
            # Verifica se <dxf> selezionato contiene l'elemento <font>
            if dxf.find("./" + FONT_PST_TAG) == None:
                continue  # non viene applicata la formattazione del contenuto testuale alla riga di intestazione
            font_style_wholetable = dxf.find("./" + FONT_PST_TAG)

    return list(font_style_headerrow), list(font_style_wholetable) # rest. il contenuto di <font> applicato alla riga di intestazione e intera table


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
        root = tree_sheet.getroot()  # get <worksheet> element

        # Inizializza un contatore che tiene traccia di quante celle usano la formattazione a livello di cella (attributo s)
        count_cell_style = 0 # per testing
        # Step 3 -> Posizionati nella sezione "Sheet Data" e ed estrai tutte le righe di celle (tag <row>)
        rows = root.findall("./" + SHEETDATA_TAG + "/" + ROW_ELEMENT_TAG)
        for row in rows:  # per ciascun riga tra tutte quelle presenti nel sheet
            # Step 4 -> # Estrai tutte le celle presenti nella riga "row"
            cells = row.findall("./" + CELL_ELEMENT_TAG)
            for cell in cells:  # per ciascuna cella tra tutte quelli presenti nella riga "row"
                # Verifica se la cella ammette come tipo di contenuto una shared string e se considera lo stile in styles.xml
                if cell.get(CELL_TYPEDATA_ATTRIBUTE) != "s":
                    continue
                if cell.get(CELL_INDEXSTYLE_ATTRIBUTE) == None:
                    continue
                # Step 5 -> Memorizza in una variabile il valore dell'attributo "s" (Index Style) di <c> e in un'altra il contenuto della cella in <v>
                cell_index_style_value = int(cell.get(CELL_INDEXSTYLE_ATTRIBUTE))
                cell_value = int(cell.find(
                    "./" + CELL_VALUE_ELEMENT_TAG).text)  # estrae l'indice della string item (<si>) presente in SST

                # Step 6-7-8 -> Estrai la formattazione del contenuto testuale della cella sezionata presente in styles.xml
                font = extract_cell_style_from_styles_xmlfile(tree_style, cell_index_style_value)
                if font == None:  # se alla cella selezionata non viene applicata la formattazione del contenuto testuale
                    continue  # ... passa alla cella successiva

                # Step 9-10-11 -> Aggiungi la formattazione estratta al/ai run presenti nello string item della SST indicato dal valore di <v> della cella <c>
                apply_fontstyle_into_string_in_sst(tree_sst, cell_value, font)
                count_cell_style+= 1
            # Step 12 -> Ripeti dallo step 4 allo step 11 finché tutte le celle <c> nella riga "row" non sono state risolte
        # Step 13 -> Ripeti dallo step 3 allo step 12 finché tutte le righe "rows" utilizzate nel foglio di lavoro "sheet" non sono state risolte
    # Step 14 -> Ripeti dallo step 2 allo step 13 finché non sono stati esaminati tutti i fogli di lavoro presenti nella directory worksheet del xlsx steganografato

    print("Cell with shared string content that using styles.xml (attribute s): " + count_cell_style.__str__()) # for testing

    if tree_sst_input == None:  # se la SST non viene passata in input, scrivi la nuova SST nel file "sharedStrings.xml"
        tree_sst.write("stego/sharedStrings.xml")

    # Applicata la formattazione alla SST, restituisci il nuovo contenuto di "tree_sst" da scrivere poi in "sharedStrings.xml"
    return tree_sst


# Applicazione della formattazione delle celle usate da una tabella o più tabelle nella Shared String Table (sharedStrings.xml)
def apply_cell_table_style_into_sst(path_file_xlsx_extracted, tree_sst_input):
    # LETTURA FILE XML INTERESSATI
    # Leggi il contenuto del file "sharedStrings.xml", se non viene già passato in input
    if tree_sst_input == None:
        tree_sst = etree.parse(path_file_xlsx_extracted + "/xl/sharedStrings.xml")
    else:
        tree_sst = tree_sst_input

    # Leggi il contenuto del file "presetTableStyles.xml"
    tree_preset_table_style = etree.parse(PRESET_TABLE_STYLE_XML_FILE_PATH)

    # Step 1 -> Estrai tutti i fogli di lavoro (sheetX.xml) dalla directory "worksheet" del workbook S
    sheets = os.listdir(path_file_xlsx_extracted + "/xl/worksheets")
    for sheet in sheets:  # Rimuovi tutti i nomi dei file che sono diversi da "slideX.xml"
        if sheet.find("sheet") == -1:
            sheets.remove(sheet)
    # Inizializza contatore che tiene traccia delle celle usate da tutte le tabelle
    count_cell_usedby_table = 0 # for testing

    # Per ciascun sheet estratto
    for sheet in sheets:
        # Step 2 -> Leggi il contenuto del file XML indicato da "sheet" estraendo il root element
        tree_sheet = etree.parse(path_file_xlsx_extracted + "/xl/worksheets/" + sheet)
        root_worksheet = tree_sheet.getroot()  # get <worksheet> element

        # Step 3 -> Verifica se "sheet" contiene una tabella
        if root_worksheet.find("./" + TABLEPARTS_ELEMENT_TAG) == None:
            continue  # ... passa ad esaminare il prossimo foglio

        # Leggi il contenuto del file ".rels" associato a "sheet" estraendo il suo root element
        sheet_rels_file = sheet + ".rels"
        tree_sheet_rels = etree.parse(path_file_xlsx_extracted + "/xl/worksheets/_rels/" + sheet_rels_file)
        root_sheet_rels = tree_sheet_rels.getroot()  # get <Relationships> element

        # Step 4 -> Estrai tutti i figli dell'elemento <tableParts>
        table_parts = root_worksheet.findall("./" + TABLEPARTS_ELEMENT_TAG + "/" + TABLEPART_ELEMENT_TAG)
        for table in table_parts:
            # Step 5 -> Seleziona un <tablePart> alla volta ed estrai il valore dell'attributo "r:id"
            table_rel_id = table.get(REL_ID_ATTRIBUTE)

            # Step 6 -> Estrai tutte le relazioni presenti "sheet_rels_file" e seleziona quella il cui attributo "Id" è uguale a "table_rel_id"
            relationships = root_sheet_rels.findall("./" + RELATIONSHIP_ELEMENT_TAG)
            table_path = None  # memorizza in questa variabile il valore dell'attributo "Target" della relazione selezionata
            for rel in relationships:
                if rel.get(RELATIONSHIP_ID_ATTRIBUTE) == table_rel_id:
                    table_path = rel.get(RELATIONSHIP_TARGET_ATTRIBUTE)  # es. "../tables/table1.xml"

            # Step 7 -> Estrai il nome dello stile e le celle usate da una tabella specificata in "table_path"
            range_cell_table, table_style_name = extract_table_info_from_table_xml_file(path_file_xlsx_extracted,
                                                                                        table_path)
            if table_style_name == None:  # la tabella attuale non usa uno stile, passa alla prossima tabella
                continue

            # Step 8-9 -> Estrai da "presetTableStyle" la formattazione del contenuto testuale per la riga di intestazione e
            # intera tabella dallo stile indicato da "table_style_name"
            font_style_header_row, font_style_whole_table = extract_fonts_table_style_from_presettablestylexml(
                tree_preset_table_style, table_style_name)
            if font_style_header_row == None or font_style_whole_table == None:
                continue  # alla tabella attuale non viene applicata la formattazione del testo o per la riga di intestazione o per l'intera tabella

            # Estrae da "range_cell_table" le informazioni relative alla prima e ultima riga e colonna di celle dello sheet usate per la tabella
            row_start, row_end, col_start, col_end = utils.extract_startend_row_column_cell_used_by_table(
                range_cell_table)

            # Step 10-14 -> Per ciascuna riga in "sheet" che fa parte di "range_cell_table", estrai le celle il cui contenuto è una stringa condivisa
            # Poi, procedi ad applicare lo style estratto a tutti gli string item della SST a cui fanno riferimento le celle estratte.
            for i in range(row_start, row_end+1, 1):
                # Estrai tutte le celle presenti nell'i-esimo elemento <row> di <sheetData> in "sheet"
                cells = root_worksheet.findall(
                    "./" + SHEETDATA_TAG + "/" + ROW_ELEMENT_TAG + "[" + i.__str__() + "]/" + CELL_ELEMENT_TAG)
                for cell in cells:  # per ciascuna cella tra tutte quelli presenti nella riga selezionata
                    # Verifica se la cella ammette come tipo di contenuto una shared string
                    if cell.get(CELL_TYPEDATA_ATTRIBUTE) != "s":
                        continue
                    # Estrai l'indice della string item (<si>) presente in SST leggendo il contenuto delle cella (tag <v>) di "cell"
                    cell_value = int(cell.find("./" + CELL_VALUE_ELEMENT_TAG).text)
                    # Step 12-14 -> Separa lo stile da applicare alla riga di celle di intestazione e alle righe che costituiscono l'intera tabella
                    if i == row_start:  # riga di intestazione
                        # Aggiungi la formattazione estratta al/ai run presenti nello string item della SST indicato dal valore di "cell_value"
                        apply_fontstyle_into_string_in_sst(tree_sst, cell_value, font_style_header_row)
                    else:
                        # Aggiungi la formattazione estratta al/ai run presenti nello string item della SST indicato dal valore di "cell_value"
                        apply_fontstyle_into_string_in_sst(tree_sst, cell_value, font_style_whole_table)
                    count_cell_usedby_table += 1
            # Step 15 -> Ripeti dallo step 10 al 14 finché tutte le celle <c> presenti in ciascuna riga <row> non state risolte
        # Step 16 -> Ripeti dallo step 5 allo step 15 finché non sono state esaminate tutte le tabelle
    # Step 17 -> Ripeti dallo step 2 allo step 13 finché non sono stati esaminati tutti i fogli di lavoro presenti nella directory "worksheet" del xlsx steganografato

    print("Total cell with shared string content used by tables: " + count_cell_usedby_table.__str__()) # for testing

    if tree_sst_input == None:  # se la SST non viene passata in input, scrivi la nuova SST nel file "sharedStrings.xml"
        tree_sst.write("stego/sharedStrings.xml")

    # Applicata la formattazione alla SST, restituisci il nuovo contenuto di "tree_sst" da scrivere poi in "sharedStrings.xml"
    return tree_sst