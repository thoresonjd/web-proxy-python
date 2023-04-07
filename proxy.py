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
INTRNL_ERR = 500
HTTP_PORT = 80
HTTP_VERSION = 'HTTP/1.1'
HTTP_METHODS = {'GET'}
HTTP_CODES = {200, 404, INTRNL_ERR}
CACHE_DIR = 'cache'
DEFAULT_PATH = '/'
END_L = '\r\n'

class RequestError(ValueError):
    """Exception that is raised whenever a request is malformed."""

    def __init__(self, message: str) -> None:
        super().__init__(f'Request Error: {message}')

class Cache():
    """A class that manages cached HTTP queries."""

    def __init__(self, dir: str) -> None:
        """
        Creates a cache.
        :param dir: The directory of the cache
        """

        self.path = Path(f'./{dir}')
        self.path.mkdir()

class Proxy():
    """A proxy that caches HTTP traffic between clients and servers."""

    def __init__(self, port: int) -> None:
        """Initializes the proxy."""

        self.listener, self.address = self.start_server(port)
        self.cache = Cache(CACHE_DIR)

    def start_server(self, port: int) -> tuple:
        """
        Creates a listening socket on for the proxy on the current host.
        :param port: The port number to listen from
        :return: The listening socket and the socket's address
        """

        address = (HOSTNAME, port)
        server = socket(AF_INET, SOCK_STREAM)
        server.bind(address)
        server.listen(BACKLOG)
        return server, address

    def run(self) -> None:
        """Executes the proxy."""
        
        while True:
            conn, addr = self.listener.accept()
            client_request = conn.recv(BUF_SZ).decode('UTF-8')
            try:
                method, host, port, path = self.parse_request(client_request)
            except RequestError as e:
                print(e)
                response = self.generate_response(INTRNL_ERR, 'Internal Server Error', False)
            else:
                server_request = self.generate_request(method, host, port, path)
                print(server_request)
                response = self.send_request(server_request, (host, port))
                if self.status_code(response) not in HTTP_CODES:
                    response = self.generate_response(INTRNL_ERR, 'Internal Server Error', False)
            conn.sendall(response.encode('UTF-8'))
            conn.close()

    @staticmethod
    def parse_request(request: str) -> tuple:
        """
        Parses and checks validity of incoming request.
        :param request: The initial request received from the client
        :return: The hostname, port, and path of the requested resource
        :raises RequestError: Invalid request
        """

        method, uri, http_version = request.split()
        uri = urlparse(uri)
        if method.upper() not in HTTP_METHODS:
            raise RequestError(f'Unsupported or unrecognized HTTP method: {method}')
        if not uri.hostname:
            raise RequestError('Invalid URI')
        if not http_version == HTTP_VERSION:
            raise RequestError('Unsupported HTTP version')
        port = uri.port if uri.port else HTTP_PORT
        path = uri.path if uri.path else DEFAULT_PATH
        return method, uri.hostname, port, path

    @staticmethod
    def status_code(response: str) -> int:
        """Determines the status code of a response."""
        
        return int(response.split()[1])

    @staticmethod
    def generate_request(method: str, host: str, port: int, path: str) -> str:
        """
        Generates a request in HTTP message format.
        :param method: The HTTP method of the request
        :param host: The host of the server to send the request to
        :param port: The port of the server to send the request to
        :param path: The path of the resource being requested
        :return: An HTTP request
        """

        return f'{method.upper()} {path} {HTTP_VERSION}{END_L}' \
               f'Host: {host}{END_L}' \
               f'Connection: close{END_L*2}'

    @staticmethod
    def generate_response(status_code: int, message: str, hit: bool) -> str:
        """
        Generates a response in HTTP message format.
        :param status_code: The status code of the response
        :param message: The status message of the response
        :param hit: True if there was a cache hit, False otherwise
        :return: An HTTP response
        """

        return f'{HTTP_VERSION} {status_code} {message}{END_L}' \
               f'Cache-Hit: {int(hit)}{END_L}' \
               f'Connection: close{END_L*2}'

    @staticmethod
    def send_request(request: str, address: tuple) -> str:
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
            return server.recv(BUF_SZ).decode('UTF-8')

def has_valid_args() -> bool:
    """Checks the validity of command line arguments."""

    return len(sys.argv) == 2 and sys.argv[1].isdigit()


def main() -> None:
    """Runs the web proxy program."""
        
    if not has_valid_args():
        print('USAGE: python3 proxy.py <PORT>')
        exit(1)
    port = int(sys.argv[1])
    proxy = Proxy(port)
    proxy.run()

if __name__ == '__main__':
    main()