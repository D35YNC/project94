import socket

from project94.commands import Command
from project94.session import Session
from project94.utils.printer import Printer


class BindShellCmd(Command):
    def __init__(self, app):
        super().__init__(app, name="bind_shell", description="connects to bind shell")
        self.parser.add_argument("rhost", type=str, help="remote host for connect")
        self.parser.add_argument("rport", type=int, help="remote port for connect")

    def main(self, args):
        rhost = args.rhost
        rport = args.rport

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((rhost, rport))
        except socket.error:
            Printer.error(f"Cant connect to {rhost}:{rport}")
        else:
            self.app.register_session(Session(sock, (rhost, rport), None))
