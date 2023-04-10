import hashlib
import importlib.util
import random
import socket
import string


requests_import_success = True
if importlib.util.find_spec("requests"):
    import requests
else:
    from .printer import Printer
    requests_import_success = False
    Printer.error("Cant import module \"requests\" -> cant get extended info by ip")


def get_ip_info(host):
    global requests_import_success
    if not requests_import_success:
        return {}
    try:
        r = requests.get("https://ifconfig.co/json", params={"ip": host}, timeout=10)
    except requests.exceptions.RequestException:
        return {}
    else:
        if r.ok:
            return r.json()
    return {}


def random_token(length: int = 10):
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
            return bytes()
        else:
            if not r:
                break
            data += r
            if len(r) < size:
                break
    return data


