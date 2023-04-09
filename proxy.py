"""
Web Proxy
:file: proxy.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0
"""

from urllib.parse import urlparse
from pathlib import Path
from socket import *
import sys

HOSTNAME, BUF_SZ, BACKLOG, TIMEOUT = 'localhost', 4096, 5, 1
OK, NOT_FOUND, INTRNL_ERR = 200, 404, 500
HTTP_PORT, HTTP_VERSION = 80, 'HTTP/1.1'
HTTP_METHODS, HTTP_CODES = {'GET'}, {OK, NOT_FOUND, INTRNL_ERR}
CACHE_DIR = 'cache'
DEFAULT_PATH = '/'
END_L = '\r\n'

class RequestError(ValueError):
    """Exception that is raised whenever a request is malformed."""

    def __init__(self, message: str) -> None:
        super().__init__(f'Request Error: {message}')

class Cache(object):
    """A class that manages cached HTTP queries."""

    def __init__(self, dir: str) -> None:
        """
        Creates a cache or clears it if one does already exists.
        :param dir: The directory of the cache
        """

        self.dir = f'./{dir}'
        path = Path(self.dir)
        if path.exists():
            self.clear_cache(path)
        else:
            path.mkdir()
    
    @staticmethod
    def clear_cache(path: Path) -> None:
        """
        Recursively clears all files from the cache.
        :param path: A path object to clear files from
        """

        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                clear_cache(child)
    
    def add(self, uri: str, response: str) -> None:
        """
        Adds a web page response of a request to a cache.
        :param uri: The URI of the HTTP requested
        :param response: The response of the request
        """

        filename = self.to_filename(uri)
        path = Path(f'{self.dir}/{filename}')
        path.write_text(response)

    def get(self, uri: str) -> str:
        """Retrieves a cached response corresponding to a requested URI."""

        filename = self.to_filename(uri)
        path = Path(f'{self.dir}/{filename}')
        path.read_text()

    def is_cached(self, uri: str) -> bool:
        """
        Checks is a web page response is cached.
        :param uri: The URI of the HTTP request
        :return: True if the response is cached, False otherwise
        """

        filename = self.to_filename(uri)
        return Path(f'{self.dir}/{filename}').exists()

    @staticmethod
    def to_filename(uri: str) -> str:
        """Converts a URI to a corresponding filename."""

        return ''.join([uri.replace('/', '$$$'), '.html'])

class Proxy(object):
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
            print('\n******************** Ready to serve ********************')
            conn, addr = self.listener.accept()
            print(f'Received client connection from {addr}')
            client_request = conn.recv(BUF_SZ).decode('UTF-8')
            print(f'Received message from client: {client_request}')
            try:
                method, host, port, path = self.parse_request(client_request)
            except RequestError as e:
                print(e)
                response = self.generate_response(INTRNL_ERR, 'Internal Server Error', False)
            else:
                uri = f'{host}{path}'
                if self.cache.is_cached(uri):
                    print('Yay! The requested file is in the cache...')
                    body = self.cache.get(uri)
                    response = self.generate_response(OK, 'OK', True, body)
                else:
                    print('Oops! No cache hit! Requesting origin server for the file..')
                    server_request = self.generate_request(method, host, port, path)
                    print(f'Sending the following message to proxy to server: {server_request}')
                    headers, body = self.send_request(server_request, (host, port))
                    status_code = self.status_code(headers)
                    print('Response received from server...')
                    if status_code == OK:
                        print(f'Status code it {OK}, caching...')
                        self.cache.add(uri, body)
                        response = f'{headers}{body}'
                    elif status_code not in HTTP_CODES:
                        response = self.generate_response(INTRNL_ERR, 'Internal Server Error', False, body)
            print('Now responding to the client...')
            conn.sendall(response.encode('UTF-8'))
            print('All done! Closing socket...')
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
    def status_code(headers: str) -> int:
        """Retrieves the status code of a response."""
        
        return int(headers.split()[1])

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
    def generate_response(status_code: int, message: str, hit: bool, body: str) -> str:
        """
        Generates a response in HTTP message format.
        :param status_code: The status code of the response
        :param message: The status message of the response
        :param hit: True if there was a cache hit, False otherwise
        :param body: The body of the response
        :return: An HTTP response
        """

        content_length = len(body.encode('UTF-8'))
        return f'{HTTP_VERSION} {status_code} {message}{END_L}' \
               f'Content-Length: {content_length}'
               f'Cache-Hit: {int(hit)}{END_L}' \
               f'Connection: close{END_L*2}' \
               f'{body}{END_L}'

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
            response = server.recv(BUF_SZ).decode('UTF-8')
            tokens = response.split(END_L*2)
            headers = tokens[0]
            body = tokens[1] if len(tokens) > 1 else ''
            content_length = 0
            for header in headers.split(END_L):
                if header.lower().find('content-length') > -1:
                    content_length = int(header.split(':')[1].strip())
            received = len(body.encode('UTF-8'))
            while received < content_length:
                data = server.recv(BUF_SZ)
                if not data: break
                received += len(data)
                body += data.decode('UTF-8')
            return headers, body

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