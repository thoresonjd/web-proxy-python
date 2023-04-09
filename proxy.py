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

class HTTPResponse(object):
    """A wrapper class for an HTTP response."""

    def __init__(self, response: str) -> None:
        """
        Initializes an HTTP response object.
        :param response: The original HTTP response
        """

        self.parse_response(response)

    def parse_response(self, response: bytes) -> None:
        """
        Parses the contents of an HTTP response.
        :param response: The original HTTP response
        """

        parsed = response.decode('UTF-8').split(END_L*2)
        headers = parsed[0].split(END_L)
        status_line = headers[0].split()
        self.version = status_line[0]
        self.status_code = int(status_line[1])
        self.status_message = ' '.join(status_line[2:])
        self.headers = {}
        for header in headers[1:]:
            self.modify_header(*header.split(': ', 1))
        self.body = parsed[1] if len(parsed) > 1 else ''

    def modify_header(self, key: str, value: str) -> None:
        """
        Adds or updates a header to the response.
        :param key: The header's name
        :param value: The header's value
        """

        self.headers[key] = value

    def has_full_body(self) -> bool:
        """Determines if the full body of a response is contained."""

        return len(self.body.encode('UTF-8')) == int(self.headers['Content-Length'])

    def extend_body(self, addend: str) -> None:
        """Extends the body of the response."""

        self.body = ''.join([self.body, addend])

    def get_status_code(self) -> int:
        """Retrieves the status code of the response."""

        return self.status_code

    def get_header(self, key: str) -> str:
        """
        Retrieves the value of a header within the response.
        :param key: The name of the header to get the value for
        """

        return self.headers[key]

    def get_body(self) -> str:
        """Retrieves the body of the response."""

        return self.body

    def __repr__(self) -> str:
        status_line = f'{self.version} {self.status_code} {self.status_message}'
        headers = ''.join([f'{key}: {value}{END_L}' for key, value in self.headers.items()])
        return END_L.join([status_line, headers, self.body])

    def __bytes__(self) -> bytes:
        return self.__repr__().encode('UTF-8')


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
    
    def write(self, uri: str, response: str) -> None:
        """
        Adds a web page response of a request to a cache.
        :param uri: The URI of the HTTP requested
        :param response: The response of the request
        """

        filename = self.to_filename(uri)
        path = Path(f'{self.dir}/{filename}')
        path.write_text(response)

    def read(self, uri: str) -> str:
        """Retrieves a cached response corresponding to a requested URI."""

        filename = self.to_filename(uri)
        path = Path(f'{self.dir}/{filename}')
        return path.read_text()

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
            print('\n\n******************** Ready to serve ********************')
            conn, addr = self.listener.accept()
            print(f'Received client connection from {addr}')
            client_request = conn.recv(BUF_SZ).decode('UTF-8')
            print(f'Received message from client:\n{client_request}')
            try:
                method, host, port, path = self.parse_request(client_request)
            except RequestError as e:
                print(e)
                response = self.generate_response(INTRNL_ERR, 'Internal Server Error')
            else:
                uri = f'{host}{path}'
                is_cached = self.cache.is_cached(uri)
                if is_cached:
                    print('Yay! The requested file is in the cache...')
                    body = self.cache.read(uri)
                    response = self.generate_response(OK, 'OK', body)
                else:
                    print('Oops! No cache hit! Requesting origin server for the file..')
                    server_request = self.generate_request(method, host, port, path)
                    print(f'Sending the following message to proxy to server:\n{server_request}')
                    response = self.transmit_request(server_request, (host, port))
                    print('Response received from server...')
                    if response.get_status_code() == OK:
                        print(f'Status code is {OK}, caching...')
                        self.cache.write(uri, response.get_body())
                    elif response.get_status_code() not in HTTP_CODES:
                        response = self.generate_response(INTRNL_ERR, 'Internal Server Error', response.get_body())
            response.modify_header('Cache-Hit', int(is_cached))
            print('Now responding to the client...')
            conn.sendall(bytes(response))
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
    def generate_response(status_code: int, message: str, body: str = '') -> str:
        """
        Generates a response in HTTP message format.
        :param status_code: The status code of the response
        :param message: The status message of the response
        :param body: The body of the response
        :return: An HTTP response
        """

        content_length = len(body.encode('UTF-8'))
        response = f'{HTTP_VERSION} {status_code} {message}{END_L}' \
                   f'Content-Length: {content_length}{END_L}' \
                   f'Connection: close{END_L*2}' \
                   f'{body}'
        return HTTPResponse(response.encode('UTF-8'))

    @staticmethod
    def transmit_request(request: str, address: tuple) -> str:
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
            response = HTTPResponse(server.recv(BUF_SZ))
            if not response.has_full_body():
                body = response.get_body()
                received = len(body.encode('UTF-8'))
                content_length = int(response.get_header('Content-Length'))
                while received < content_length:
                    data = server.recv(BUF_SZ)
                    if not data: break
                    received += len(data)
                    response.extend_body(data.decode('UTF-8'))
            return response

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