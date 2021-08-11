import cgi
import http.server
import os
import socketserver
import urllib
from zipfile import ZipFile

from Crypto.Random import random

from webapp.decoder import decoding
from webapp.encoder import encoding


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        qs = {}
        path = ""
        if self.path == '/decoder' or self.path.startswith("/decoder?testo_segreto="):
            self.path = 'decoder.html'
        elif self.path == '/encoder' or self.path == "/encoder?success=true":
            self.path = 'encoder.html'

        if '?' in self.path:
            path, tmp = self.path.split('?', 1)
            if tmp:
                qs = urllib.parse.parse_qs(tmp)
        if path == '/encoding':
            encoding(qs['input'][0],qs['message'][0],qs['pass'][0])
            self.send_response(301)
            self.send_header('Location', "/encoder?success=true")
            self.end_headers()
            return #necessario perche' fornisce eccezione 'FileNotFoundError' per '/encoding'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):

        if self.path == '/decoding':
            # Parse the form data posted
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': self.headers['Content-Type'],
                         })
            filename = form['file_stego'].filename
            data = form['file_stego'].file.read()
            open("stego/stego.zip", "wb").write(data)
            # Create a ZipFile Object and load sample.zip in it
            with ZipFile('stego/stego.zip', 'r') as zipObj:
                # Extract all the contents of zip file in different directory
                zipObj.extractall('stego/file_extracted')
            os.remove("stego/stego.zip")
            secret_text = decoding(form.getvalue("password"))
            self.send_response(301)
            self.send_header('Location', "/decoder?testo_segreto=" + secret_text)
            self.end_headers()
            return #necessario perche' fornisce eccezione 'FileNotFoundError' per '/decoding'

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Create an object of the above class
handler_object = MyHttpRequestHandler
rand = random.choice(range(7000, 8999))
print(rand)
PORT = 8080

my_server = socketserver.TCPServer(("", PORT), handler_object)
# Star the server
my_server.serve_forever()