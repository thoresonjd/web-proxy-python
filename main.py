"""
Web Proxy
:file: main.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0

A simple proxy server that resolves HTTP requests between clients and servers.
Successful responses (status code 200) are stored within a cache directory.

Supports:
- HTTP/1.1 and earlier
- GET requests
- Status codes 200, 404, and 500

Since the proxy supports up to HTTP/1.1 but uses non-persistent connections, it
really just supports HTTP/1.0. Thus, we can humorously think of this proxy as
supporting HTTP/1.05.
"""

from Proxy import Proxy
import sys

MIN_PORT, MAX_PORT = 10000, 65535

def has_valid_args() -> bool:
    """Checks the validity of command line arguments."""

    return len(sys.argv) == 2 and \
        sys.argv[1].isdigit() and \
        MIN_PORT <= int(sys.argv[1]) <= MAX_PORT

def main() -> None:
    """Runs the web proxy program."""
        
    if not has_valid_args():
        print('USAGE: python3 proxy.py <PORT>')
        print(f'PORT must be a valid, unreserved TCP port between {MIN_PORT} and {MAX_PORT}')
        exit(1)
    port = int(sys.argv[1])
    try:
        proxy = Proxy(port)
    except OSError as e:
        print(f'Could not execute the web proxy: {e}')
    else:
        proxy.run()  

if __name__ == '__main__':
    main()