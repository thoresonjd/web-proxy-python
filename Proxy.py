"""
Proxy
:file: Proxy.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0
"""

from Cache import Cache
from HTTPRequest import HTTPRequest
from HTTPResponse import HTTPResponse
from RequestError import RequestError
from socket import *

HOSTNAME, BUF_SZ, BACKLOG, TIMEOUT = 'localhost', 4096, 5, 1
OK, NOT_FOUND, INTRNL_ERR = 200, 404, 500
HTTP_CODES = {OK, NOT_FOUND, INTRNL_ERR}

class Proxy(object):
    """A proxy that caches HTTP traffic between clients and servers."""

    def __init__(self, port: int) -> None:
        """Initializes the proxy."""

        self.listener, self.address = self.__start_server(port)
        self.cache = Cache()

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
        
        try:
            while True:
                self.__resolve()
        except KeyboardInterrupt:
            print('\nShutting down...')
            self.listener.close()

    def __resolve(self) -> None:
        """Resolves an incoming client connection and request."""

        print('\n\n******************** Ready to serve ********************')
        conn, addr = self.listener.accept()
        print(f'Received client connection from {addr}')
        try:
            request = conn.recv(BUF_SZ)
            print(f'Received message from client: {request}')
            request = HTTPRequest(request)
        except RequestError as e:
            print(e)
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

        print('Yay! The requested file was found in the cache!')
        body = self.cache.read(uri)
        return HTTPResponse.create_response(OK, 'OK', body)

    def __forward_to_server(self, request: HTTPRequest) -> HTTPResponse:
        """
        Forwards a client request to the requested server.
        :param request: The original HTTP request
        :return: The response to the request
        """

        print('Oops! No cache hit! Requesting origin server for the file...')
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
            print('Response received from server')
            print(f'Status code is {response.get_status_code()}')
            if response.get_status_code() == OK:
                print(f'Writing to cache...')
                self.cache.write(request.get_uri(), response.get_body())
            elif response.get_status_code() not in HTTP_CODES:
                response = HTTPResponse.create_response(INTRNL_ERR, 'Internal Server Error',)
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
        except (timeout, gaierror, ConnectionRefusedError) as e:
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