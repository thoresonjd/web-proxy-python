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
        while True:
            conn, addr = self.listener.accept()
            data = conn.recv(BUF_SZ)
            print(data)

    def receive(self, sock: socket) -> str:
        pass
    
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