import codecs
import socket
import ssl
import time

from .utils.networking import create_session_hash


class Session:
    def __init__(self, sock: socket.socket, listener):
        self.__socket = sock
        self.__listener = listener

        self.__rhost, self.__rport = sock.getpeername()
        self.__encoding = "utf-8"
        self.__session_hash = networking.create_session_hash(self.rhost, self.rport)
        self.__timestamp = time.time()

        self.recv_data = []
        self.interactive = False
        self.extended_info = {}

    @property
    def socket(self) -> socket.socket | ssl.SSLSocket:
        """
        :return: Session `socket` object
        """
        return self.__socket

    @property
    def listener(self):
        """
        :return: Pointer to listener that accept this session
        """
        return self.__listener

    @property
    def rhost(self):
        """
        :return: Remote address
        """
        return self.__rhost

    @property
    def rport(self):
        """
        :return: Remote port
        """
        return self.__rport

    @property
    def ssl_enabled(self):
        """
        Is ssl enabled
        :return: `True` if ssl enabled and active
        """
        return isinstance(self.__socket, ssl.SSLSocket)

    @property
    def cert(self) -> dict:
        """
        Alias for SSLSocket.getpeercert()
        :return: `dict` that contain certificate
        """
        return self.socket.getpeercert()

    @property
    def hash(self) -> str:
        return self.__session_hash

    @property
    def encoding(self) -> str:
        return self.__encoding

    @encoding.setter
    def encoding(self, value):
        try:
            codecs.lookup(value)
        except LookupError:
            self.__encoding = "utf-8"
        else:
            self.__encoding = value

    @property
    def timestamp(self):
        return self.__timestamp

    def __str__(self):
        return f"{self.hash[:8]} <{self.rhost}:{self.rport}>"
