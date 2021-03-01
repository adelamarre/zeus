from multiprocessing import Process
import http.server
from typing import List
from urllib.parse import urlparse
from urllib.parse import parse_qs
from json import dumps
from src.services.console import Console
from ssl import wrap_socket
from requests import get
from OpenSSL import crypto


class StatsProvider:
    def __init__(self, name: str):
        self.name = name

    def getStats():
        pass

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    statsProviders: List[StatsProvider] = None
    apiKey = 'sdkfjhsagkfsjqgksqjgfqskjgbn'
    

    def log_message(self, format: str, *args) -> None:
        pass

    def do_GET(self):

        # Extract query param
        query_components = parse_qs(urlparse(self.path).query)
        if 'k' in query_components:
            if query_components["k"][0] != MyHttpRequestHandler.apiKey:
                return    
        else:
            return
        # Sending an '200 OK' response
        self.send_response(200)

        # Setting the header
        self.send_header("Content-type", "application/json")

        # Whenever using 'send_header', you also have to call 'end_headers'
        self.end_headers()

        result = {}
        for s in MyHttpRequestHandler.statsProviders:
            result[s.name] = s.getStats()

        json = dumps(result)

        # Some custom HTML code, possibly generated by another function
        #html = f"<html><head></head><body><h1>Hello {name}!</h1></body></html>"

        # Writing the HTML contents with UTF-8
        self.wfile.write(bytes(json, "utf8"))

        return

def runner(apiKey: str, ip: str, certificate: str, statsProviders: List[StatsProvider]):

    #openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes

    handler_object = MyHttpRequestHandler
    handler_object.statsProviders = statsProviders
    handler_object.apiKey = apiKey
    PORT = 63443
    
    #try:
        #my_server = socketserver.TCPServer(("", PORT), handler_object)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler_object)
    server.socket = wrap_socket(server.socket, certfile=certificate, server_side=True)
    server.serve_forever()
    #except:
        #print(traceback.format_exc())
        #console.exception()



class HttpStatsServer:
    def __init__(self, apiKey: str, console: Console, userDir: str, statsProviders: List[StatsProvider]):
        self.apiKey = apiKey
        self.console = console
        self.statsProviders = statsProviders
        self.process: Process = None
        self.ip = get('https://api.ipify.org').text
        self.certificate = userDir + '/server.pem'
        self.cert_gen(
            commonName=self.ip,
            PEM_FILE=self.certificate
        )


    def start(self):
        self.process = Process(target=runner, args=(self.apiKey, self.ip, self.certificate, self.statsProviders, ))
        self.process.start()
    
    def stop(self):
        self.process.kill()
        self.process.join()
    
    def cert_gen(self,
        emailAddress="email@address.com",
        commonName="commonName",
        countryName="NT",
        localityName="localityName",
        stateOrProvinceName="stateOrProvinceName",
        organizationName="organizationName",
        organizationUnitName="organizationUnitName",
        serialNumber=0,
        validityStartInSeconds=0,
        validityEndInSeconds=10*365*24*60*60,
        #KEY_FILE = "private.key",
        #CERT_FILE="selfsigned.crt"
        PEM_FILE="server.pem"
        ):
        #can look at generated file using openssl:
        #openssl x509 -inform pem -in selfsigned.crt -noout -text
        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 4096)
        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = countryName
        cert.get_subject().ST = stateOrProvinceName
        cert.get_subject().L = localityName
        cert.get_subject().O = organizationName
        cert.get_subject().OU = organizationUnitName
        cert.get_subject().CN = commonName
        cert.get_subject().emailAddress = emailAddress
        cert.set_serial_number(serialNumber)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(validityEndInSeconds)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha512')
        with open(PEM_FILE, "w") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        with open(PEM_FILE, "a") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))