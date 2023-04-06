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
BUF_SZ = 4096
BACKLOG = 5
TIMEOUT = 1
HTTP_PORT = 80
HTTP_VERSION = 'HTTP/1.1'
DEFAULT_PATH = '/'
END_L = '\r\n'

class RequestError(ValueError):
    """Exception that is raised whenever a request is malformed."""

    def __init__(self, message: str) -> None:
        super().__init__(f'Request Error: {message}')

class Proxy():
    """A proxy that sits between a client and a server."""

    def __init__(self, port: int) -> None:
        self.listener, self.address = self.start_server(HOSTNAME, port)

    def start_server(self, host: str, port: int) -> tuple:
        """
        Creates a listening socket for the proxy.
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
        """Executes the proxy."""
        
        while True:
            conn, addr = self.listener.accept()
            client_request = conn.recv(BUF_SZ)
            try:
                host, port, path = self.parse_request(client_request)
            except RequestError as e:
                print(e)
                conn.close()
                continue
            server_request = self.generate_request(host, port, path)
            print(server_request)
            try:
                response = self.send_request(server_request, (host, port))
            except Exception as e:
                print(e)
                conn.close()
                continue
            conn.sendall(response)
            conn.close()

    @staticmethod
    def parse_request(request: bytes) -> tuple:
        """
        Parses and checks validity of incoming request.
        :param request: The initial request received from the client
        :return: The hostname, port, and path of the requested resource
        :raises RequestError: Invalid request
        """

        method, uri, http_version = request.decode('UTF-8').split()
        uri = urlparse(uri)
        if not method == 'GET':
            raise RequestError('Unsupported HTTP method')
        if not uri.hostname:
            raise RequestError('Invalid URI')
        if not http_version == HTTP_VERSION:
            raise RequestError('Unsupported HTTP version')
        port = uri.port if uri.port else HTTP_PORT
        path = uri.path if uri.path else DEFAULT_PATH
        return uri.hostname, port, path

    @staticmethod
    def generate_request(host: str, port: int, path: str) -> str:
        """
        Generates a request in HTTP message format.
        :param host: The host of the server to send the request to
        :param port: The port of the server to send the request to
        :param path: The path of the resource being requested
        :return: A request in HTTP message format
        """

        return f'GET {path} {HTTP_VERSION}{END_L}' \
               f'Host: {host}{END_L}' \
               f'Connection: close{END_L*2}'

    @staticmethod
    def send_request(request: str, address: tuple) -> bytes:
        """
        Sends a request to a server.
        :param request: The request to send
        :param address: The address of the server
        :return: The response to the request
        """
        
        with socket(AF_INET, SOCK_STREAM) as server:
            server.connect(address)
            server.settimeout(TIMEOUT)
            server.sendall(request.encode('UTF-8'))
            return server.recv(BUF_SZ)
            # response = server.recv(BUF_SZ)
            # return response.decode('UTF-8')

def main() -> None:
    """Runs the web proxy program."""
        
    if len(sys.argv) != 2:
        print('USAGE: python3 proxy.py <port>')
        exit(1)
    proxy = Proxy(int(sys.argv[1]))
    proxy.run()

if __name__ == '__main__':
    main()