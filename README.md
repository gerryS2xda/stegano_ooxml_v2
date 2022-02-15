# Stegano OOXML (v2) - Il metodo dello split del contenuto testuale
Progetto di tesi magistrale per il corso di Digital Forensics a cura di Paolo Vigorito (prima versione) e Gerardo Michele Laucella (seconda versione). 

<p align="center" width="100%">
  <img align="left" src="./webapp/frontend/image/HideAText.png" height="100" />
</p>

## Info sul progetto
Questo progetto realizza la tecnica steganografica del metodo dello split del contenuto testuale per i documenti Microsoft Office Word, PowerPoint ed Excel. Tale tecnica è stata studiata per i documenti Word consultando il paper [1] . L'idea è stata quella di verificare se è possibile riadattare la tecnica applicata per i documenti Word anche per le altre tipologie di file in formato OOXML come file ".pptx" e ".xlsx" sfruttando qualche elemento in comune nel gestire il contenuto testuale.

## Il metodo dello split
È una tecnica steganografica per nascondere informazioni all'interno di un documento in formato OOXML sfruttando le caratteristiche di gestione del contenuto testuale, da mostrare sull'applicativo, in tali documenti. L'idea è quella di splittare gli elementi o tag XML che si occupano del contenuto testuale in base ai bit dell'informazione da nascondere. Ad esempio, se il bit da nascondere è "1" si applica lo split, altrimenti non si applica lo split ma si tiene traccia nel testo del punto in cui andare a fare la prossima suddivisione quando il prossimo bit da incapsulare è "1".

## Funzionalità
  - Uso di un modulo di cifratura simmetrico (AES-CBC) per cifrare o decifrare testo da nascondere
  - Nascondere un testo in un ".docx", ".pptx", ".xlsx"
  - Estrazione di un testo da un ".docx", ".pptx", ".xlsx"
  - Web Application dedicata e una versione da riga di comando
  - Risolto problema dell'impercettibilità in Excel

## Command Line App version
1) Inserire i file di input nella directory "app/input"
2) Eseguire il file "main.py":
                                    "python main.py"
3) Selezionare la modalità di esecuzione digitando 1 per iniettare un testo e 2 per estrarre un testo nascosto
4) Per iniettare un testo occorre specificare il file di input (directory "app/input"), il testo da nascondere e una password per cifrare il testo prima di incapsularlo
5) Per estrarre un testo occorre specificare il file di input (directory "app/stego") e una password per decifrare il testo dopo l'estrazione.

## Webapp version
1) Avviare l'esecuzione del file "/webapp/main_web_server" 
                                    "python main_web_server.py"
2) Aprire un web browser e digitare "http://localhost:8080/"
3) Per iniettare del testo segreto, selezionare la voce "Nascondi un testo"
4) Per estrapolare del testo segreto, selezionare la voce "Estrai un testo segreto"
5) Completare i vari form.

## Sviluppi futuri
  - Risolvere problemi di prestazioni dovuto alla ripetizione del testo e algoritmi per l'impercettibilità Excel
  - Includere il contenuto testuale di tabelle e altri oggetti per aumentare capacità di inclusione
  - Provare ad usare un modulo di cifratura asimmetrico 
  - Risolvere problema della robustezza relativa all'alterazione automatica dei file XML quando si salva un file
  - Incapsulare il codice di un malware e verificare se esso viene rilevato da un antivirus

## Bibliografia
  [1] W. Guo, L. Yang, Y. Yang, L. Li, Z. Liu e Y. Lu, «Information Hiding in OOXML Format Data based on the Splitting of Text Elements,» IEEE International Conference on Intelligence and Security Informatics (ISI), pp. 188-190, 2019. 
  [2] P. Virgorito, Tecniche di steganografia: nascondere informazioni mediante l'uso dei documenti Word [Tesi di Laurea], Università degli Studi di Salerno - Dipartimento di Informatica, 2020. 
  [3] Z. Fu, X. Sun, Y. Liu e B. Li, «Text split-based steganography in OOXML format documents for covert communication,» Security & Communication Networks, vol. 5, n. 9, pp. 957-968, 2012.
  [4] OfficeOpenXML.com, «What is OOXML?,» [Online]. Available: http://officeopenxml.com/index.php.
  [5] ECMA International, «Standard ECMA-376 Office Open XML File Formats – Part 1,» ECMA International Publication, June 2011. 
