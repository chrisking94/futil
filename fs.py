from abc import ABC, abstractmethod
from webdav3.client import Client


class FilesystemClient(ABC):
    @abstractmethod
    def upload(self, local_fp: str, remote_fp: str):
        pass

    @abstractmethod
    def download(self, remote_fp: str, local_fp: str):
        pass

    @abstractmethod
    def makedirs(self, remote_path: str):
        pass


class WebDAVFolder(FilesystemClient):
    def __init__(self, host, username, password):
        options = {
            'webdav_hostname': host,
            'webdav_login': username,
            'webdav_password': password
        }
        client = Client(options)
        client.verify = True  # To not check SSL certificates (Default = True)
        self.client = client

    def upload(self, local_fp: str, remote_fp: str):
        self.client.upload(remote_fp, local_fp)

    def download(self, remote_fp: str, local_fp: str):
        self.client.download(remote_fp, local_fp)

    def makedirs(self, remote_path: str):
        self.client.mkdir(remote_path)
