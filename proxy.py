"""
Web Proxy
:file: proxy.py
:author: Justin Thoreson
:version: 1.0
"""

from urllib.parse import urlparse
from pathlib import Path
from socket import *
import sys

HOSTNAME = 'localhost'
BUF_SZ = 1024
BACKLOG = 5

class RequestError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(''.join(['Request Error: ', message]))

class Proxy():
    def __init__(self, port: int) -> None:
        self.listener, self.address = self.start_server(HOSTNAME, port)

    def start_server(self, host: str, port: int) -> tuple:
        """
        Creates a listening socket for the proxy
        :param host: The host name to listen from
        :param port: The port number to listen from
        :return: The listening socket and the socket's address
        """

        address = (host, port)
        server = socket(AF_INET, SOCK_STREAM)
        server.bind(address)
        server.listen(BACKLOG)
        return server, address

    def run(self) -> None:
        """Execute the proxy"""
        
        while True:
            conn, addr = self.listener.accept()
            request = conn.recv(BUF_SZ)
            try:
                host, port, path = self.parse_request(request)
            except RequestError as e:
                print(e)
            conn.close()

    @staticmethod
    def parse_request(request: str) -> tuple:
        method, uri, http_version = request.decode('UTF-8').split()
        uri = urlparse(uri)
        if not method == 'GET':
            raise RequestError('Unsupported method')
        if not uri.hostname:
            raise RequestError('Invalid URI')
        if not http_version == 'HTTP/1.1':
            raise RequestError('Unsupported version')
        return uri.hostname, uri.port, uri.path

    def send(self):
        pass

def main() -> None:
    if len(sys.argv) != 2:
        print('USAGE: python3 proxy.py <port>')
        exit(1)
    proxy = Proxy(int(sys.argv[1]))
    proxy.run()

if __name__ == '__main__':
    main()