
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
});

$("#decoder_image_button").click(function(){
    hideAllContent();
    $("#decoder_area_container").show();
});

//funzioni per pulsanti
function showHomeContent(){ //pulsante "Home"
    hideAllContent();
    $("#main_container").show();
}

//funzioni per pulsanti "Encoder Area"
$("#hide_txt_action").click(function(){ //pulsante "Nascondi testo"
    //Aggiorna il pulsante con pulsante "Loading..."

    //...richiesta servlet
    var coverfile = $("#upload_cover_file")[0].files[0]; //object file
    var text_to_hide = $("#secret_text").val(); //string
    var password_enc = $("#password_encrypt").val(); //string

    alert(" Text: " + text_to_hide + "; Password: " + password_enc);
   /*
    $.post("encoder-controller", {"action": "hideText", "coverfile": coverfile, "secretText", text_to_hide, "passwordEnc", password_enc},
      function(resp, status, xhr){
		if(xhr.readyState == 4 & status=="success"){
			var o = JSON.parse(resp); //conversione in oggetto JS da strina JSON ricevuta da servlet
			//...
		}else{
			//window.location.href = "./error.jsp"; //pagina errore 404
		}
	});
	*/

    //Mostra popup successo operazione
    $("#content_popup_downstego").show();
    $("#content_popup_downstego").addClass("popup_body");

    //Mostra popup operazione fallita
    //$("#content_popup_error_hidetext").show();
    //$("#content_popup_error_hidetext").addClass("popup_body");

    //Al termine dell'operazione, vai alla home
    //showHomeContent();
});

$("#cancel_download_stego_action").click(function(){ //pulsante "Annulla" del popup "Download stego file"
    removePopupDownloadStego();
});

$("#download_stego_action").click(function(){ //pulsante "Download stego file"

    //Richiesta http

    //Rimuovi popup al termine dell'operazione
    removePopupDownloadStego();
});

function removePopupDownloadStego(){
    $("#content_popup_downstego").removeClass("popup_body");
    $("#content_popup_downstego").hide();
}

function removePopupErrorHideText(){
    $("#content_popup_error_hidetext").removeClass("popup_body");
    $("#content_popup_error_hidetext").hide();
}


//funzioni per pulsanti "Decoder Area"
$("#extract_txt_action").click(function(){ //pulsante "Estrai testo nascosto"
    //Aggiorna il pulsante con pulsante "Loading..."

    //...richiesta servlet
    var stegofile = $("#upload_stego_file")[0].files[0]; //object file
    var password_dec = $("#password_decrypt").val(); //string



    //Mostra popup successo operazione
    $("#content_popup_extracttext").show();
    $("#content_popup_extracttext").addClass("popup_body");

    //Mostra popup operazione fallita
    //$("#content_popup_error_extracttext").show();
    //$("#content_popup_error_extracttext").addClass("popup_body");

    //Al termine dell'operazione, vai alla home
    //showHomeContent();
});

$("#ok_extracted_text_btn").click(function(){ //pulsante "Ok" del popup "Estrai testo nascosto"
    removePopupExtractText()
    showHomeContent();
});

function removePopupExtractText(){
    $("#content_popup_extracttext").removeClass("popup_body");
    $("#content_popup_extracttext").hide();
}

function removePopupErrorExtractText(){
    $("#content_popup_error_extracttext").removeClass("popup_body");
    $("#content_popup_error_extracttext").hide();
}