import codecs
import queue
import socket
import ssl
import time

from .utils import networking


class Session:
    def __init__(self, sock: socket.socket, listener):
        self.__socket = sock
        self.__listener = listener

        self.__rhost, self.__rport = sock.getpeername()
        self.__encoding = "utf-8"
        self.__session_hash = networking.create_session_hash(self.rhost, self.rport)
        self.__commands_queue = queue.Queue()

        self.__on_read = lambda _: None
        self.__on_write = lambda _: None
        self.__on_error = lambda _: None

        self.interactive = False
        self.extended_info = {}

    def set_callbacks(self, read_callback=None, write_callback=None, error_callback=None):
        # TODO ADD REFERENCE TO NOTE IN project94.py
        if read_callback:
            self.__on_read = read_callback
        if write_callback:
            self.__on_write = write_callback
        if error_callback:
            self.__on_error = error_callback

    @property
    def socket(self) -> socket.socket:
        return self.__socket

    @property
    def listener(self):
        return self.__listener

    @property
    def rhost(self):
        return self.__rhost

    @property
    def rport(self):
        return self.__rport

    @property
    def ssl_enabled(self):
        return isinstance(self.__socket, ssl.SSLSocket)

    @property
    def hash(self):
        return self.__session_hash

    @property
    def encoding(self):
        return self.__encoding

    @encoding.setter
    def encoding(self, value):
        try:
            codecs.lookup(value)
        except LookupError:
            self.__encoding = "utf-8"
        else:
            self.__encoding = value

    def next_command(self):
        if not self.__commands_queue.empty():
            return self.__commands_queue.get_nowait()
        return None

    def send_command(self, command):
        if not self.interactive:
            print(f"> \"{command}\" -> {self.rhost}:{self.rport}")
        self.__commands_queue.put_nowait(f"{command}\n")
        self.__on_write(self)

    def send_command_and_recv(self, command: str, return_raw: bool = False) -> str | bytes | None:
        try:
            self.__on_read(self)
            time.sleep(1)
            if not command.endswith('\n'):
                command += '\n'
            self.socket.send(command.encode(self.__encoding))
            data = networking.recvall(self.socket)
            try:
                if not return_raw:
                    data = data.decode(self.__encoding)
            except (UnicodeError, UnicodeDecodeError):
                return None
            else:
                return data
        finally:
            self.__on_read(self)

    def kill(self):
        self.__on_error(self)

    def __str__(self):
        return f"{self.hash[:8]} <{self.rhost}:{self.rport}>"
