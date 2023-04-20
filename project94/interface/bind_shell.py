import socket

from .base_command import BaseCommand


class BindShell(BaseCommand):
    @property
    def description(self) -> str:
        return "connects to bind shell"

    @property
    def usage(self) -> str:
        return f"Usage: {self.name} IP PORT"

    def __call__(self, *args, **kwargs):
        ip = args[1]
        try:
            port = int(args[2])
        except ValueError:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(f"Cant convert {args[1]} to int")
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except socket.error:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(f"Cant connect to {ip}:{port}")
        else:
            self._app.handle_connection(sock, sock.getpeername())
