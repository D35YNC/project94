import importlib
import os
import readline
import select
import signal
import socket
import ssl
import threading
import time

from .cli_commands import base_command
from .session import Session
from .utils import CommandsCompleter
from .utils import Printer
from .utils import get_banner
from .utils import recvall


__version__ = '1.1.beta'
__all__ = ["Project94", "entry", "__version__"]


class Project94:
    def __init__(self, args):
        self.EXIT_FLAG = False

        self.commands = {}
        for f in os.listdir(os.path.join(os.path.dirname(__file__), "cli_commands")):
            if f.endswith(".py"):
                mod = os.path.basename(f)[:-3]
                if mod != "__init__" and mod != "base_command":
                    try:
                        importlib.import_module(f"project94.cli_commands.{mod}")
                    except Exception as ex:
                        Printer.error(f"Error while importing {mod}: {ex}")
                    # TODO CHECK IS CORRECT WORKIN
        for cls in base_command.BaseCommand.__subclasses__():
            cmd = cls(self)
            if cmd.name in self.commands:
                Printer.error(f"Command {cmd.name} from \"{cmd.__module__}\" already exists.")
                Printer.error(f"Imported from \"{self.commands[cmd.name].__module__}\"")
            else:
                self.commands[cmd.name] = cmd

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        Printer.colored = not args.disable_colors
        self.blackout = args.blackout
        self.suppress_banner = not args.show_banner
        self.allow_duplicate_sessions = args.allow_duplicates

        self.master_host = args.lhost
        self.master_port = args.lport

        self.master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sessions: dict[str, Session] = {}
        self.active_session: Session = None

        self.inputs: list[socket.socket] = []
        self.outputs: list[socket.socket] = []

        if args.keyfile and args.certfile:
            # TODO CHECK REVSHELL w\o ca (cert+key)
            self.ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=args.keyfile.name)
            self.ssl.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            self.ssl.load_cert_chain(args.certfile.name)
            self.ssl.set_ciphers("ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES256-SHA384")
            Printer.success("SSL ENABLED")
        else:
            self.ssl = None
            Printer.warning("SSL DISABLED")

    def main(self):
        Printer.info(f"Listening: {self.master_host}:{self.master_port}")

        if self.allow_duplicate_sessions:
            Printer.warning("Session duplicating enabled")

        self.master_socket.bind((self.master_host, self.master_port))
        self.master_socket.listen(0x10)
        self.inputs.append(self.master_socket)

        th = threading.Thread(target=self.interface, daemon=True)
        th.start()

        while True:
            # I FUCKING HATE THIS TIMEOUT
            # TODO
            #  1. [ ] DO WHATEVER YOU WANT, BUT REMOVE hisith FUCKING TIMEOUT
            #  2. [X] ValueError when killin session and socket_fd == -1
            read_sockets, write_sockets, error_sockets = select.select(self.inputs, self.outputs, self.inputs, 0.5) # 0.25

            if self.EXIT_FLAG:
                break

            for socket_fd in read_sockets:
                if socket_fd is self.master_socket:
                    self.__accept_and_handle_connection()
                else:
                    session = self.find_session(fd=socket_fd)
                    data = recvall(socket_fd)
                    if not data:
                        # When session is None then sessino killed manually
                        # Else session DO SUICIDE
                        if session:
                            Printer.warning(f"Session {session.rhost}:{session.rport} dead")
                            self.restore_prompt()
                            self.close_connection(session, False)
                        continue
                        # break
                    try:
                        data = data.decode(session.encoding)
                    except (UnicodeDecodeError, UnicodeError):
                        Printer.error("Cant decode session output. Check&change encoding.")
                        self.restore_prompt()
                    else:
                        if not session.interactive:
                            Printer.success(f"{session.rhost}:{session.rport}")
                            print(data, end='')
                            print(f"{'-' * 0x2A}")
                            self.restore_prompt()
                        else:
                            print(data, end='')

            for socket_fd in write_sockets:
                session = self.find_session(fd=socket_fd)
                if not session:
                    if socket_fd in self.outputs:
                        self.outputs.remove(socket_fd)
                    continue
                if next_cmd := session.next_command():
                    try:
                        socket_fd.send(next_cmd.encode(session.encoding))
                    except (socket.error, OSError):
                        Printer.error(f"Cant send data to session {session.rhost}:{session.rport}")
                        self.restore_prompt()
                        self.close_connection(session)
                else:
                    self.outputs.remove(socket_fd)

            for socket_fd in error_sockets:
                # MMMMM?
                if socket_fd is self.master_socket:
                    Printer.error("MASTER ERROR")
                    self.shutdown()
                if session := self.find_session(fd=socket_fd):
                    self.close_connection(session)

        Printer.warning("Master exiting...")
        self.master_socket.shutdown(socket.SHUT_RDWR)
        self.master_socket.close()
        th.join()

    def interface(self):
        # TODO
        #  [-] 1/DISABLING AUTOCOMPLETION IN INTERACTIVE MODE
        #   Logic changed <it will not be fixed yet>
        #  [-] 2/FIX DELETION PROMPT WHEN DELETE SEMI-COMPLETED COMMAND
        #    Partiladadry fixed. Context not dislpaying on autocompletion
        #  [-] 3/FIX <ENTER> PRESSING WHEN EXIT WITH NON EMPTY INPUT
        #    ? <it will not be fixed yet>
        completer = CommandsCompleter(self.commands)
        readline.set_completer_delims("\t")
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')
        readline.set_completion_display_matches_hook(completer.display_matches)
        while True:
            if self.EXIT_FLAG:
                break

            try:
                command = input(self.context)
            except EOFError:
                self.shutdown()
                break

            command = command.strip()
            if not command:
                continue

            command = command.split(' ')
            if command[0] in self.commands:
                self.commands[command[0]](*command,
                                          print_success_callback=lambda x: Printer.success(x),
                                          print_info_callback=lambda x: Printer.info(x),
                                          print_warning_callback=lambda x: Printer.warning(x),
                                          print_error_callback=lambda x: Printer.error(x))
            elif self.active_session and self.active_session.interactive:
                if command[0] == "exit":
                    self.active_session.interactive = False
                else:
                    self.active_session.send_command(" ".join(command))
            else:
                Printer.error("Unknown command")

    def __accept_and_handle_connection(self):
        session_socket, session_addr = self.master_socket.accept()
        self.handle_connection(session_socket, session_addr)

    def handle_connection(self, session_socket, session_addr):
        if self.ssl:
            try:
                session_socket = self.ssl.wrap_socket(session_socket, True)
            except ssl.SSLCertVerificationError:
                Printer.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. Bad certificate")
                return
            except ssl.SSLError as ex:
                Printer.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. {ex}")
                return

        if not self.allow_duplicate_sessions:
            for id_ in self.sessions:
                if self.sessions[id_].rhost == session_addr[0]:
                    Printer.warning("Detect the same host connection, dropping...")
                    self.restore_prompt()
                    session_socket.shutdown(socket.SHUT_RDWR)
                    session_socket.close()
                    return

        if self.suppress_banner:
            session_socket.send("pwd\n".encode())
            time.sleep(1)
            recvall(session_socket)

        Printer.info(f"New session: {session_addr[0]}:{session_addr[1]}")
        self.restore_prompt()

        self.inputs.append(session_socket)
        session = Session(session_socket, not self.blackout)
        session.set_callbacks(self.read_callback, self.write_callback, self.error_callback)
        self.sessions[session.session_hash] = session

    def close_connection(self, session: Session, show_msg: bool = True):
        """
        Gracefully close connection
        :param session: `Session` to close
        :param show_msg: Show a message that the session is closed
        """
        if self.active_session == session:
            self.active_session = None
        if session.socket in self.inputs:
            self.inputs.remove(session.socket)
        if session.socket in self.outputs:
            self.outputs.remove(session.socket)
        if session == self.active_session:
            self.active_session = None
        try:
            session.socket.shutdown(socket.SHUT_RDWR)
            session.socket.close()
        except (socket.error, OSError):
            pass
        if session.session_hash in self.sessions:
            self.sessions.pop(session.session_hash)
        if show_msg:
            Printer.warning(f"Session {session.rhost}:{session.rport} killed")

    def find_session(self, *, fd: socket.socket = None, id_: str = None, idx: int = None) -> [Session, None]:
        """
        Looking for session in `self.sessions` by criteria:
        :param fd: search by socket
        :param id_: search by id (session.session_hash)
        :param idx: search by index in `self.sessions`
        :return: `Session` or `None`
        """
        if fd:
            for id_ in self.sessions:
                if self.sessions[id_].socket == fd:
                    return self.sessions[id_]
        if id_:
            for h in self.sessions:
                if h.startswith(id_):
                    return self.sessions[h]
        if idx:
            if not isinstance(idx, int):
                try:
                    idx = int(idx)
                except ValueError:
                    return None
            if 0 <= idx < len(self.sessions):
                return self.sessions.get(list(self.sessions.keys())[idx])
        return None

    def restore_prompt(self):
        """
        Prints prompt message
        """
        print(self.context, end='', flush=True)

    @property
    def context(self):
        """
        :return:Current session context [rhost:rport]
        """
        if self.active_session:
            if self.active_session.interactive:
                return "\r"
            else:
                return f"{Printer.context(f'{self.active_session.rhost}:{self.active_session.rport}')}>> "
        else:
            return f"{Printer.context('NO_SESSION')}>> "

    # TODO NOTE ABOUT THIS CALLBACKS

    def read_callback(self, session: Session):
        if session.socket in self.inputs:
            self.inputs.remove(session.socket)
        else:
            self.inputs.append(session.socket)

    def write_callback(self, session: Session):
        if session.socket not in self.outputs:
            self.outputs.append(session.socket)

    def error_callback(self, session: Session):
        self.close_connection(session)

    def shutdown(self, *args):
        """
        Gracefully exit
        """
        Printer.warning("Exit...")
        self.EXIT_FLAG = True
        while 0 < len(self.sessions):
            self.close_connection(self.sessions[list(self.sessions.keys())[0]])


def entry():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version",
                        action='version',
                        version=f"%(prog)s ver.{__version__}")
    parser.add_argument("-p", "--lport",
                        type=int,
                        metavar="PORT",
                        help="Port to listen",
                        default=443)
    parser.add_argument("-k", "--keyfile",
                        type=argparse.FileType(mode='r'),
                        help="keyfile for ssl")
    parser.add_argument("-H", "--lhost",
                        type=str,
                        metavar="HOST",
                        help="Host to listen",
                        default="0.0.0.0")
    parser.add_argument("-c", "--certfile",
                        type=argparse.FileType(mode='r'),
                        help="certfile for ssl")
    parser.add_argument("--disable-colors",
                        action="store_true",
                        help="disable colored output",
                        default=False)
    parser.add_argument("--blackout",
                        action="store_true",
                        help="dont try query info about sessions ip addresses",
                        default=False)
    parser.add_argument("--show-banner-pls",
                        dest="show_banner",
                        action="store_true",
                        help="dont suppress banners for new sessions",
                        default=False)
    # parser.add_argument("--silent",
    #                     action="store_true",
    #                     help="dont try automatic detect os",
    #                     default=False)
    parser.add_argument("--allow-duplicates",
                        action="store_true",
                        help="allow duplicating sessions from same ip",
                        default=False)
    a = parser.parse_args()

    print(f"\n{get_banner()}")

    app = Project94(a)
    app.main()


if __name__ == '__main__':
    entry()
