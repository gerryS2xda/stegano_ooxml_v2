import socketserver
from http.server import SimpleHTTPRequestHandler

# Server configuration
hostName = "localhost"
serverPort = 8080

# Classe che riceverà e risponderà alla richieste HTTP
class MyHttpRequestHandlerServer(SimpleHTTPRequestHandler):
    # Implementazione del metodo che risponde alle richieste GET
    def do_GET(self):

        # Ridireziona verso la pagina iniziale
        if self.path == "/":
            self.path = "/frontend/index.html"



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


