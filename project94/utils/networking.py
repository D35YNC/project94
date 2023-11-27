import hashlib
import random
import socket
import string


def random_token(length: int = 10):
    return "".join(random.choice(string.hexdigits) for _ in range(length)).lower()


def create_session_hash(host, port) -> str:
    return hashlib.sha256(f"{host}:{port}".encode()).hexdigest()


def recvall(sock: socket.socket) -> bytes:
    data = b""
    size = 1024
    while True:
        try:
            r = sock.recv(size)
        except (OSError, socket.error):
            return data
        else:
            if not r:
                break
            data += r
            if len(r) < size:
                break
    return data
