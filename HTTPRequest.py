"""
HTTPRequest
:file: HTTPRequest.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0
"""

from RequestError import RequestError
from urllib.parse import urlparse

HTTP_PORT, HTTP_VERSION, HTTP_METHODS = 80, 1.1, {'GET'}
DEFAULT_PATH, END_L = '/', '\r\n'

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

        method, uri, version, headers = self.__decode_request(request)
        self.method = self.__parse_method(method)
        self.version = self.__parse_version(version)
        self.headers = self.__parse_headers(headers)
        self.host, self.port, self.path, self.uri = self.__parse_uri(uri, self.headers)

    @staticmethod
    def __decode_request(request: bytes) -> tuple:
        """Decodes the bytestring request."""

        try:
            parsed = request.decode('UTF-8').split(END_L)
        except UnicodeDecodeError as e:
            raise RequestError('Can not decode request')
        request_line = parsed[0].split()
        if len(request_line) != 3:
            raise RequestError('Malformed request')
        method, uri, version = request_line
        headers = parsed[1:]
        return method, uri, version, headers

    @staticmethod
    def __parse_method(method: str) -> str:
        """Parses an HTTP method."""

        parsed_method = method.upper()
        if parsed_method not in HTTP_METHODS:
            raise RequestError(f'Unsupported or unrecognized HTTP method: {method}') 
        return parsed_method 

    @staticmethod
    def __parse_version(version: str) -> float:
        """Parses an HTTP version."""

        if not 'HTTP/' == version[:5] or not version[5:].replace('.', '', 1).isdigit():
            raise RequestError(f'Unrecognized HTTP version: {version}')
        version = float(version[5:])
        if version > HTTP_VERSION:
            raise RequestError(f'Unsupported HTTP version: {version}')
        return version

    @staticmethod
    def __parse_headers(headers: list) -> dict:
        """Parses headers within a request."""

        parsed_headers = {}
        for header in headers:
            if header:
                key, value = header.split(':', 1)
                parsed_headers[key] = value.strip()
        return parsed_headers

    @staticmethod
    def __parse_uri(uri: str, headers: dict) -> tuple:
        """Parses the URI of a request."""

        parsed_uri = urlparse(uri)
        if not parsed_uri.hostname and 'Host' not in headers:
            raise RequestError('Malformed request: Invalid URI')
        host = parsed_uri.hostname if parsed_uri.hostname else headers['Host']
        port = parsed_uri.port if parsed_uri.port else HTTP_PORT
        path = parsed_uri.path if parsed_uri.path else DEFAULT_PATH
        uri = f'{host}{path}'
        return host, port, path, uri

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

        request = f'{method.upper()} {path} HTTP/{HTTP_VERSION}{END_L}' \
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

        request_line = f'{self.method} {self.path} HTTP/{self.version}'
        headers = ''.join([f'{key}: {value}{END_L}' for key, value in self.headers.items()])
        return f'{request_line}{END_L}{headers}{END_L}'

    def __bytes__(self) -> bytes:
        """Retrieves the bytestring representation of an HTTPRequest object."""

        return self.__repr__().encode('UTF-8')