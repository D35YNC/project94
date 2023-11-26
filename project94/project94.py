import json
import os
import readline
import select
import signal
import socket
import ssl
import threading
import importlib

from project94.listener import Listener, ListenerStartError, ListenerStopError
from project94.session import Session

from project94.commands import Command

from project94.utils.completer import CommandsCompleter
from project94.utils.networking import recvall
from project94.utils.printer import Printer


__version__ = '1.2.dev'


class Project94:
    def __init__(self, args):
        self.EXIT = threading.Event()

        signal.signal(signal.SIGINT, self.no_shutdown)
        signal.signal(signal.SIGTERM, self.no_shutdown)

        self.commands: dict[str, Command] = {}
        self.__load_commands()

        self.listeners: list[Listener] = []
        self.sessions: dict[str, Session] = {}
        self.__active_session: Session = None
        self.__epoll = select.epoll()

        Printer.colored = not args.disable_colors

        if args.disable_config:
            self.__config_path = None
            self.config = {}
            if args.listeners:
                self.config["listeners"] = json.loads(args.listeners)
        else:
            self.__config_path = args.config
            if os.path.isfile(self.__config_path):
                self.config = json.load(open(self.__config_path, mode='r', encoding="utf-8"))
            else:
                self.config = {"listeners": []}
        if 0 < len(self.config["listeners"]):
            Printer.info("Loading listeners...")
            for settings in self.config["listeners"]:
                try:
                    listener = Listener.from_dict(settings)
                except Exception as ex:
                    Printer.error(str(ex))
                else:
                    self.listeners.append(listener)
                    Printer.success(f"{listener} loaded")

    def main(self):
        arn = [listener for listener in self.listeners if listener.autorun]
        if 0 < len(arn):
            Printer.info("Autorun listeners...")
            for listener in arn:
                if listener.autorun:
                    try:
                        listener.start()
                    except ListenerStartError as ex:
                        Printer.error(str(ex))
                    else:
                        self.register_listener(listener)
                        Printer.success(f"{listener} started")

        th = threading.Thread(target=self.interface, daemon=True)
        th.start()

        while True:
            events = self.__epoll.poll(1)

            if self.EXIT.is_set():
                break

            for fd, event in events:
                if event & select.EPOLLIN:
                    if listener := self.get_listener(fd=fd):
                        session_socket, session_addr = listener.listen_socket.accept()
                        if listener.ssl_enabled:
                            try:
                                session_socket = listener.ssl_context.wrap_socket(session_socket, True)
                            except ssl.SSLError as ex:
                                Printer.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. {ex}")
                                self.__restore_prompt()
                                continue
                        session = Session(session_socket, session_addr, listener)
                        self.register_session(session)
                        self.__restore_prompt()
                    elif session := self.get_session(fd=fd):
                        data = recvall(session.socket)
                        if not data:
                            # When session is None then sessino killed manually
                            # Else session DO SUICIDE
                            self.close_session(session)
                            self.__restore_prompt()
                            continue
                        try:
                            data = data.decode(session.encoding)
                        except (UnicodeDecodeError, UnicodeError):
                            Printer.error("Cant decode session output. Check&change encoding.")
                            self.__restore_prompt()
                        else:
                            if session.shell_mode:
                                print(data, end='')
                            else:
                                session.recv_data.put_nowait(data)

                elif (event & select.EPOLLHUP) or (event & select.EPOLLRDHUP) or (event & select.EPOLLERR):
                    if listener := self.get_listener(fd=fd):
                        try:
                            listener.stop()
                        except ListenerStopError:
                            pass
                        self.unregister_listener(listener)
                        Printer.error(f"{str(listener)} error")
                    elif session := self.get_session(fd=fd):
                        self.close_session(session)

        th.join()

        if self.__config_path:
            self.config["listeners"] = []
            for listener in self.listeners:
                self.config["listeners"].append(listener.to_dict())

            json.dump(self.config, open(self.__config_path, mode='w', encoding="utf-8"))

    def interface(self):
        completer = CommandsCompleter(self.commands)
        readline.set_completer_delims("\t")
        readline.set_completer(completer.complete)
        readline.set_completion_display_matches_hook(completer.display_matches)
        readline.parse_and_bind("tab: complete")

        while not self.EXIT.is_set():
            try:
                command = input(self.context)
            except EOFError:
                self.shutdown()
                break

            command = command.strip().split(' ')
            if self.active_session and self.active_session.shell_mode:
                if command[0] == "exit":
                    self.active_session.shell_mode = False
                else:
                    try:
                        self.active_session.socket.send((" ".join(command) + "\n").encode(self.active_session.encoding))
                    except (socket.error, OSError):
                        self.close_session(self.active_session)
                        self.__restore_prompt()
            elif command[0] and command[0] in self.commands:
                cmd = command[0]
                args = command[1:]
                try:
                    self.commands[cmd](*args)
                except Exception as error:
                    Printer.error(f"{cmd}; ERR:{error}; ARGS:{args}")
                    # self.modules[cmd].module.on_command_error(error, cmd, args)
            elif command[0].strip() == '':
                pass
            else:
                Printer.error(f"Unknown command")

    def register_session(self, session: Session):
        session_addr = session.socket.getpeername()

        if listener := session.listener:
            if listener.drop_duplicates:
                for s in listener.sockets:
                    if s.getpeername()[0] == session_addr[0]:
                        Printer.warning(f"Listener {str(listener)} received duplicate connection from {session_addr[0]}, dropping...")
                        session.socket.shutdown(socket.SHUT_RDWR)
                        session.socket.close()
                        return

        listener.sockets.append(session.socket)
        self.__epoll.register(session.socket.fileno(), select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR | select.EPOLLET)
        self.sessions[session.hash] = session

        Printer.info(f"New session: {session}")

    def close_session(self, session: Session, *, its_manual_kill: bool = False):
        """
        Gracefully close connection
        :param session: `Session` to close
        :param its_manual_kill: Write a message that the session was interrupted manually or died by them
        """
        self.__epoll.unregister(session.socket.fileno())
        if self.active_session is session:
            self.active_session = None
        if (listener := session.listener) and session.socket in listener.sockets:
            listener.sockets.remove(session.socket)
        if session.hash in self.sessions:
            self.sessions.pop(session.hash)
        try:
            session.socket.shutdown(socket.SHUT_RDWR)
            session.socket.close()
        except (socket.error, OSError):
            pass

        if its_manual_kill:
            Printer.warning(f"{str(session)} killed")
        else:
            Printer.warning(f"{str(session)} dead")

    def register_listener(self, listener: Listener):
        # TODO: Error handling?
        if listener.listen_socket:
            self.__epoll.register(listener.listen_socket.fileno(), select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR | select.EPOLLET)

    def unregister_listener(self, listener: Listener):
        if listener.listen_socket:
            self.__epoll.unregister(listener.listen_socket.fileno())

    def get_listener(self, *, fd: int = None, socket_: socket.socket = None, name: str = None) -> Listener | None:
        """
        Looking for listener in `self.listeners` by criteria:
        :param fd: search by `listener.listen_socket.fileno`
        :param socket_: search by `listener.listen_socket`
        :param name: search by `listener.name`
        :return: `Listener` or `None`
        """
        if fd:
            for listener in self.listeners:
                if listener.listen_socket.fileno() == fd:
                    return listener
        if socket_:
            for listener in self.listeners:
                if listener.listen_socket is socket_:
                    return listener
        if name:
            for listener in self.listeners:
                if listener.name == name:
                    return listener
        return None

    def get_session(self, *, fd: int = None, socket_: socket.socket = None, id_: str = None) -> Session | None:
        """
        Looking for session in `self.sessions` by criteria:
        :param fd: search by `session.socket.fileno`.
        :param socket_: search by `session.socket`
        :param id_: search by id `session.hash`
        :return: `Session` or `None`
        """
        if fd:
            for h in self.sessions:
                if self.sessions[h].socket.fileno() == fd:
                    return self.sessions[h]
        if socket_:
            for h in self.sessions:
                if self.sessions[h].socket is socket_:
                    return self.sessions[h]
        if id_:
            for h in self.sessions:
                if h.startswith(id_):
                    return self.sessions[h]
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
            if self.active_session.shell_mode:
                return "\n"
            else:
                return f"{Printer.context(f'{self.active_session.rhost}:{self.active_session.rport}')}>> "
        else:
            return f"{Printer.context('PROJECT94')}>> "

    def no_shutdown(self, *args):
        Printer.warning(f"Maaan use exit command to exit pls")
        self.__restore_prompt()

    def shutdown(self, *args):
        """Gracefully exit"""
        Printer.warning("Exit...")
        self.EXIT.set()
        while 0 < len(self.sessions):
            self.close_session(self.sessions[list(self.sessions.keys())[0]], its_manual_kill=True)
        for listener in self.listeners:
            if listener.is_running:
                self.unregister_listener(listener)
                try:
                    listener.stop()
                except ListenerStopError:
                    pass
                Printer.warning(f"{str(listener)} stopped")

    def __load_commands(self):
        for f in os.listdir(os.path.join(os.path.dirname(__file__), "commands")):
            if f.endswith(".py"):
                mod = os.path.basename(f)[:-3]
                if mod != "__init__":
                    try:
                        importlib.import_module(f"project94.commands.{mod}")
                    except Exception as ex:
                        Printer.error(f"Error while importing {mod}: {ex}")

        for cls in Command.__subclasses__():
            try:
                cmd = cls(self)
            except Exception as ex:
                Printer.error(f"Cant load {cls.__name__}. {ex}")
                continue

            if cmd.name in self.commands:
                Printer.error(f"Module {cmd.name} from {cmd.__module__} already imported from "
                              f"{self.commands[cmd.name].__module__}")
                continue

            self.commands[cmd.name] = cmd

    def __restore_prompt(self):
        print(self.context, end='', flush=True)
        print(readline.get_line_buffer(), end='', flush=True)


def entry():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version",
                        action='version',
                        version=f"%(prog)s v{__version__}")
    parser.add_argument("-c", "--config",
                        type=str,
                        help="load specified config",
                        default="94.conf")
    parser.add_argument("-l", "--listeners",
                        type=str,
                        help="load listeners from string",
                        default=None)
    parser.add_argument("--disable-config",
                        action="store_true",
                        help="disable config save-load",
                        default=False)
    parser.add_argument("--disable-colors",
                        action="store_true",
                        help="disable colored output",
                        default=False)

    a = parser.parse_args()

    if a.listeners:
        a.disable_config = True

    print(f"\n{get_banner()}")

    app = Project94(a)
    app.main()


if __name__ == '__main__':
    entry()
