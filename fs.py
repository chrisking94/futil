from abc import ABC, abstractmethod
from webdav3.client import Client


class FilesystemClient(ABC):
    def __init__(self, root: str):
        self._root = root

    @abstractmethod
    def upload(self, local_path: str, remote_path: str):
        pass

    @abstractmethod
    def upload_buffer(self, buffer, remote_path: str):
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str):
        pass

    @abstractmethod
    def makedirs(self, remote_path: str):
        pass

    def _abspath(self, remote_path: str):
        return self._root + remote_path


class WebDAVFolder(FilesystemClient):
    def __init__(self, host, username, password, root="/"):
        super().__init__(root)
        options = {
            'webdav_hostname': host,
            'webdav_login': username,
            'webdav_password': password
        }
        client = Client(options)
        client.verify = True  # To not check SSL certificates (Default = True)
        self.client = client

    def upload(self, local_path: str, remote_path: str):
        self.client.upload(self._abspath(remote_path), local_path)

    def download(self, remote_path: str, local_path: str):
        self.client.download(self._abspath(remote_path), local_path)

    def makedirs(self, remote_path: str):
        self.client.mkdir(self._abspath(remote_path))
