import abc
import enum
import socket
import ssl


"""
LEEEEEGO
Yeahs its "state" pattern
Yeahs its overengineering
XDD
"""


__all__ = ["Listener", "ListenerInitError", "ListenerStartError", "ListenerStopError"]


class ListenerStateEnum(enum.Enum):
    Unknown = -1,
    Ready = 0,
    Running = 1,
    Stopped = 2,


class ListenerState(metaclass=abc.ABCMeta):
    def __init__(self, listener, enum_obj):
        self._listener = listener
        self.__enum_obj = enum_obj

    @abc.abstractmethod
    def start(self) -> socket.socket | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError()

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def enum_obj(self):
        return self.__enum_obj


class Running(ListenerState):
    def start(self):
        raise ListenerStartError(f"{self._listener} already running")

    def stop(self):
        for s in self._listener.sockets:
            if session := self._listener.app.get_session(fd=s):
                self._listener.app.close_session(session)
        self._listener.listen_socket.shutdown(socket.SHUT_RDWR)
        self._listener.listen_socket.close()
        self._listener.change_state(ListenerStateEnum.Ready)


class Stopped(ListenerState):
    def start(self):
        raise ListenerStartError(f"{self._listener} is not ready to start")

    def stop(self):
        raise ListenerStopError(f"{self._listener} is not running")


class Ready(ListenerState):
    def start(self) -> socket.socket | None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self._listener.lhost, self._listener.lport))
        except OSError as ex:
            raise ListenerStartError(str(ex))
        else:
            sock.listen(0x10)
            self._listener.change_state(ListenerStateEnum.Running)
            return sock

    def stop(self):
        raise ListenerStopError(f"{self._listener} is not running")


class Unknown(ListenerState):
    def start(self) -> socket.socket | None:
        raise ListenerStartError(f"{self._listener} need setup")

    def stop(self):
        ListenerStopError(f"{self._listener} need setup")


class Listener:
    def __init__(self, app, name: str, ip: str, port: int):
        if app is None:
            raise ListenerInitError("App is None")
        if name.strip() == "" or ' ' in name:
            raise ListenerInitError("Incorrect name")
        if not isinstance(port, int):
            raise ListenerInitError("Port is not int")
        elif not (0 < port < 0xFFFF):
            raise ListenerInitError("Port is not in range 0-65535")

        self.app = app
        self.__name = name
        self.__lhost = ip
        self.__lport = port

        self.__states = {ListenerStateEnum.Ready: Ready(self, ListenerStateEnum.Ready),
                         ListenerStateEnum.Running: Running(self, ListenerStateEnum.Running),
                         ListenerStateEnum.Stopped: Stopped(self, ListenerStateEnum.Stopped),
                         ListenerStateEnum.Unknown: Unknown(self, ListenerStateEnum.Unknown)}
        self.__state = self.__states[ListenerStateEnum.Unknown]
        self.__ssl_context: ssl.SSLContext = None

        self.__socket: socket.socket = None
        self.__accepted_sockets = []

        self.__ca = []
        self.__cert = []

        self.__autorun = False
        self.__drop_duplicates = True
        self.__suppress_banners = True

    def setup(self, autorun: bool, enable_ssl: bool, ca: list = None, cert: list[tuple] = None, drop_duplicates: bool = True, suppress_banners: bool = True):
        if enable_ssl:
            self.__ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__ssl_context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            self.__ssl_context.set_ciphers("ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES256-SHA384")
            self.__state = self.__states[ListenerStateEnum.Stopped]
            if ca:
                if isinstance(ca, list):
                    for cafile in ca:
                        if not self.load_ca(cafile):
                            raise ListenerInitError(f"Cant load ca cert {cafile}")
                else:
                    raise ListenerInitError("list of ca certs is not list")
            if cert:
                if isinstance(cert, list):
                    for certfile in cert:
                        if len(certfile) == 2:
                            if not self.load_cert(*certfile):
                                raise ListenerInitError(f"Cant load cert {certfile}")
                else:
                    raise ListenerInitError("list of certs is not list")
        else:
            self.__state = self.__states[ListenerStateEnum.Ready]

        self.__autorun = autorun
        self.__drop_duplicates = drop_duplicates
        self.__suppress_banners = suppress_banners

    def load_ca(self, cafile) -> bool | None:
        if self.ssl_enabled:
            try:
                self.__ssl_context.load_verify_locations(cafile=cafile)
            except (ssl.SSLError, OSError):
                return False
            else:
                self.__ca.append(cafile)

                if 0 < len(self.__ca) and 0 < len(self.__cert) and self.__state.enum_obj is not ListenerStateEnum.Running:
                    self.__state = self.__states[ListenerStateEnum.Ready]
                return True
        return None

    def load_cert(self, certfile, keyfile=None) -> bool | None:
        if self.ssl_enabled:
            try:
                self.__ssl_context.load_cert_chain(certfile, keyfile)
            except (ssl.SSLError, OSError):
                return False
            else:
                self.__cert.append((certfile, keyfile))

                if 0 < len(self.__ca) and 0 < len(self.__cert) and self.__state.enum_obj is not ListenerStateEnum.Running:
                    self.__state = self.__states[ListenerStateEnum.Ready]
                return True
        return None

    def start(self) -> socket.socket | None:
        sock = self.__state.start()
        self.__socket = sock
        return self.__socket

    def stop(self):
        self.__state.stop()

    def restart(self) -> socket.socket | None:
        self.stop()
        return self.start()

    def change_state(self, new_state: ListenerStateEnum):
        if new_state in self.__states:
            self.__state = self.__states[new_state]

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
    def ssl_context(self):
        return self.__ssl_context

    @property
    def certs_status(self) -> dict:
        if self.ssl_enabled:
            return self.__ssl_context.cert_store_stats()
        else:
            return {}

    @property
    def drop_duplicates(self):
        return self.__drop_duplicates

    @drop_duplicates.setter
    def drop_duplicates(self, value):
        self.__drop_duplicates = True if value else False

    @property
    def suppress_banners(self):
        return self.__suppress_banners

    @suppress_banners.setter
    def suppress_banners(self, value):
        self.__suppress_banners = True if value else False

    @property
    def autorun(self):
        return self.__autorun

    @autorun.setter
    def autorun(self, value):
        self.__autorun = True if value else False

    @property
    def state(self) -> str:
        return self.__state.name

    def save(self) -> dict:
        return {
            "name": self.name,
            "ip": self.lhost,
            "port": self.lport,
            "ssl": self.ssl_enabled,
            "ca": self.__ca,
            "cert": self.__cert,
            "autorun": self.autorun,
            "drop_duplicates": self.drop_duplicates,
            "suppress_banners": self.suppress_banners
        }

    @staticmethod
    def load(app, settings):
        listener = Listener(app, settings.get("name"), settings.get("ip", "0.0.0.0"), settings.get("port", 4444))
        listener.setup(settings.get("autorun"), settings.get("ssl"), settings.get("ca", []), settings.get("cert", []))
        return listener

    def __str__(self):
        return f"{self.name} <{self.lhost}:{self.lport}>"


class ListenerInitError(Exception):
    pass


class ListenerStartError(Exception):
    pass


class ListenerStopError(Exception):
    pass
