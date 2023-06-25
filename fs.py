import io
from abc import ABC, abstractmethod
from webdav3.client import Client


class FilesystemClient(ABC):
    def __init__(self, root: str):
        self._root = root

    @abstractmethod
    def upload(self, r_buff, remote_path: str):
        pass

    @abstractmethod
    def download(self, remote_path: str, r_buff):
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

    def upload(self, r_buff, remote_path: str):
        self.client.upload_to(r_buff, self._abspath(remote_path))

    def download(self, remote_path: str, w_buff):
        self.client.download_from(w_buff, self._abspath(remote_path))

    def makedirs(self, remote_path: str):
        self.client.mkdir(self._abspath(remote_path))
