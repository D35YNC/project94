import abc
import enum
import socket
import ssl

from project94.utils.logs import create_full_logger


class ListenerStateEnum(enum.Enum):
    Unknown = -1,
    Stopped = 0,
    Running = 1


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
        self._listener.listen_socket.shutdown(socket.SHUT_RDWR)
        self._listener.listen_socket.close()
        self._listener.change_state(ListenerStateEnum.Stopped)


class Stopped(ListenerState):
    def start(self):
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
        raise ListenerStopError(f"{self._listener} is not running")


class Listener:
    def __init__(self, name: str, lhost: str, lport: int, autorun: bool = False, drop_duplicates: bool = True, enable_ssl: bool = False):
        if name.strip() == "" or ' ' in name:
            raise ValueError(f"Listener name '{name}' is incorrect")
        if not isinstance(lport, int):
            raise ValueError("Port is not int")
        elif not (0 < lport < 0xFFFF):
            raise ValueError("Port is not in range 0-65535")

        self.__name = name
        self.__lhost = lhost
        self.__lport = lport
        self.__socket: socket.socket = None
        self.__accepted_sockets = []
        self.__ssl_context: ssl.SSLContext = None
        self.__ca = []
        self.__cert = []
        self.__autorun = autorun
        self.__drop_duplicates = drop_duplicates
        self.__logger = create_full_logger(self.__name)
        self.__states = {ListenerStateEnum.Running: Running(self, ListenerStateEnum.Running),
                         ListenerStateEnum.Stopped: Stopped(self, ListenerStateEnum.Stopped),
                         ListenerStateEnum.Unknown: Unknown(self, ListenerStateEnum.Unknown)}
        if enable_ssl:
            self.__state = self.__states[ListenerStateEnum.Unknown]
            self.__ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__ssl_context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            self.__ssl_context.set_ciphers("ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES256-SHA384")
            self.__logger.info(f"SSL context created")
        else:
            self.__state = self.__states[ListenerStateEnum.Stopped]

        self.__logger.info(f"Seems initialized: {self} {self.state}")

    def load_ca(self, cafile) -> bool | None:
        if self.ssl_enabled:
            try:
                self.__ssl_context.load_verify_locations(cafile=cafile)
            except (ssl.SSLError, OSError):
                return False
            else:
                self.__ca.append(cafile)

                if 0 < len(self.__ca) and 0 < len(self.__cert) and self.__state.enum_obj is not ListenerStateEnum.Running:
                    self.__state = self.__states[ListenerStateEnum.Stopped]
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
                    self.__state = self.__states[ListenerStateEnum.Stopped]
                return True
        return None

    def start(self):
        self.__socket = self.__state.start()

    def stop(self):
        self.__state.stop()

    def restart(self) -> socket.socket | None:
        self.stop()
        return self.start()

    def change_state(self, new_state: ListenerStateEnum):
        if new_state in self.__states:
            self.__state = self.__states[new_state]

    @property
    def log(self) -> list[str]:
        return self.__logger.handlers[0].stream.getvalue().strip().split('\n')

    @property
    def logger(self):
        return self.__logger

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
    def state(self) -> str:
        return self.__state.name

    @property
    def ssl_enabled(self) -> bool:
        return self.__ssl_context is not None

    @property
    def ssl_context(self):
        return self.__ssl_context

    @property
    def drop_duplicates(self):
        return self.__drop_duplicates

    @drop_duplicates.setter
    def drop_duplicates(self, value):
        self.__drop_duplicates = bool(value)

    @property
    def autorun(self):
        return self.__autorun

    @autorun.setter
    def autorun(self, value):
        self.__autorun = bool(value)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "lhost": self.lhost,
            "lport": self.lport,
            "ssl": self.ssl_enabled,
            "ca": self.__ca,
            "cert": self.__cert,
            "autorun": self.autorun,
            "drop_duplicates": self.drop_duplicates,
        }

    @staticmethod
    def from_dict(config: dict):
        listener = Listener(name=config.get("name", ""),
                            lhost=config.get("lhost", "0.0.0.0"),
                            lport=config.get("lport", 1337),
                            autorun=config.get("autorun", False),
                            drop_duplicates=config.get("drop_duplicates", True),
                            enable_ssl=config.get("ssl", False))
        if config.get("ssl"):
            for ca in config.get("ca", []):
                listener.load_ca(ca)
            for cert in config.get("cert", []):
                listener.load_cert(cert[0], cert[1])
        return listener

    def __str__(self):
        return f"{self.name} <{self.lhost}:{self.lport}>"


class ListenerStartError(Exception):
    pass


class ListenerStopError(Exception):
    pass
