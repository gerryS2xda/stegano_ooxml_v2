
//funzione eseguita dopo il caricamento della pagina (body tag)
function hideAllContentExceptMainArea(){
	$("#encoder_area_container").hide();
	$("#decoder_area_container").hide();
}

function hideAllContent(){
    $("#main_container").hide();
    $("#encoder_area_container").hide();
	$("#decoder_area_container").hide();
}

//funzioni per la selezione della modalità
$("#encoder_image_button").click(function(){
    hideAllContent();
    $("#encoder_area_container").show();
    $("#path_stego_file_to_download").text(""); //reset hidden path
});

$("#decoder_image_button").click(function(){
    hideAllContent();
    $("#decoder_area_container").show();
    $("#extract_text_textarea").text(""); //reset textarea popup
});

//funzioni per pulsanti
function showHomeContent(){ //pulsante "Home"
    hideAllContent();
    $("#main_container").show();
}

//funzioni per pulsanti "Encoder Area"
$("#hide_txt_action").click(function(){ //pulsante "Nascondi testo"
    //Prima di eseguire, verifica che tutti i campi del form sono riempiti
    if(!formHideTextValidation()){
        alert("Ci sono uno o più campi obbligatori che devono essere completati!!");
        return;
    }

    //Aggiorna il pulsante con pulsante "Loading..."
    $("#home_btn_hidetext").hide();
    $("#hide_txt_action").hide();
    $("#loading_btn_hidetxt").show();

    // Send HTTP POST Request to server
    var coverfile = $("#upload_cover_file")[0].files[0]; //object file
    var text_to_hide = $("#secret_text").val(); //string
    var password_enc = $("#password_encrypt").val(); //string

    var fd = new FormData(); // create FormData to send data with POST req
    fd.append('action', "hideText");
    fd.append('coverfile', coverfile);
    fd.append('secretText', text_to_hide);
    fd.append('passwordEnc', password_enc);

    $.ajax({
        url: 'encoder-controller',
        type: 'POST',
        data: fd,
        contentType: false,
        processData: false,
        success: function(result,status,xhr){
            error_msg = "";
            if(xhr.readyState == 4 & status == "success"){
                if(result["success"] === "true"){
                    //Scrivi da qualche parte il path del file steganografato da scaricare
                    $("#path_stego_file_to_download").text(result["path_stego_file"])

                    //Mostra popup successo operazione
                    $("#content_popup_downstego").show();
                    $("#content_popup_downstego").addClass("popup_body");

                    //Rimuovi pulsante "loading"
                    removeLoadingBtnHideText();
                    resetFormHideText();
                    return;
                }
                error_msg = "Impossibile completare l'operazione! Non vi è abbastanza capacità di inclusione per nascondere un testo!!";
            }else{
                error_msg = "Impossibile completare l'operazione! Errore da parte del server!!";
            }
            //Mostra popup di errore, rimuovi pulsante "Loading" e resetta i campi del form
            showPopupHideTextError(error_msg);
            removeLoadingBtnHideText();
            resetFormHideText();
        },
    });
});

function showPopupHideTextError(error_msg){
    //Imposta messaggio di errore da mostrare
    $("#p_popup_hidetext_err").text(error_msg)

    //Mostra popup operazione fallita
    $("#content_popup_error_hidetext").show();
    $("#content_popup_error_hidetext").addClass("popup_body");
}

$("#cancel_download_stego_action").click(function(){ //pulsante "Annulla" del popup "Download stego file"
    removePopupDownloadStego();
});

$("#download_stego_action").click(function(){ //pulsante "Download stego file"

    // Get path of file to download and fix path
    stego_file_path = $("#path_stego_file_to_download").text();
    if(stego_file_path[0] === "." && stego_file_path[1] === "."){
        stego_file_path = stego_file_path.substring(2)
    }else if(stego_file_path[0] === "."){
        stego_file_path = stego_file_path.substring(1)
    }

    //Send POST Http request for download a file
    $.ajax({
        url: stego_file_path,
        cache: false,
        xhr: function () {
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function () {
                if (xhr.readyState == 2) {
                    if (xhr.status == 200) {
                        xhr.responseType = "blob";
                    } else {
                        xhr.responseType = "text";
                    }
                }
            };
            return xhr;
        },
        success: function (data, status, xhr) {
            if(xhr.readyState == 4 & status == "success"){
                //Convert the Byte Data to BLOB object.
                var blob = new Blob([data], { type: "application/octetstream" });

                //Get filename to download
                fileName = $("#path_stego_file_to_download").text();
                fileName = fileName.substring(fileName.lastIndexOf('/')+1);

                //Check the Browser type and download the File.
                var isIE = false || !!document.documentMode;
                if (isIE) {
                    window.navigator.msSaveBlob(blob, fileName);
                } else {
                    var url = window.URL || window.webkitURL;
                    link = url.createObjectURL(blob);
                    var a = $("<a />");
                    a.attr("download", fileName);
                    a.attr("href", link);
                    a.attr("id", "link_fittizio")
                    $("body").append(a);
                    a[0].click();
                    $("#link_fittizio").remove();
                    //$("body").remove(a);
                }
                removePopupDownloadStego();
                showHomeContent(); //ritorna alla home
                return;
            }
            error_msg = "Impossibile completare l'operazione! Errore da parte del server!!";
            showPopupHideTextError(error_msg);
        }
    });
});

function removePopupDownloadStego(){
    $("#content_popup_downstego").removeClass("popup_body");
    $("#content_popup_downstego").hide();
}

function removePopupErrorHideText(){
    $("#content_popup_error_hidetext").removeClass("popup_body");
    $("#content_popup_error_hidetext").hide();
}

function removeLoadingBtnHideText(){
    $("#loading_btn_hidetxt").hide();
    $("#home_btn_hidetext").show();
    $("#hide_txt_action").show();
}

function resetFormHideText(){
    $("#upload_cover_file").val("");
    $("#secret_text").val("");
    $("#password_encrypt").val("");
}

//funzioni per pulsanti "Decoder Area"
$("#extract_txt_action").click(function(){ //pulsante "Estrai testo nascosto"
    //Prima di eseguire, verifica che tutti i campi del form sono riempiti
    if(!formExtractTextValidation()){
        alert("Ci sono uno o più campi obbligatori che devono essere completati!!");
        return;
    }

    //Aggiorna il pulsante con pulsante "Loading..."
    $("#home_btn_extracttxt").hide();
    $("#extract_txt_action").hide();
    $("#loading_btn_extracttxt").show();

    // Send HTTP POST Request to server
    var stegofile = $("#upload_stego_file")[0].files[0]; //object file
    var password_dec = $("#password_decrypt").val(); //string

    var fd = new FormData();
    fd.append("action", "extractTxt");
    fd.append("stegofile", stegofile);
    fd.append("passwordDec", password_dec);

    $.ajax({
        url: 'decoder-controller',
        type: 'POST',
        data: fd,
        contentType: false,
        processData: false,
        success: function(result,status,xhr){
            if(xhr.readyState == 4 & status == "success"){
                if(result["success"] === "true"){
                    //Scrivi nella textarea il testo estratto
                    $("#extract_text_textarea").text(result["extract_txt"]);

                    //Scrivi il numero di volte in cui viene estratto lo stesso testo
                    $("#num_rip_txt_segreto").text(result["count_repeat_same_secret_txt"]);

                    //Mostra popup successo operazione
                    $("#content_popup_extracttext").show();
                    $("#content_popup_extracttext").addClass("popup_body");

                    //Rimuovi pulsante "loading"
                    removeLoadingBtnExtractText();
                    resetFormExtractText();
                    return;
                }
                error_msg = "Impossibile completare l'operazione! Password errata o testo segreto non presente!";
            }else{
                error_msg = "Impossibile completare l'operazione! Errore da parte del server!!";
            }
            //Mostra popup di errore, rimuovi pulsante "Loading" e resetta i campi del form
            showPopupExtractTextError(error_msg);
            removeLoadingBtnExtractText();
            resetFormExtractText();
        },
    });
});

$("#ok_extracted_text_btn").click(function(){ //pulsante "Ok" del popup "Estrai testo nascosto"
    removePopupExtractText();
    showHomeContent();
});

function showPopupExtractTextError(error_msg){
    //Imposta messaggio di errore da mostrare
    $("#p_popup_extracttext_err").text(error_msg);

    //Mostra popup operazione fallita
    $("#content_popup_error_extracttext").show();
    $("#content_popup_error_extracttext").addClass("popup_body");
}

function removePopupExtractText(){
    $("#content_popup_extracttext").removeClass("popup_body");
    $("#content_popup_extracttext").hide();
}

function removePopupErrorExtractText(){
    $("#content_popup_error_extracttext").removeClass("popup_body");
    $("#content_popup_error_extracttext").hide();
}

function removeLoadingBtnExtractText(){
    $("#loading_btn_extracttxt").hide();
    $("#home_btn_extracttxt").show();
    $("#extract_txt_action").show();
}

function resetFormExtractText(){
    $("#upload_stego_file").val("");
    $("#password_decrypt").val("");
}

//Funzioni per la validazione dei campi dei form
function validateUploadCoverFileField(item){
    var x = item.val();
    var esito = true;
    if(x === ""){ //campo vuoto
        $("#p_form_hidetext_field_err").show();
        item.css("border","3px solid red");
        esito = false;
    }else{
        $("#p_form_hidetext_field_err").hide();
        item.css("border", "1px solid #ccc");
    }

    return esito;
}

function validateSecretTextField(item){
    var x = item.val();
    var esito = true;
    if(x === ""){ //campo vuoto
        $("#p_form_hidetext_field_err").show();
        item.css("border","3px solid red");
        esito = false;
    }else{
        $("#p_form_hidetext_field_err").hide();
        item.css("border", "1px solid #ccc");
    }

    return esito;
}

function validatePasswordEncryptField(item){
    var x = item.val();
    var esito = true;
    if(x === ""){ //campo vuoto
        $("#p_form_hidetext_field_err").show();
        item.css("border","3px solid red");
        esito = false;
    }else{
        $("#p_form_hidetext_field_err").hide();
        item.css("border", "1px solid #ccc");
    }

    return esito;
}

function validateUploadStegoFileField(item){
    var x = item.val();
    var esito = true;
    if(x === ""){ //campo vuoto
        $("#p_form_extracttext_field_err").show();
        item.css("border","3px solid red");
        esito = false;
    }else{
        $("#p_form_extracttext_field_err").hide();
        item.css("border", "1px solid #ccc");
    }

    return esito;
}

function validatePasswordDecryptField(item){
    var x = item.val();
    var esito = true;
    if(x === ""){ //campo vuoto
        $("#p_form_extracttext_field_err").show();
        item.css("border","3px solid red");
        esito = false;
    }else{
        $("#p_form_extracttext_field_err").hide();
        item.css("border", "1px solid #ccc");
    }

    return esito;
}

function formHideTextValidation(){
    var esito = false;
    if(validateUploadCoverFileField($("#upload_cover_file"))){
        if(validateSecretTextField($("#secret_text"))){
            if(validatePasswordEncryptField($("#password_encrypt"))){
                esito = true;
            }
        }
    }
    return esito;
}

function formExtractTextValidation(){
    var esito = false;
    if(validateUploadStegoFileField($("#upload_stego_file"))){
        if(validatePasswordDecryptField($("#password_decrypt"))){
            esito = true;
        }
    }
    return esito;
}