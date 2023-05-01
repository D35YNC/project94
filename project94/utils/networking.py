import hashlib
import random
import socket
import string


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
