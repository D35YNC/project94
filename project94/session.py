import queue
import socket
import codecs
import time

from .utils import networking


class Session:
    # TODO
    #  1\OS DETECTION
    #  2\Software detection
    def __init__(self, socket_fd, query_info=True):
        self._socket_fd = socket_fd
        self._commands_queue = queue.Queue()
        self._rhost, self._rport = socket_fd.getpeername()
        self._session_hash = networking.create_session_hash(self.rhost, self.rport)
        self._encoding = "utf-8"
        self.interactive = False
        self._on_read = lambda _: None
        self._on_write = lambda _: None
        self._on_error = lambda _: None
        self._os = "lunex"
        if query_info and (api_info := networking.get_ip_info(self.rhost)):
            self._asn = api_info.get("asn", "Unknown")
            self._asn_org = api_info.get("asn_org", "Unknown")
            self._country = api_info.get("country", "Unknown")
            self._region = api_info.get("region_name", "Unknown")
            self._city = api_info.get("city", "Unknown")
            self._timezone = api_info.get("time_zone", "Unknown")
        else:
            self._asn = "Unknown"
            self._asn_org = "Unknown"
            self._country = "Unknown"
            self._region = "Unknown"
            self._city = "Unknown"
            self._timezone = "Unknown"

    def set_callbacks(self, read_callback=None, write_callback=None, error_callback=None):
        # TODO ADD REFERENCE TO NOTE IN project94.py
        if read_callback:
            self._on_read = read_callback
        if write_callback:
            self._on_write = write_callback
        if error_callback:
            self._on_error = error_callback

    def __str__(self) -> str:
        return f"Hash: {self._session_hash}; From: {self._rhost}:{self._rport}"

    # region PROPS

    @property
    def socket(self):
        return self._socket_fd

    @property
    def rhost(self):
        return self._rhost

    @property
    def rport(self):
        return self._rport

    @property
    def os(self):
        return self._os

    @property
    def session_hash(self):
        return self._session_hash

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        try:
            codecs.lookup(value)
        except LookupError:
            self._encoding = "utf-8"
        else:
            self._encoding = value

    @property
    def asn(self):
        return self._asn

    @property
    def asn_org(self):
        return self._asn_org

    @property
    def country(self):
        return self._country

    @property
    def region(self):
        return self._region

    @property
    def city(self):
        return self._city

    @property
    def timezone(self):
        return self._timezone

    # endregion

    def next_command(self):
        if not self._commands_queue.empty():
            return self._commands_queue.get_nowait()
        return None

    def send_command(self, command):
        if not self.interactive:
            print(f"> \"{command}\" -> {self.rhost}:{self.rport}")
        self._commands_queue.put_nowait(f"{command}\n")
        self._on_write(self)

    def rough_os_detection(self):
        cmd = 'cat /etc/*release | grep PRETTY_NAME | sed "s/PRETTY_NAME=//"\n\nsysteminfo\n'
        cmd = cmd.encode(self._encoding)
        self._on_read(self)
        time.sleep(0.25)
        try:
            self._socket_fd.send(cmd)
            time.sleep(0.25)
            result = networking.recvall(self._socket_fd)
            result = result.decode(self._encoding)
            print(result, end='')
        except (socket.error, OSError):
            self._on_error(self)
        else:
            pass
        finally:
            self._on_read(self)

    def detect_software_in_path(self, name: str) -> bool:
        token = networking.random_token()
        if "windows" in self.os.lower():
            cmd = f"powershell -Command \"if (Get-Command '{name}' -ErrorAction SilentlyContinue){{Write-Output '{token}'}}\"\n"
        else:
            cmd = f"/bin/bash -c \"if ( hash {name} 2>/dev/null ); then echo '{token}'; else echo ''; fi\"\n"
        self._on_read(self)
        time.sleep(0.25)
        try:
            self._socket_fd.send(cmd.encode(self._encoding))
            time.sleep(0.25)
            result = networking.recvall(self._socket_fd)
            result = result.decode(self._encoding)
            print(result, end='')
        except (socket.error, OSError):
            self._on_error(self)
            return False
        else:
            return token in result
        finally:
            self._on_read(self)

    def kill(self):
        self._on_error(self)
