import importlib
import json
import os
import readline
import select
import signal
import socket
import threading

from .listener import Listener
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
        self.EXIT = threading.Event()

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        Printer.colored = not args.disable_colors
        self.sessions_drop_duplicates = args.drop_duplicates
        self.sessions_show_banner = args.show_banner
        self.config_path = args.config

        self.modules: list[Module] = []
        self.commands: dict[str, Command] = {}
        self.listeners: list[Listener] = []
        self.sessions: dict[str, Session] = {}
        self.__active_session: Session = None
        self.__read_sockets: list[socket.socket] = []
        self.__write_sockets: list[socket.socket] = []

        self.__load_modules()

        if os.path.isfile(self.config_path):
            self.config = json.load(open(self.config_path, mode='r', encoding="utf-8"))
        else:
            self.config = {"listeners": []}

        for settings in self.config["listeners"]:
            Printer.info(f"Loading listener \"{settings.get('name')}\"")
            listener = Listener.load(self, settings)
            self.listeners.append(listener)

    def main(self):
        for mod in self.modules:
            mod.on_master_ready()

        print("Startup options:")
        if self.sessions_drop_duplicates:
            Printer.warning("- Duplicates dropping enabled")
        else:
            Printer.info("- Duplicates dropping disabled")

        if self.sessions_show_banner:
            Printer.info("- Banners suppressing disabled")
        else:
            Printer.warning("- Banners suppressing enabled")

        th = threading.Thread(target=self.interface, daemon=True)
        th.start()
        while True:
            # TODO
            #  1. [ ] DO WHATEVER YOU WANT, BUT REMOVE hisith FUCKING TIMEOUT
            #  2. [X] ValueError when killin session and socket_fd == -1
            # I FUCKING HATE THIS TIMEOUT
            read_sockets, write_sockets, error_sockets = select.select(self.__read_sockets, self.__write_sockets, self.__read_sockets, 0.5) # 0.25

            if self.EXIT.is_set():
                break

            for socket_fd in read_sockets:
                if listener := self.get_listener(fd=socket_fd):
                    # TODO: REWRITE
                    if not listener.is_running and listener.listen_socket in self.__read_sockets:
                        self.__read_sockets.remove(listener.listen_socket)
                        continue
                    session_socket, session_addr = listener.listen_socket.accept()
                    session = listener.handle_connection(session_socket, session_addr,
                                                         drop_duplicates=self.sessions_drop_duplicates,
                                                         show_banner=self.sessions_show_banner)
                    self.__restore_prompt()
                    if session:
                        self.__read_sockets.append(session.socket)
                        session.set_callbacks(self.session_read_callback, self.session_write_callback, self.session_error_callback)
                        self.sessions[session.hash] = session

                        for mod in self.modules:
                            mod.on_session_ready(session)
                elif session := self.get_session(fd=socket_fd):
                    data = recvall(socket_fd)
                    if not data:
                        # When session is None then sessino killed manually
                        # Else session DO SUICIDE
                        Printer.warning(f"Session {session.rhost}:{session.rport} dead")
                        self.__restore_prompt()
                        self.close_connection(session, False)
                        continue
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
                # else:
                #     Printer.error(f"Read unknown socket {socket_fd}")
            for socket_fd in write_sockets:
                if session := self.get_session(fd=socket_fd):
                    if next_cmd := session.next_command():
                        try:
                            socket_fd.send(next_cmd.encode(session.encoding))
                        except (socket.error, OSError) as ex:
                            Printer.error(f"Cant send data to session {session.rhost}:{session.rport}. {ex}")
                            self.__restore_prompt()
                            self.close_connection(session)
                    else:
                        if socket_fd in self.__write_sockets:
                            self.__write_sockets.remove(socket_fd)
                # else:
                #     Printer.error(f"Write unknown socket {socket_fd}")
            for socket_fd in error_sockets:
                # MMMMM?
                if listener := self.get_listener(fd=socket_fd):
                    listener.stop()
                    Printer.error(f"Listener {listener.lhost}:{listener.lport} error")
                elif session := self.get_session(fd=socket_fd):
                    self.close_connection(session)

        th.join()

        self.config["listeners"] = []
        for listener in self.listeners:
            self.config["listeners"].append(listener.save())
            if listener.is_running:
                listener.stop()
            Printer.warning(f"Listener {listener} stopped")
        json.dump(self.config, open(self.config_path, mode='w', encoding="utf-8"))

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
        while not self.EXIT.is_set():
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
                self.commands[command[0]](*command, app=self)
            else:
                Printer.error("Unknown command")

    def close_connection(self, session: Session, show_msg: bool = True):
        """
        Gracefully close connection
        :param session: `Session` to close
        :param show_msg: Show a message that the session is closed
        """
        # Notifying modules about dead session
        for mod in self.modules:
            mod.on_session_dead(session)
        if self.active_session is session:
            self.active_session = None
        if (listener := session.listener) and session.socket in listener.sockets:
            listener.sockets.remove(session.socket)
        if session.hash in self.sessions:
            self.sessions.pop(session.hash)
        if session.socket in self.__read_sockets:
            self.__read_sockets.remove(session.socket)
        if session.socket in self.__write_sockets:
            self.__write_sockets.remove(session.socket)
        try:
            session.socket.shutdown(socket.SHUT_RDWR)
            session.socket.close()
        except (socket.error, OSError):
            pass
        if show_msg:
            Printer.warning(f"Session {session.rhost}:{session.rport} killed")

    def add_listener_sock(self, sock: socket.socket):
        if sock and sock not in self.__read_sockets:
            self.__read_sockets.append(sock)

    def get_listener(self, *, fd: socket.socket = None, name: str = None) -> Listener | None:
        """
        Looking for listener in `self.listeners` by criteria:
        :param fd: search by `listener.listen_socket`
        :param name: search by `listener.name`
        :return: `Listener` or `None`
        """
        if fd:
            for listener in self.listeners:
                if listener.listen_socket is fd:
                    return listener
        if name:
            for listener in self.listeners:
                if listener.name == name:
                    return listener
        return None

    def get_session(self, *, fd: socket.socket = None, id_: str = None, idx: int = None) -> Session | None:
        """
        Looking for session in `self.sessions` by criteria:
        :param fd: search by `session.socket`
        :param id_: search by id `session.hash`
        :param idx: search by index in `self.sessions`
        :return: `Session` or `None`
        """
        if fd:
            for h in self.sessions:
                if self.sessions[h].socket is fd:
                    return self.sessions[h]
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
    def active_session(self) -> Session:
        return self.__active_session

    @active_session.setter
    def active_session(self, value: Session):
        if isinstance(value, Session):
            self.__active_session = value
        else:
            self.__active_session = None

    @property
    def context(self):
        """
        :return: Current session context `[rhost:rport]`
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
        self.EXIT.set()
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
            try:
                mod = cls(self)
            except Exception as ex:
                Printer.error(f"Error while loading mudule {cls.__name__}: {ex}")
                continue
            else:
                if mod in self.modules:
                    Printer.error(f"Module {mod.name} from {mod.__module__} already imported from {self.modules.index(mod).__module__}")
                else:
                    self.modules.append(mod)

        for mod in self.modules:
            mod_load_succ = True
            mod_commands = mod.get_commands()
            for cmd in mod_commands:
                if mod_commands[cmd].is_subcommand:
                    continue
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
    parser.add_argument("-c", "--config",
                        type=str,
                        help="load specified config",
                        default="94.conf")
    parser.add_argument("--disable-config",
                        action="store_true",
                        help="disable config save-load",
                        default=False)
    parser.add_argument("--disable-colors",
                        action="store_true",
                        help="disable colored output",
                        default=False)
    parser.add_argument("--show-banner-pls",
                        dest="show_banner",
                        action="store_true",
                        help="dont suppress banners for new sessions",
                        default=False)
    parser.add_argument("--drop-duplicates",
                        action="store_true",
                        help="disable duplicating sessions from same ip",
                        default=False)
    a = parser.parse_args()

    print(f"\n{get_banner()}")

    app = Project94(a)
    app.main()


if __name__ == '__main__':
    entry()
