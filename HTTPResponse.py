"""
HTTPResponse
:file: HTTPResponse.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0
"""

HTTP_VERSION, END_L = 1.1, '\r\n'

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
        self.version = status_line[0].split('HTTP/')[1]
        self.status_code = int(status_line[1])
        self.status_message = ' '.join(status_line[2:])
        self.headers = {}
        for header in headers[1:]:
            key, value = header.split(':', 1)
            self.modify_header(key, value.strip())
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
        response = f'HTTP/{HTTP_VERSION} {status_code} {message}{END_L}' \
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

        status_line = f'HTTP/{self.version} {self.status_code} {self.status_message}'
        headers = ''.join([f'{key}: {value}{END_L}' for key, value in self.headers.items()])
        return END_L.join([status_line, headers, self.body])

    def __bytes__(self) -> bytes:
        """Retrieves the bytestring representation of an HTTPResponse object."""

        return self.__repr__().encode('UTF-8')