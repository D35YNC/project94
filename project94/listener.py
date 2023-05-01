import abc
import socket
import ssl
import time
import enum

from .session import Session
from .utils import Printer
from .utils.networking import recvall

"""
LEEEEEGO
Yeahs its "state" pattern
Yeahs its overengineering
XDD
"""


__all__ = ["Listener", "ListenerInitException", "ListenerStartException"]


class ListenerStateEnum(enum.Enum):
    Ready = 0,
    Running = 1,
    Stopped = 2,


class ListenerState(metaclass=abc.ABCMeta):
    def __init__(self, listener):
        self._listener = listener

    @abc.abstractmethod
    def start(self) -> socket.socket | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def handle_connection(self, session_socket: socket.socket, session_addr: tuple[str, int], *,
                          ssl_context=None,
                          drop_duplicates=False,
                          show_banner=False) -> Session | None:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def active(self):
        raise NotImplementedError()

    @property
    def name(self):
        return self.__class__.__name__


class Running(ListenerState):
    @property
    def active(self):
        return True

    def start(self):
        Printer.error(f"{self._listener} already running")
        return None

    def stop(self):
        for s in self._listener.sockets:
            if session := self._listener.app.get_session(fd=s):
                self._listener.app.close_connection(session)
        self._listener.listen_socket.shutdown(socket.SHUT_RDWR)
        self._listener.listen_socket.close()

    def handle_connection(self, session_socket: socket.socket, session_addr: tuple[str, int], *, ssl_context=None,
                          drop_duplicates=False, show_banner=False) -> Session | None:
        if ssl_context:
            try:
                session_socket = ssl_context.wrap_socket(session_socket, True)
            except ssl.SSLCertVerificationError:
                Printer.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. Bad certificate")
                return None
            except ssl.SSLError as ex:
                Printer.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. {ex}")
                return None

        if drop_duplicates:
            for s in self._listener.sockets:
                if s.getpeername() == session_addr:
                    Printer.warning("Detect the same host connection, dropping...")
                    session_socket.shutdown(socket.SHUT_RDWR)
                    session_socket.close()
                    return None

        if not show_banner:
            try:
                session_socket.send("pwd\n".encode())
            except (OSError, socket.error, ssl.SSLError) as ex:
                Printer.error(f"{session_addr[0]}:{session_addr[1]} dies from cringe")
                Printer.error(str(ex))
                return None
            else:
                time.sleep(1)
                recvall(session_socket)

        Printer.info(f"New session: {session_addr[0]}:{session_addr[1]}")

        self._listener.sockets.append(session_socket)
        return Session(session_socket, self._listener)


class Stopped(ListenerState):
    @property
    def active(self):
        return False

    def start(self):
        Printer.error("Listener is not ready to start")
        return None

    def stop(self):
        Printer.warning(f"{self._listener} is not running")

    def handle_connection(self, session_socket: socket.socket, session_addr: tuple[str, int], *, ssl_context=None,
                          drop_duplicates=False, show_banner=False) -> Session | None:
        Printer.error("Cant handle connection when listener is stopped")
        return None


class Ready(ListenerState):
    def start(self) -> socket.socket | None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self._listener.lhost, self._listener.lport))
        except OSError as ex:
            Printer.error(str(ex))
            self._listener.change_state(ListenerStateEnum.Stopped)
            return None
        else:
            sock.listen(0x10)
            self._listener.change_state(ListenerStateEnum.Running)
            return sock

    def stop(self):
        Printer.warning(f"{self._listener} is not running")

    def handle_connection(self, session_socket: socket.socket, session_addr: tuple[str, int], *, ssl_context=None,
                          drop_duplicates=False, show_banner=False) -> Session | None:
        Printer.error("Cant handle connection when listener is stopped")
        return None

    @property
    def active(self):
        return False


class Listener:
    def __init__(self, app, name: str, ip: str, port: int, enable_ssl: bool = False, autorun: bool = False):
        if app is None:
            raise ListenerInitException("App is None")
        if name.strip() == "" or ' ' in name:
            raise ListenerInitException("Incorrect name")
        if not isinstance(port, int):
            raise ListenerInitException("Port is not int")
        elif not (0 < port < 0xFFFF):
            raise ListenerInitException("Port is not in range 0-65535")

        self.app = app
        self.__name = name
        self.__lhost = ip
        self.__lport = port
        self.__accepted_sockets = []
        self.__states = {ListenerStateEnum.Ready: Ready(self),
                         ListenerStateEnum.Running: Running(self),
                         ListenerStateEnum.Stopped: Stopped(self)}
        self.__socket: socket.socket = None
        self.__ca = []
        self.__cert = []
        self.__autorun = autorun
        self.__ifr = True  # Its First Run flag
        self.__ssl_context: ssl.SSLContext = None
        if enable_ssl:
            self.__ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__ssl_context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            self.__ssl_context.set_ciphers("ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES256-SHA384")
            self.__state = self.__states[ListenerStateEnum.Stopped]
        else:
            self.__state = self.__states[ListenerStateEnum.Ready]

    def load_ca(self, cafile):
        if self.ssl_enabled:
            try:
                self.__ssl_context.load_verify_locations(cafile=cafile)
            except (ssl.SSLError, OSError) as ex:
                Printer.error(f"Cant load {cafile}: {ex}")
                return False
            else:
                self.__ca.append(cafile)

                if 0 < len(self.__ca) and 0 < len(self.__cert):
                    self.change_state(ListenerStateEnum.Ready)
                return True
        else:
            Printer.warning("SSL not enabled")
        return False

    def load_cert(self, certfile, keyfile=None):
        if self.ssl_enabled:
            try:
                self.__ssl_context.load_cert_chain(certfile, keyfile)
            except (ssl.SSLError, OSError) as ex:
                Printer.error(f"Cant load cert or key: {ex}")
                return False
            else:
                self.__cert.append((certfile, keyfile))

                if 0 < len(self.__ca) and 0 < len(self.__cert):
                    self.change_state(ListenerStateEnum.Ready)
                return True
        else:
            Printer.warning("SSL not enabled")
        return False

    def start(self) -> socket.socket | None:
        self.__socket = self.__state.start()
        return self.__socket

    def stop(self):
        self.__state.stop()

    def restart(self) -> socket.socket | None:
        self.stop()
        return self.start()

    @property
    def is_running(self):
        return self.__state is self.__states[ListenerStateEnum.Running] and self.__socket is not None

    @property
    def listen_socket(self) -> socket.socket:
        return self.__socket

    @property
    def sockets(self) -> list[socket.socket]:
        return self.__accepted_sockets

    @property
    def name(self):
        return self.__name

    @property
    def lhost(self) -> str:
        return self.__lhost

    @property
    def lport(self) -> int:
        return self.__lport

    @property
    def ssl_enabled(self) -> bool:
        return self.__ssl_context is not None

    @property
    def certs_status(self) -> dict:
        if self.ssl_enabled:
            return self.__ssl_context.cert_store_stats()
        else:
            return {}

    @property
    def autorun(self):
        return self.__autorun

    @autorun.setter
    def autorun(self, value):
        self.__autorun = True if value else False

    @property
    def state(self) -> str:
        return self.__state.name

    def change_state(self, new_state: ListenerStateEnum):
        if new_state in self.__states:
            self.__state = self.__states[new_state]
            if new_state == ListenerStateEnum.Ready and self.__ifr and self.__autorun:
                Printer.info(f"Starting listener {self}")
                self.__ifr = False
                self.start()

    def save(self) -> dict:
        return {
            "name": self.name,
            "ip": self.lhost,
            "port": self.lport,
            "ssl": self.ssl_enabled,
            "autorun": self.autorun,
            "ca": self.__ca,
            "cert": self.__cert
        }

    @staticmethod
    def load(app, settings):
        l = Listener(app,
                     settings.get("name"),
                     settings.get("ip", "0.0.0.0"),
                     settings.get("port", 4444),
                     settings.get("ssl", False),
                     settings.get("autorun", False))
        if l.ssl_enabled:
            for ca in settings.get("ca", []):
                l.load_ca(ca)
            for cert, key in settings.get("cert", []):
                l.load_cert(cert, key)
        return l

    def handle_connection(self, session_socket: socket.socket, session_addr: tuple[str, int], *,
                          drop_duplicates=False, show_banner=False) -> Session | None:
        return self.__state.handle_connection(session_socket, session_addr, ssl_context=self.__ssl_context,
                                              drop_duplicates=drop_duplicates, show_banner=show_banner)

    def __str__(self):
        return f"{self.name} <{self.lhost}:{self.lport}>"


class ListenerInitException(Exception):
    pass


class ListenerStartException(Exception):
    pass
