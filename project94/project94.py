import importlib
import os
import readline
import select
import signal
import socket
import ssl
import threading
import time

from .modules.module_base import Module, Command
from .session import Session
from .utils import CommandsCompleter
from .utils import Printer
from .utils import get_banner
from .utils import recvall


__version__ = '1.1'
__all__ = ["Project94", "entry", "__version__"]


class Project94:
    def __init__(self, args):
        self.EXIT_FLAG = False

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        Printer.colored = not args.disable_colors
        self.allow_duplicate_sessions = args.allow_duplicates
        self.blackout = args.blackout
        self.suppress_banner = not args.show_banner
        self.master_host = args.lhost
        self.master_port = args.lport

        self.active_session: Session = None
        self.sessions: dict[str, Session] = {}
        self.modules: list[Module] = []
        self.commands: dict[str, Command] = {}

        self.__load_modules()

        self.__master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__read_sockets: list[socket.socket] = []
        self.__write_sockets: list[socket.socket] = []

        if args.keyfile and args.certfile:
            # TODO CHECK REVSHELL w\o ca (cert+key)
            self.__ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=args.keyfile.name)
            self.__ssl_context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            self.__ssl_context.load_cert_chain(args.certfile.name)
            self.__ssl_context.set_ciphers("ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES256-SHA384")
            Printer.success("SSL ENABLED")
        else:
            self.__ssl_context = None
            Printer.warning("SSL DISABLED")

    def main(self):
        for mod in self.modules:
            mod.on_master_ready()

        Printer.info(f"Listening: {self.master_host}:{self.master_port}")

        if self.allow_duplicate_sessions:
            Printer.warning("Session duplicating enabled")

        self.__master_socket.bind((self.master_host, self.master_port))
        self.__master_socket.listen(0x10)
        self.__read_sockets.append(self.__master_socket)

        th = threading.Thread(target=self.interface, daemon=True)
        th.start()

        while True:
            # I FUCKING HATE THIS TIMEOUT
            # TODO
            #  1. [ ] DO WHATEVER YOU WANT, BUT REMOVE hisith FUCKING TIMEOUT
            #  2. [X] ValueError when killin session and socket_fd == -1
            read_sockets, write_sockets, error_sockets = select.select(self.__read_sockets, self.__write_sockets, self.__read_sockets, 0.5) # 0.25

            if self.EXIT_FLAG:
                break

            for socket_fd in read_sockets:
                if socket_fd is self.__master_socket:
                    session_socket, session_addr = self.__master_socket.accept()
                    self.handle_connection(session_socket, session_addr)
                else:
                    session = self.get_session(fd=socket_fd)
                    data = recvall(socket_fd)
                    if not data:
                        # When session is None then sessino killed manually
                        # Else session DO SUICIDE
                        if session:
                            Printer.warning(f"Session {session.rhost}:{session.rport} dead")
                            self.__restore_prompt()
                            self.close_connection(session, False)
                        continue
                        # break
                    try:
                        data = data.decode(session.encoding)
                    except (UnicodeDecodeError, UnicodeError):
                        Printer.error("Cant decode session output. Check&change encoding.")
                        self.__restore_prompt()
                    else:
                        if not session.interactive:
                            Printer.success(f"{session.rhost}:{session.rport}")
                            print(data, end='')
                            print('-' * 0x2A)
                            self.__restore_prompt()
                        else:
                            print(data, end='')

            for socket_fd in write_sockets:
                session = self.get_session(fd=socket_fd)
                if not session:
                    if socket_fd in self.__write_sockets:
                        self.__write_sockets.remove(socket_fd)
                    continue
                if next_cmd := session.next_command():
                    try:
                        socket_fd.send(next_cmd.encode(session.encoding))
                    except (socket.error, OSError):
                        Printer.error(f"Cant send data to session {session.rhost}:{session.rport}")
                        self.__restore_prompt()
                        self.close_connection(session)
                else:
                    self.__write_sockets.remove(socket_fd)

            for socket_fd in error_sockets:
                # MMMMM?
                if socket_fd is self.__master_socket:
                    Printer.error("MASTER ERROR")
                    self.shutdown()
                    break
                if session := self.get_session(fd=socket_fd):
                    self.close_connection(session)

        Printer.warning("Master exiting...")
        self.__master_socket.shutdown(socket.SHUT_RDWR)
        self.__master_socket.close()
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
            if self.active_session and self.active_session.interactive:
                if command[0] == "exit":
                    self.active_session.interactive = False
                else:
                    self.active_session.send_command(" ".join(command))
            elif command[0] in self.commands:
                self.commands[command[0]](*command,
                                          app=self,
                                          print_success_callback=lambda x: Printer.success(x),
                                          print_info_callback=lambda x: Printer.info(x),
                                          print_warning_callback=lambda x: Printer.warning(x),
                                          print_error_callback=lambda x: Printer.error(x))
            else:
                Printer.error("Unknown command")

    def handle_connection(self, session_socket: socket.socket, session_addr: tuple[str, int]):
        if self.__ssl_context:
            try:
                session_socket = self.__ssl_context.wrap_socket(session_socket, True)
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
                    self.__restore_prompt()
                    session_socket.shutdown(socket.SHUT_RDWR)
                    session_socket.close()
                    return

        if self.suppress_banner:
            session_socket.send("pwd\n".encode())
            time.sleep(1)
            recvall(session_socket)

        Printer.info(f"New session: {session_addr[0]}:{session_addr[1]}")
        self.__restore_prompt()

        self.__read_sockets.append(session_socket)
        session = Session(session_socket)
        session.set_callbacks(self.session_read_callback, self.session_write_callback, self.session_error_callback)
        self.sessions[session.session_hash] = session

        for mod in self.modules:
            mod.on_session_ready(session, blackout=self.blackout)

    def close_connection(self, session: Session, show_msg: bool = True):
        """
        Gracefully close connection
        :param session: `Session` to close
        :param show_msg: Show a message that the session is closed
        """
        for mod in self.modules:
            mod.on_session_dead(session)
        if show_msg:
            Printer.warning(f"Session {session.rhost}:{session.rport} killed")
        if self.active_session == session:
            self.active_session = None
        if session.socket in self.__read_sockets:
            self.__read_sockets.remove(session.socket)
        if session.socket in self.__write_sockets:
            self.__write_sockets.remove(session.socket)
        try:
            session.socket.shutdown(socket.SHUT_RDWR)
            session.socket.close()
        except (socket.error, OSError):
            pass
        if session.session_hash in self.sessions:
            self.sessions.pop(session.session_hash)

    def get_session(self, *, fd: socket.socket = None, id_: str = None, idx: int = None) -> [Session, None]:
        """
        Looking for session in `self.sessions` by criteria:
        :param fd: search by `session.socket`
        :param id_: search by id `session.session_hash`
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

    def session_read_callback(self, session: Session):
        if session.socket in self.__read_sockets:
            self.__read_sockets.remove(session.socket)
        else:
            self.__read_sockets.append(session.socket)

    def session_write_callback(self, session: Session):
        if session.socket not in self.__write_sockets:
            self.__write_sockets.append(session.socket)

    def session_error_callback(self, session: Session):
        self.close_connection(session)

    def shutdown(self, *args):
        """Gracefully exit"""
        Printer.warning("Exit...")
        self.EXIT_FLAG = True
        for mod in self.modules:
            mod.on_master_dead()
        while 0 < len(self.sessions):
            self.close_connection(self.sessions[list(self.sessions.keys())[0]])

    def __load_modules(self):
        for f in os.listdir(os.path.join(os.path.dirname(__file__), "modules")):
            if f.endswith(".py"):
                mod = os.path.basename(f)[:-3]
                if mod not in ["module_base", "__init__"]:
                    try:
                        importlib.import_module(f"project94.modules.{mod}")
                    except Exception as ex:
                        Printer.error(f"Error while importing {mod}: {ex}")
                    # TODO CHECK IS CORRECT WORKIN
        for cls in Module.__subclasses__():
            mod = cls(self)
            if mod in self.modules:
                Printer.error(f"Module {mod.name} from {mod.__module__} already imported from {self.modules.index(mod).__module__}")
            else:
                self.modules.append(mod)

        for mod in self.modules:
            mod_load_succ = True
            mod_commands = mod.get_commands()
            for cmd in mod_commands:
                if cmd in self.commands:
                    Printer.error(f"Command {cmd} from \"{mod.name}\" ({mod_commands[cmd].module.__module__}) already imported from \"{self.commands[cmd].module.name}\" ({self.commands[cmd].module.__module__})")
                    mod_load_succ = False
                else:
                    self.commands[cmd] = mod_commands[cmd]
            if mod_load_succ:
                Printer.success(f"{mod.name} loaded")

    def __restore_prompt(self):
        print(self.context, end='', flush=True)


def entry():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version",
                        action='version',
                        version=f"%(prog)s ver{__version__}")
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
