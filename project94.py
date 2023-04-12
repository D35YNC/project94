import codecs
import queue
import select
import signal
import socket
import ssl
import threading
import time
import utils

__version__ = "1.0.[DEV]"
__author__ = "d35ync"
__github__ = "https://github.com/D35YNC/project94"


class Session:
    def __init__(self, socket_fd, query_info=True):
        self._socket_fd = socket_fd
        self._commands_queue = queue.Queue()
        self._rhost, self._rport = socket_fd.getpeername()
        self._session_hash = utils.create_session_hash(self.rhost, self.rport)
        self._encoding = "utf-8"
        self._interactive = False
        self._on_read = lambda _: None
        self._on_write = lambda _: None
        self._on_error = lambda _: None
        self._os = "lunex"
        if query_info and (api_info := utils.get_ip_info(self.rhost)):
            self._asn = api_info.get("asn", "Unknown")
            self._asn_org = api_info.get("asn_org", "Unknown")
            self._country = api_info.get("country", "Unknown")
            self._region = api_info.get("region_name", "Unknown")
            self._city = api_info.get("city", "Unknown")
            self._timezone = api_info.get("time_zone", "Unknown")
        else:
            self._asn = "Unknown"
            self._asn_org = "Unknown"
            self._country = "Unknown"
            self._region = "Unknown"
            self._city = "Unknown"
            self._timezone = "Unknown"

    def set_callbacks(self, read_callback=None, write_callback=None, error_callback=None):
        if read_callback:
            self._on_read = read_callback
        if write_callback:
            self._on_write = write_callback
        if error_callback:
            self._on_error = error_callback

    def __str__(self) -> str:
        return f"Hash: {self._session_hash}; From: {self._rhost}:{self._rport}"

    # region SESSION_PROPS

    @property
    def socket(self):
        return self._socket_fd

    @property
    def rhost(self):
        return self._rhost

    @property
    def rport(self):
        return self._rport

    @property
    def os(self):
        return self._os

    @property
    def session_hash(self):
        return self._session_hash

    @property
    def encoding(self):
        return self._encoding

    @property
    def is_interactive(self):
        return self._interactive

    @encoding.setter
    def encoding(self, value):
        try:
            codecs.lookup(value)
        except LookupError:
            self._encoding = "utf-8"
        else:
            self._encoding = value

    @property
    def asn(self):
        return self._asn

    @property
    def asn_org(self):
        return self._asn_org

    @property
    def country(self):
        return self._country

    @property
    def region(self):
        return self._region

    @property
    def city(self):
        return self._city

    @property
    def timezone(self):
        return self._timezone

    # endregion

    def next_command(self):
        if not self._commands_queue.empty():
            return self._commands_queue.get_nowait()
        return None

    def send_command(self, command):
        print(f"> \"{command}\" -> {self.rhost}:{self.rport}")
        self._commands_queue.put_nowait(f"{command}\n")
        self._on_write(self)

    def interact(self):
        self._interactive = True
        while True:
            command = input()
            if not command:
                continue
            elif command == "exit":
                self._interactive = False
                self._commands_queue.put_nowait("\n")
                break
            self._commands_queue.put_nowait(f"{command}\n")
            self._on_write(self)
            time.sleep(0.25)

    def rough_os_detection(self):
        cmd = 'cat /etc/*release | grep PRETTY_NAME | sed "s/PRETTY_NAME=//"\n\nsysteminfo\n'
        cmd = cmd.encode(self._encoding)
        self._on_read(self)
        time.sleep(0.25)
        try:
            self._socket_fd.send(cmd)
            time.sleep(0.25)
            result = utils.recvall(self._socket_fd)
            result = result.decode(self._encoding)
            print(result, end='')#CHECK
        except (socket.error, OSError):
            self._on_error(self)
            return False
        else:
            return True
        finally:
            self._on_read(self)

    def detect_software_in_path(self, name: str) -> bool:
        token = utils.random_string()
        if "windows" in self.os.lower():
            cmd = f"powershell -Command \"if (Get-Command '{name}' -ErrorAction SilentlyContinue){{Write-Output '{token}'}}\"\n"
        else:
            cmd = f"/bin/bash -c \"if ( hash {name} 2>/dev/null ); then echo '{token}'; else echo ''; fi\"\n"
        self._on_read(self)
        time.sleep(0.25)
        try:
            self._socket_fd.send(cmd.encode(self._encoding))
            time.sleep(0.25)
            result = utils.recvall(self._socket_fd)
            result = result.decode(self._encoding)
            print(result, end='')
        except (socket.error, OSError):
            self._on_error(self)
            return False
        else:
            return token in result
        finally:
            self._on_read(self)

    def kill(self):
        self._on_error(self)
        # try:
        #     self._socket_fd.shutdown(socket.SHUT_RDWR)
        #     self._socket_fd.close()
        # except OSError:
        #     pass
        #     # mmmm?


class Project94:
    def __init__(self, args):
        self.EXIT_FLAG = False

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        utils.Log.colored = not args.disable_colors
        self.blackout = args.blackout
        self.suppress_banner = not args.show_banner
        # self.silent = args.silent
        self.allow_duplicate_sessions = args.allow_duplicates

        self.master_host = args.lhost
        self.master_port = args.lport

        self.master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sessions = {}
        self.active_session: Session = None

        self.inputs = []
        self.outputs = []

        if args.keyfile and args.certfile:
            self.ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=args.keyfile.name)
            self.ssl.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            self.ssl.load_cert_chain(args.certfile.name)
            self.ssl.set_ciphers("ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES256-SHA384")
            utils.Log.success("SSL ENABLED")
        else:
            self.ssl = None
            utils.Log.warning("SSL DISABLED")

    def main(self):
        utils.Log.info(f"Listening: {self.master_host}:{self.master_port}")

        if self.allow_duplicate_sessions:
            utils.Log.warning("Session duplicating enabled")

        # if not self.blackout:
        #     utils.Log.warning("")

        self.master_socket.bind((self.master_host, self.master_port))
        self.master_socket.listen(0x10)
        self.inputs.append(self.master_socket)

        th = threading.Thread(target=self.interface, daemon=True)
        th.start()

        while True:
            if self.EXIT_FLAG:
                break
            # I FUCKING HATE THIS TIMEOUT
            # TODO
            #  1. [ ] DO WHATEVER YOU WANT, BUT REMOVE hisith FUCKING TIMEOUT
            #  2. [X] ValueError when killin session and socket_fd == -1
            read_sockets, write_sockets, error_sockets = select.select(self.inputs, self.outputs, self.inputs, 0.5) # 0.25
            for socket_fd in read_sockets:
                if socket_fd is self.master_socket:
                    self.handle_connection()
                else:
                    session = self.find_session(fd=socket_fd)
                    data = utils.recvall(socket_fd)
                    if not data:
                        # When session is None then sessino killed manually
                        # Else session DO SUICIDE
                        if session:
                            print("\r", end='')
                            utils.Log.warning(f"Session {session.rhost}:{session.rport} dead")
                            self.restore_prompt()
                            self.close_connection(session, False)
                        continue
                        # break
                    try:
                        data = data.decode(session.encoding)
                    except (UnicodeDecodeError, UnicodeError):
                        utils.Log.error("Cant decode session output. Check&change encoding.")
                    else:
                        if not session.is_interactive:
                            print('\r', end='')
                            utils.Log.success(f"{session.rhost}:{session.rport}")
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
                        print("\r", end='')
                        utils.Log.error(f"Cant send data to session {session.rhost}:{session.rport}")
                        self.restore_prompt()
                        self.close_connection(session)
                else:
                    self.outputs.remove(socket_fd)

            for socket_fd in error_sockets:
                # MMMMM?
                if socket_fd is self.master_socket:
                    print()
                    utils.Log.error("MASTER ERROR")
                    self.shutdown()
                if session := self.find_session(fd=socket_fd):
                    self.close_connection(session)
                    print('1')

        utils.Log.warning("Master exiting...")
        self.master_socket.shutdown(socket.SHUT_RDWR)
        self.master_socket.close()
        th.join()

    def interface(self):
        while True:
            if self.EXIT_FLAG:
                break

            self.restore_prompt()
            command = input()
            if not command:
                continue
            match command.split(' '):
                case ["h"] | ["help"] | ["/help"] | ["show", "help"]:
                    print("[h]  help                        display this message\n"
                          "[s]  sessions                    display sessions list\n"
                          "[i]  info                        display info about current session\n"
                          "[g]  goto ID|IDX                 switch to another session\n"
                          "[in] interact                    start interactive shell\n"
                          "[e]  encoding ENC                changes session encoding\n"
                          "[k]  kill [ID|IDX]               kill active or specified session\n"
                          "[c]  cmd CMD                     execute single command in current session\n"
                          "[ac] multiple_cmd CMD            execute single command in all sessions\n"
                          "[e]  exit                        shutdown\n")
                    print(f"{'-' * 0x2A}")

                case ["s"] | ["sessions"] | ["/sessions"] | ["show", "sessions"] | ["list"]:
                    if len(self.sessions) == 0:
                        utils.Log.warning("No online sessions")
                    else:
                        utils.Log.info("Listing online sessions...")
                        utils.Log.info(f"{len(self.sessions)} sessions online")
                        for id_ in self.sessions:
                            print(f"{'-' * 0x2A}")
                            print(f"Index: {list(self.sessions.keys()).index(id_)}")
                            print(f"Hash: {self.sessions[id_].session_hash}")
                            print(f"From: {self.sessions[id_].rhost}:{self.sessions[id_].rport}")
                            print(f"ASN: {self.sessions[id_].asn} {self.sessions[id_].asn_org}")
                            print(f"Location: {self.sessions[id_].country}, {self.sessions[id_].region}, {self.sessions[id_].city}. TZ: {self.sessions[id_].timezone}")
                        print(f"{'-' * 0x2A}")

                case ["g", id_] | ["goto", id_] | ["/goto", id_] | ["use", id_]:
                    if new_session := self.find_session(id_=id_, idx=id_):
                        self.active_session = new_session
                    else:
                        utils.Log.warning("This session does not exist")

                case ["i"] | ["info"] | ["/info"] | ["show", "info"]:
                    if self.active_session:
                        print(f"{'-' * 0x2A}")
                        print(f"Hash: {self.active_session.session_hash}")
                        print(f"From: {self.active_session.rhost}:{self.active_session.rport}")
                        print(f"ASN: {self.active_session.asn} {self.active_session.asn_org}")
                        print(f"Location: {self.active_session.country}, {self.active_session.region}, {self.active_session.city}. TZ: {self.active_session.timezone}")
                        print(f"{'-' * 0x2A}")
                    else:
                        utils.Log.warning("Current session is FUCKING DEAD")

                case ["in"] | ["interact"] | ["/interact"]:
                    if self.active_session:
                        utils.Log.info("Enter interactive mode...")
                        self.active_session.interact()
                    else:
                        utils.Log.warning("Current session is FUCKING DEAD")

                case ["e", encoding] | ["chenc", encoding] | ["/encoding", encoding]:
                    if self.active_session:
                        try:
                            codecs.lookup(encoding)
                        except LookupError:
                            utils.Log.error("Bad encoding")
                        else:
                            self.active_session.encoding = encoding
                    else:
                        utils.Log.warning("Current session is FUCKING DEAD")

                case ["k", *session] | ["kill", *session] | ["/kill", *session]:
                    if not session and self.active_session:
                        self.active_session.kill()
                    elif session and (session_obj := self.find_session(id_=session[0], idx=session[0])):
                        session_obj.kill()
                    else:
                        utils.Log.warning("Session not found")

                case ["c", *cmdline] | ["cmd", *cmdline] | ["/cmd", *cmdline]:
                    if self.active_session:
                        self.active_session.send_command(" ".join(cmdline))
                    else:
                        utils.Log.warning("Current session is FUCKING DEAD")

                case ["ac", *cmdline] | ["acmd", *cmdline] | ["/acmd", *cmdline]:
                    for id_ in self.sessions:
                        self.sessions[id_].send_command(" ".join(cmdline))
                case ["exit"] | ["/exit"] | ["q"] | ["quit"]:
                    self.shutdown()
                    break

                case _:
                    utils.Log.error("Unknown command")

    def handle_connection(self):
        session_socket, session_addr = self.master_socket.accept()

        if self.ssl:
            try:
                session_socket = self.ssl.wrap_socket(session_socket, True)
            except ssl.SSLCertVerificationError:
                utils.Log.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. Bad certificate")
                return
            except ssl.SSLError as ex:
                utils.Log.error(f"Connection from {session_addr[0]}:{session_addr[1]} dropped. {ex}")
                return

        if not self.allow_duplicate_sessions:
            for id_ in self.sessions:
                if self.sessions[id_].rhost == session_addr[0]:
                    utils.Log.warning("Detect the same host connection, dropping...")
                    self.restore_prompt()
                    session_socket.shutdown(socket.SHUT_RDWR)
                    session_socket.close()
                    return

        if self.suppress_banner:
            session_socket.send("pwd\n".encode())
            time.sleep(1)
            utils.recvall(session_socket)

        print("\r", flush=True, end='')
        utils.Log.info(f"New session: {session_addr[0]}:{session_addr[1]}")
        self.restore_prompt()

        self.inputs.append(session_socket)
        session = Session(session_socket, not self.blackout)
        session.set_callbacks(self.read_callback, self.write_callback, self.error_callback)
        self.sessions[session.session_hash] = session

    def close_connection(self, session, show_msg=True):
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
        self.sessions.pop(session.session_hash)
        if show_msg:
            utils.Log.warning(f"Session {session.rhost}:{session.rport} killed")

    def find_session(self, *, fd: socket.socket = None, id_: str = None, idx: int = None) -> Session:
        if fd:
            for id_ in self.sessions:
                if self.sessions[id_].socket == fd:
                    return self.sessions[id_]
        if id_ and id_ in self.sessions:
            return self.sessions.get(id_)
        if idx:
            if not isinstance(idx, int):
                try:
                    idx = int(idx)
                except ValueError:
                    return None
            if 0 <= idx < len(self.sessions):
                return self.sessions.get(list(self.sessions.keys())[idx])
        return None

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

    def restore_prompt(self):
        if self.active_session:
            utils.Log.context(f"{self.active_session.rhost}:{self.active_session.rport}")
        else:
            utils.Log.context("NO_SESSION")
        print(">> ", end='', flush=True)

    def shutdown(self, *args):
        utils.Log.warning("Exit...")
        self.EXIT_FLAG = True
        while 0 < len(self.sessions):
            self.close_connection(self.sessions[list(self.sessions.keys())[0]])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    # parser = argparse.ArgumentParser(description="PR0J3C794:R3V3R53_SH311_H4ND13R")
    parser.add_argument("-H", "--lhost",
                        type=str,
                        metavar="HOST",
                        help="Host to listen",
                        default="0.0.0.0")
    parser.add_argument("-p", "--lport",
                        type=int,
                        metavar="PORT",
                        help="Port to listen",
                        default=443)
    parser.add_argument("-k", "--keyfile",
                        type=argparse.FileType(mode='r'),
                        help="keyfile for ssl")
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

    print("\n"
          "     ########:: ########::: #######:::::::: ##: ########:: ######:: ########:: #######:: ##::::::::\n"
          "     ##.... ##: ##.... ##: ##.... ##::::::: ##: ##.....:: ##... ##:... ##..:: ##.... ##: ##::: ##::\n"
          "     ##:::: ##: ##:::: ##: ##:::: ##::::::: ##: ##::::::: ##:::..::::: ##:::: ##:::: ##: ##::: ##::\n"
          "     ########:: ########:: ##:::: ##::::::: ##: ######::: ##:::::::::: ##::::: ########: ##::: ##::\n"
          "     ##.....::: ##.. ##::: ##:::: ##: ##::: ##: ##...:::: ##:::::::::: ##:::::...... ##: #########:\n"
          "     ##:::::::: ##::. ##:: ##:::: ##: ##::: ##: ##::::::: ##::: ##:::: ##::::'##:::: ##:...... ##::\n"
          "     ##:::::::: ##:::. ##:. #######::. ######:: ########:. ######::::: ##::::. #######:::::::: ##::\n"
          "    ..:::::::::..:::::..:::.......::::......:::........:::......::::::..::::::.......:::::::::..:::\n"
          )

    app = Project94(a)
    app.main()
