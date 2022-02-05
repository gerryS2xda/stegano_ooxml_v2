import socketserver
import cgi
import json
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse
from urllib.parse import parse_qs
from webapp.backend import split_method_stegano

# Server configuration
hostName = "localhost"
serverPort = 8080

# Other configuration
INPUT_FILES_DIR = "./backend/input_files"
WORKING_DIRECTORY_PATH = "./backend/working_directory"
OUTPUT_STEGO_DIRECTORY = "./backend/output_stego"

# Classe che riceverà e risponderà alla richieste HTTP
class MyHttpRequestHandlerServer(SimpleHTTPRequestHandler):

    # Set header for a JSON Response
    def _set_json_response_header(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    # Implementazione del metodo che risponde alle richieste GET
    def do_GET(self):

        # Ridireziona verso la pagina iniziale
        if self.path == "/":
            self.path = "/frontend/index.html"


        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        controller_type = self.path.split('?')[0]

        # Encoder controller
        if controller_type == "/encoder-controller":
            # Estrai i parametri della richiesta POST
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': self.headers['Content-Type'],
                         })
            action = form.getvalue("action")
            if action == "hideText":
                # Get uploaded file from POST request and put it in "working_directory" folder
                cover_filename = form["coverfile"].filename
                print(cover_filename)
                coverfile = form["coverfile"].file.read()
                open(INPUT_FILES_DIR + "/" + cover_filename, "wb").write(coverfile)

                # Get text to hide and password to encrypt text
                secret_text = form.getvalue("secretText")
                password_enc = form.getvalue("passwordEnc")

                # Run encoder
                esito_op, path_output_stego_file = split_method_stegano.run_encoder(cover_filename, secret_text, password_enc)
                if not esito_op: # se l'operazione è fallita
                    self._set_json_response_header()
                    self.wfile.write(bytes(json.dumps({"success": "false"}), "utf8"))
                else:
                    self._set_json_response_header()
                    self.wfile.write(bytes(json.dumps({"success": "true", "path_stego_file": path_output_stego_file}), "utf8"))
        elif controller_type == "/decoder-controller":
            # Estrai i parametri della richiesta POST
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': self.headers['Content-Type'],
                         })
            action = form.getvalue("action")
            if action == "extractTxt":
                # Get uploaded file from POST request and put it in "working_directory" folder
                stego_filename = form["stegofile"].filename
                stego_file = form["stegofile"].file.read()
                open(INPUT_FILES_DIR + "/" + stego_filename, "wb").write(stego_file)

                # Get password to decrypt extracted text
                password_dec = form.getvalue("passwordDec")

                # Run decoder
                esito_op, text_extracted = split_method_stegano.run_decoder(stego_filename, password_dec)
                if not esito_op:  # se l'operazione è fallita
                    self._set_json_response_header()
                    self.wfile.write(bytes(json.dumps({"success": "false"}), "utf8"))
                else:
                    self._set_json_response_header()
                    self.wfile.write(
                        bytes(json.dumps({"success": "true", "extract_txt": text_extracted}), "utf8"))

        return

# Avvio e stop del server
if __name__ == "__main__":
    print("Avvio del server...")
    webServer = socketserver.TCPServer((hostName, serverPort), MyHttpRequestHandlerServer)
    print("Server started: http://%s:%s" % (hostName, serverPort))
    print("Server in esecuzione...")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")


