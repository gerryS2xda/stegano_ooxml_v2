import socketserver
import cgi
import os
import sys
import time
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
    # Implementazione del metodo che risponde alle richieste GET
    def do_GET(self):

        # Ridireziona verso la pagina iniziale
        if self.path == "/":
            self.path = "/frontend/index.html"

        """
        controller_type = self.path.split('?')[0]

        # Encoder controller
        if controller_type == "/encoder-controller":
            # Estrai i parametri della richiesta dall'url
            params = parse_qs(urlparse(self.path).query)
            print(params) # {'action': ['hideText'], 'coverfile': ['{}'], 'secretText': ['HelloWorld'], 'passwordEnc': ['123ad']}
            #action = params["action"][0]
            self.send_response(200)
            self.end_headers()
        """

        """
        # Specifica codice di risposta
        self.send_response(301)
        self.send_header('Location', self.path)
        self.end_headers()

        
        print(self.path)
        
        # Costruzione risposta da inviare
        #message = "Hello World"
        #self.wfile.write(bytes(message, "utf8"))
        
            self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        """
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
            print(action)
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
                esito_op = split_method_stegano.run_encoder(cover_filename, secret_text, password_enc)
                if not esito_op: # se l'operazione è fallita
                    print("Operazione fallita")
                else:
                    print("Operazione eseguita correttamente")


            self.send_response(200)
            self.end_headers()

        return SimpleHTTPRequestHandler.do_GET(self)

# Avvio e stop del server
if __name__ == "__main__":
    print("Avvio del server...")
    #webServer = HTTPServer((hostName, serverPort), MyHttpRequestHandlerServer)
    webServer = socketserver.TCPServer((hostName, serverPort), MyHttpRequestHandlerServer)
    print("Server started: http://%s:%s" % (hostName, serverPort))
    print("Server in esecuzione...")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")


