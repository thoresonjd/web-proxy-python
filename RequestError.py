"""
RequestError
:file: RequestError.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0
"""

class RequestError(ValueError):
    """Exception that is raised whenever a request is malformed."""

    def __init__(self, message: str) -> None:
        super().__init__(f'Request Error: {message}')   