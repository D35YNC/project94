import importlib.util
import hashlib
import random
import socket
import string
import sys


class Log:
    colored = True

    @staticmethod
    def _black(line):
        return '\033[30m' + line + '\033[0m'

    @staticmethod
    def _blue(line):
        return '\033[94m' + line + '\033[0m'

    @staticmethod
    def _gray(line):
        return '\033[1;30m' + line + '\033[0m'

    @staticmethod
    def _green(line):
        return '\033[92m' + line + '\033[0m'

    @staticmethod
    def _cyan(line):
        return '\033[96m' + line + '\033[0m'

    @staticmethod
    def _light_purple(line):
        return '\033[94m' + line + '\033[0m'

    @staticmethod
    def _purple(line):
        return '\033[95m' + line + '\033[0m'

    @staticmethod
    def _red(line):
        return '\033[91m' + line + '\033[0m'

    @staticmethod
    def _underline(line):
        return '\033[4m' + line + '\033[0m'

    @staticmethod
    def _white(line):
        return '\033[0m' + line + '\033[0m'

    @staticmethod
    def _white_2(line):
        return '\033[1m' + line + '\033[0m'

    @staticmethod
    def _yellow(line):
        return '\033[93m' + line + '\033[0m'

    @staticmethod
    def _print(line):
        sys.stdout.write(line)
        sys.stdout.flush()

    @staticmethod
    def info(message: str):
        Log._print(f"\r[*] {Log._light_purple(message) if Log.colored else message}\n")

    @staticmethod
    def warning(message: str):
        Log._print(f"\r[!] {Log._yellow(message) if Log.colored else message}\n")

    @staticmethod
    def error(message: str):
        Log._print(f"\r[!!!] {Log._red(message) if Log.colored else message}\r\n")

    @staticmethod
    def success(message: str):
        Log._print(f"\r[+] {Log._green(message) if Log.colored else message}\n")

    @staticmethod
    def context(context: str):
        Log._print(f"\r[{Log._gray(context) if Log.colored else context}]")


request_can_import = True
if importlib.util.find_spec("requests"):
    import requests
else:
    request_can_import = False
    Log.error("Cant import module \"requests\" -> cant get extended info by ip")


def get_ip_info(host):
    global request_can_import
    if not request_can_import:
        return None
    try:
        r = requests.get("https://ifconfig.co/json", params={"ip": host}, timeout=10)
    except requests.exceptions.RequestException:
        return None
    else:
        if r.ok:
            return r.json()
    return None


def random_string(length: int = 10):
    return "".join(random.choice(string.hexdigits) for _ in range(length)).lower()


def create_session_hash(host, port) -> str:
    return hashlib.sha256(f"{host}:{port}".encode()).hexdigest()


def recvall(socket_fd: socket.socket) -> bytes:
    data = b""
    size = 0x100
    while True:
        try:
            r = socket_fd.recv(size)
        except (OSError, socket.error):
            return None
        else:
            if not r:
                break
            data += r
            if len(r) < size:
                break
    return data
