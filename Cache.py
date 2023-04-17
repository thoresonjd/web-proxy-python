"""
Cache
:file: Cache.py
:author: Justin Thoreson
:date: 19 April 2023
:version: 1.0
"""

from pathlib import Path

CACHE_DIR, DEFAULT_FILENAME = 'cache', 'idx'

class Cache(object):
    """A class that manages cached HTTP queries."""

    def __init__(self) -> None:
        """
        Creates a cache or clears it if one does already exists.
        :param dir: The directory of the cache
        """

        self.dir = f'./{CACHE_DIR}'
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
                Cache.__clear_cache(child)
                child.rmdir()
    
    def write(self, uri: str, response: str) -> None:
        """
        Adds a web page response of a request to a cache.
        :param uri: The URI of the HTTP requested
        :param response: The response of the request
        """

        path = Path(self.__create_file_path(uri))
        path.write_text(response)

    def read(self, uri: str) -> str:
        """Retrieves a cached response corresponding to a requested URI."""

        return Path(self.__get_file_path(uri)).read_text()

    def is_cached(self, uri: str) -> bool:
        """
        Checks is a web page response is cached.
        :param uri: The URI of the HTTP request
        :return: True if the response is cached, False otherwise
        """

        return Path(self.__get_file_path(uri)).exists()

    def __create_file_path(self, uri: str) -> str:
        """Creates a file path from the URI of a new response to cache."""

        segments = uri.split('/')
        directory = '/'.join([self.dir, *segments[:-1]])
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return '/'.join([directory, segments[-1] if segments[-1] else DEFAULT_FILENAME])

    def __get_file_path(self, uri: str) -> str:
        """Converts a URI to a corresponding file path."""

        return '/'.join([self.dir, f'{uri}{DEFAULT_FILENAME}' if uri[-1] == '/' else uri])