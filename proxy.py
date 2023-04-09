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

class HTTPRequest(object):
    """A wrapper class for an HTTP request."""

    def __init__(self, request: bytes) -> None:
        """
        Initializes an HTTP request object.
        :param request: The original HTTP request
        """

        self.__parse_request(request)

    def __parse_request(self, request: bytes) -> None:
        """
        Parses and validates the contents of an HTTP request.
        :param request: The original HTTP request
        :raises RequestError: Invalid request
        """

        parsed = request.decode('UTF-8').split(END_L)
        request_line = parsed[0].split()
        if len(request_line) != 3:
            raise RequestError('Malformed request')
        method, uri, self.version = request_line
        self.method = method.upper()
        if self.method not in HTTP_METHODS:
            raise RequestError(f'Unsupported or unrecognized HTTP method: {method}')
        if not self.version == HTTP_VERSION:
            raise RequestError('Unsupported HTTP version')
        self.headers = {}
        for header in parsed[1:]:
            if header:
                self.modify_header(*header.split(': ', 1))
        uri = urlparse(uri)
        if not uri.hostname and 'Host' not in self.headers:
            raise RequestError('Malformed request: Invalid URI')
        self.host = uri.hostname if uri.hostname else self.headers['Host']
        self.port = uri.port if uri.port else HTTP_PORT
        self.path = uri.path if uri.path else DEFAULT_PATH
        self.uri = f'{self.host}{self.path}'

    def modify_header(self, key: str, value: str) -> None:
        """
        Adds or updates a header to the request.
        :param key: The header's name
        :param value: The header's value
        """

        self.headers[key] = value

    @classmethod
    def create_request(cls, method: str, host: str, path: str) -> 'HTTPRequest':
        """
        Generates a request in HTTP message format.
        :param method: The HTTP method of the request
        :param host: The host of the server to send the request to
        :param path: The path of the resource being requested
        :return: An HTTP request
        """

        request = f'{method.upper()} {path} {HTTP_VERSION}{END_L}' \
                  f'Host: {host}{END_L}' \
                  f'Connection: close{END_L*2}'
        return cls(request.encode('UTF-8'))

    def get_method(self) -> str:
        """Retrieves the method of the request."""

        return self.method
    
    def get_uri(self) -> str:
        """Retrieves the URI of the request."""

        return self.uri

    def get_host(self) -> str:
        """Retrieves the hostname of the request."""

        return self.host

    def get_port(self) -> int:
        """Retrieves the port of the request."""

        return self.port

    def get_path(self) -> str:
        """Retrieves the path of the request."""

        return self.path

    def __repr__(self) -> str:
        """Retrieves the string representation of an HTTPRequest object."""

        request_line = f'{self.method} {self.path} {self.version}'
        headers = ''.join([f'{key}: {value}{END_L}' for key, value in self.headers.items()])
        return f'{request_line}{END_L}{headers}{END_L}'

    def __bytes__(self) -> bytes:
        """Retrieves the bytestring representation of an HTTPRequest object."""

        return self.__repr__().encode('UTF-8')

class HTTPResponse(object):
    """A wrapper class for an HTTP response."""

    def __init__(self, response: bytes) -> None:
        """
        Initializes an HTTP response object.
        :param response: The original HTTP response
        """

        self.__parse_response(response)

    def __parse_response(self, response: bytes) -> None:
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

        self.body = f'{self.body}{addend}'

    @classmethod
    def create_response(cls, status_code: int, message: str, body: str = '') -> 'HTTPResponse':
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
        return cls(response.encode('UTF-8'))

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
        """Retrieves the string representation of an HTTPResponse object."""

        status_line = f'{self.version} {self.status_code} {self.status_message}'
        headers = ''.join([f'{key}: {value}{END_L}' for key, value in self.headers.items()])
        return END_L.join([status_line, headers, self.body])

    def __bytes__(self) -> bytes:
        """Retrieves the bytestring representation of an HTTPResponse object."""

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
            self.__clear_cache(path)
        else:
            path.mkdir()
    
    @staticmethod
    def __clear_cache(path: Path) -> None:
        """
        Recursively clears all files from the cache.
        :param path: A path object to clear files from
        """

        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                __clear_cache(child)
    
    def write(self, uri: str, response: str) -> None:
        """
        Adds a web page response of a request to a cache.
        :param uri: The URI of the HTTP requested
        :param response: The response of the request
        """

        filename = self.__to_filename(uri)
        path = Path(f'{self.dir}/{filename}')
        path.write_text(response)

    def read(self, uri: str) -> str:
        """Retrieves a cached response corresponding to a requested URI."""

        filename = self.__to_filename(uri)
        path = Path(f'{self.dir}/{filename}')
        return path.read_text()

    def is_cached(self, uri: str) -> bool:
        """
        Checks is a web page response is cached.
        :param uri: The URI of the HTTP request
        :return: True if the response is cached, False otherwise
        """

        filename = self.__to_filename(uri)
        return Path(f'{self.dir}/{filename}').exists()

    @staticmethod
    def __to_filename(uri: str) -> str:
        """Converts a URI to a corresponding filename."""

        return ''.join([uri.replace('/', '$$$'), '.html'])

class Proxy(object):
    """A proxy that caches HTTP traffic between clients and servers."""

    def __init__(self, port: int) -> None:
        """Initializes the proxy."""

        self.listener, self.address = self.__start_server(port)
        self.cache = Cache(CACHE_DIR)

    def __start_server(self, port: int) -> tuple:
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
            try:
                request = HTTPRequest(conn.recv(BUF_SZ))
                print(f'Received message from client:\n{request}')
            except RequestError as e:
                print(type(e))
                is_cached = False
                response = HTTPResponse.create_response(INTRNL_ERR, 'Internal Server Error')
            else:
                uri = request.get_uri()
                is_cached = self.cache.is_cached(uri)
                response = self.__retrieve_from_cache(uri) if is_cached else self.__forward_to_server(request)
            response.modify_header('Cache-Hit', int(is_cached))
            print('Now responding to the client...')
            conn.sendall(bytes(response))
            print('All done! Closing socket...')
            conn.close()

    def __retrieve_from_cache(self, uri: str) -> HTTPResponse:
        """
        Retrieves the web page body of a cached response.
        :param uri: The URI of the original HTTP request
        :return: An HTTP response created with the cached web page body
        """

        print('Yay! The requested file is in the cache...')
        body = self.cache.read(uri)
        return HTTPResponse.create_response(OK, 'OK', body)

    def __forward_to_server(self, request: HTTPRequest) -> HTTPResponse:
        """
        Forwards a client request to the requested server.
        :param request: The original HTTP request
        :return: The response to the request
        """

        print('Oops! No cache hit! Requesting origin server for the file..')
        server_request = HTTPRequest.create_request(
            request.get_method(),
            request.get_host(),
            request.get_path()
        )
        try:
            print(f'Sending the following message to proxy to server:\n{server_request}')
            response = self.__transmit_request(server_request)
        except RequestError as e:
            print(e)
            response = HTTPResponse.create_response(INTRNL_ERR, 'Internal Server Error')
        else:
            print('Response received from server...')
            if response.get_status_code() == OK:
                print(f'Status code is {OK}, caching...')
                self.cache.write(uri, response.get_body())
            elif response.get_status_code() not in HTTP_CODES:
                response = HTTPResponse.create_response(
                    INTRNL_ERR,
                    'Internal Server Error',
                    response.get_body()
                )
        return response

    @staticmethod
    def __transmit_request(request: HTTPRequest) -> HTTPResponse:
        """
        Sends a request to a server.
        :param request: The request to send
        :return: The response to the request
        :raises RequestError: Failed request
        """

        try:
            with socket(AF_INET, SOCK_STREAM) as server:
                address = (request.get_host(), request.get_port())
                server.connect(address)
                server.settimeout(TIMEOUT)
                server.sendall(bytes(request))
                return Proxy.__receive_response(server)
        except (timeout, gaierror) as e:
            raise RequestError(e)

    @staticmethod
    def __receive_response(sock: socket) -> HTTPResponse:
        """
        Receives a response from a server.
        :param sock: The socket gateway to the connection with the server
        :return: The response to the request
        """

        response = HTTPResponse(sock.recv(BUF_SZ))
        if response.has_full_body():
            return response
        body = response.get_body()
        received = len(body.encode('UTF-8'))
        content_length = int(response.get_header('Content-Length'))
        while received < content_length:
            data = sock.recv(BUF_SZ)
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