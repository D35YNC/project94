import os.path
import socket
import time
import datetime

from .module_base import *
from ..listener import Listener
from ..listener import ListenerStartError, ListenerStopError
from ..session import Session
from ..utils.printer import Printer, print_listener, print_session, input_filename


class Builtins(Module):
    session = Command(name="session", description="sessions management")
    listener = Command(name="listener", description="listeners management")

    @command(name="bind_shell", description="connects to bind shell")
    def bind_shell(self, ip: str, port: int):
        try:
            port = int(port)
        except ValueError:
            Printer.error(f"Cant convert {port} to int")
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except socket.error:
            Printer.error(f"Cant connect to {ip}:{port}")
        else:
            self.app.register_session(Session(sock, (ip, port), None))

    @command(name="exit",
             description="shutdown project94",
             long_description="its really just shutdown")
    def exit(self):
        self.app.shutdown()

    @command(name="help",
             description="display help message",
             long_description="IM A FUCKING PSYCHO\n"
                              "         ⠀⠀⠀⠀⠀⠀⣀⣀⣤⣤⣤⣤⣤⣤⣤⣤⣄⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                              "         ⠀⠀⠀⠀⣠⠞⠁⠀⡀⠄⣒⠨⠭⠭⠭⠉⢀⣒⣒⣚⠋⠙⢛⠶⣄⡀⠀⠀⠀\n"
                              "         ⠀⠀⠀⢰⠇⠀⠀⢎⠰⡱⣆⣉⣉⡉⠇⠀⠀⠀⠰⠶⠆⠰⢀⠀⠀⢹⡀⠀⠀\n"
                              "         ⠀⠀⢀⡞⠀⠀⠁⠢⠊⠱⢀⣀⣀⠠⠉⠢⠀⠀⢘⠠⠒⡒⢒⠒⡠⡘⣇⠀⠀\n"
                              "         ⢀⡴⠟⢒⣒⣂⡒⢇⠀⡀⠻⠿⠿⠂⡪⢤⠃⢤⣆⠰⠀⢴⣿⡦⢀⣘⢌⢳⡀\n"
                              "         ⡞⠈⣰⠋⠀⣎⡙⠋⠉⠂⠴⠤⠤⠅⠒⠁⠀⠀⢿⡲⠅⣠⣐⡢⡐⠺⢰⠡⡇\n"
                              "         ⣇⠀⢻⡐⠻⡏⠙⠲⣤⣀⡒⠒⠊⣟⢩⣤⡀⠀⠀⣹⡦⢀⠀⠀⣧⠠⣊⢴⠇\n"
                              "         ⠸⣎⠶⡀⠀⣿⣷⣀⣷⠈⠉⠿⢶⣏⣀⠀⠀⠰⡾⠁⠀⢀⣰⡿⣾⡏⢀⡏⠀\n"
                              "         ⠀⠘⢧⡀⠀⢸⣿⣿⣿⣷⣶⣤⣞⡀⠉⠉⡟⠛⢻⠛⠛⢹⠁⣟⣽⡇⢸⠀⠀\n"
                              "         ⠀⠀⠈⢧⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⠀⠀\n"
                              "         ⠀⠀⠀⠈⠳⣄⠻⡝⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⠀⠀\n"
                              "         ⠀⠀⠀⠀⢠⠏⠳⡝⢾⡃⠈⠙⢻⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠘⡇⠀\n"
                              "         ⠀⠀⠀⠀⣿⠀⠀⠸⡆⠹⣶⣀⡏⠀⠀⠀⡏⠉⠿⡿⠿⡿⢿⣏⣏⡏⠀⡇⠀\n"
                              "         ⠀⠀⠀⠀⢻⠀⠀⠀⠈⠢⣄⡙⠓⠶⠤⢤⣧⣀⣰⣃⣴⡧⠾⠶⠚⠀⡼⠁⠀\n"
                              "         ⠀⠀⠀⡴⠙⢖⠒⠢⢄⡀⠀⠉⠓⠲⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠴⠚⠁⠀⠀\n")
    def help(self, command_name: str = ""):
        if command_name:
            if cmd := self.app.commands.get(command_name):
                Printer.info(f"Help: {cmd.name}")
                print(cmd.description)
                if cmd.long_description:
                    print(cmd.long_description)
                if cmd.has_subcommands:
                    for subcmd in cmd.subcommands:
                        print(f"{subcmd.name:<10} - {subcmd.description}")
                        if subcmd.long_description:
                            print(subcmd.long_description)
                print("Usage:")
                print(cmd.usage)
                if cmd.has_subcommands:
                    for subcmd in cmd.subcommands:
                        print(subcmd.usage)
            else:
                Printer.warning(f"Command \"{command_name}\" not found")
        else:
            for cmd in self.app.commands:
                print(f"{cmd:<20}{self.app.commands[cmd].description}")

    #
    # Sessions
    #

    @session.subcommand(name="list", description="shows list of sessions and some information about them")
    def sessions_list(self):
        if len(self.app.sessions) == 0:
            Printer.warning("No online sessions")
        else:
            Printer.info("Listing online sessions...")
            Printer.info(f"{len(self.app.sessions)} sessions online")
            for id_ in self.app.sessions:
                print('-' * 0x2A)
                print(f"Index: {list(self.app.sessions.keys()).index(id_)}")
                print(f"Hash: {self.app.sessions[id_].hash}")
                print(f"From: {self.app.sessions[id_].rhost}:{self.app.sessions[id_].rport}")
                print(f"When: {datetime.datetime.fromtimestamp(self.app.sessions[id_].timestamp).strftime('%m.%d %H:%M:%S')}")

    @session.subcommand(name="status", description="shows information about active or specified session")
    def sessions_status(self, session_id: str = ""):
        if session_id:
            if session := self.app.get_session(id_=session_id, idx=session_id):
                print_session(session)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif session := self.app.active_session:
            print_session(session)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @session.subcommand(name="encoding", description="changes active session encoding")
    def encoding(self, new_encoding: str):
        if session := self.app.active_session:
            session.encoding = new_encoding
            Printer.info(f"Installed encoding: {session.encoding}")
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @session.subcommand(name="goto", description="switch to another session")
    def goto(self, session_id: str = ""):
        if not session_id:
            self.app.active_session = None
        elif session := self.app.get_session(id_=session_id, idx=session_id):
            self.app.active_session = session
        else:
            Printer.warning(f"Session \"{session_id}\" not found")

    @session.subcommand(name="shell", description="starts shell of active or specified session")
    def session_shell(self, session_id: str = ""):
        def enter_shell(session):
            Printer.info(f"{str(session)} : enter shell mode...")
            session.shell_mode = True

            while not session.recv_data.empty():
                print(session.recv_data.get_nowait(), end='')

        if session_id:
            if session := self.app.get_session(id_=session_id, idx=session_id):
                if self.app.active_session is not session:
                    self.app.active_session = session
                enter_shell(session)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif self.app.active_session:
            enter_shell(self.app.active_session)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @session.subcommand(name="kill", description="kill active or specified session")
    def session_kill(self, session_id: str = ""):
        if session_id:
            if session := self.app.get_session(id_=session_id, idx=session_id):
                self.app.close_session(session, its_manual_kill=True)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif session := self.app.active_session:
            self.app.close_session(session, its_manual_kill=True)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    #
    # Listeners
    #

    @listener.subcommand(name="list", description="shows list of listeners and some information about them")
    def listener_list(self):
        if len(self.app.listeners) == 0:
            Printer.warning("No available listeners")
        else:
            Printer.info("Listing all listeners...")
            for listener in self.app.listeners:
                print('-' * 0x2A)
                print(f"Name: {listener.name}")
                print(f"Address: {listener.lhost}:{listener.lport}")
                print(f"State: {listener.state}")
                print(f"Active sessions: {len(listener.sockets)}")

    @listener.subcommand(name="status", description="shows status of specified listener")
    def listener_status(self, name: str):
        if listener := self.app.get_listener(name=name):
            print_listener(listener)
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="create", description="initializing new listener")
    def listener_create(self):
        print("Interactive listener creation [type exit to exit]")
        name = input("Name: ")
        if name == "exit":
            return
        #
        ip = input("IP [0.0.0.0]: ") or "0.0.0.0"
        if ip == "exit":
            return
        #
        port = -1
        while not (0 < port < 0xFFFF):
            val = input("Port [443]: ") or 443
            if val == "exit":
                return
            try:
                port = int(val)
            except ValueError:
                pass
        #
        ans = ""
        while ans not in ['y', 'n', 'yes', 'no']:
            ans = input("Enable SSL [y/n] ").lower()
        # TODO CHECK TIS FUK
        try:
            listener = Listener(name, ip, port)
        except Exception as ex:
            Printer.error(str(ex))
            return

        if ans.lower().startswith('y'):
            listener.setup(False, True, True)
            ca = input_filename("CA")
            if ca is None:
                return
            cert = input_filename("CERT")
            if cert is None:
                return
            key = input_filename("KEY")
            if key is None:
                return

            try:
                listener.setup_ssl([ca], [(cert, key if key else None)])
            except Exception as ex:
                Printer.error(str(ex))
                # TODO Message about ssl eror and cant create listener
                return
            else:
                Printer.success("SSL enabled")
        else:
            listener.setup(False, True)
        Printer.info(f"{listener} created")
        self.app.listeners.append(listener)

    @listener.subcommand(name="start", description="starting specified listener")
    def listener_start(self, name: str):
        if listener := self.app.get_listener(name=name):
            try:
                listener.start()
            except ListenerStartError as ex:
                Printer.error(str(ex))
            else:
                self.app.register_listener(listener)
                Printer.success(f"{str(listener)} Start: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="stop", description="stops specified listener")
    def listener_stop(self, name: str):
        if listener := self.app.get_listener(name=name):
            self.app.unregister_listener(listener)
            time.sleep(0.5)
            try:
                listener.stop()
            except ListenerStopError as ex:
                Printer.error(str(ex))
            else:
                Printer.success(f"{str(listener)} Stop: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="restart", description="restarting specified listener")
    def listener_restart(self, name: str):
        if listener := self.app.get_listener(name=name):
            Printer.info(f"Restarting listener {listener}")
            self.app.unregister_listener(listener)
            time.sleep(0.5)
            try:
                listener.restart()
            except ListenerStartError as ex:
                Printer.error(str(ex))
                Printer.error(f"{listener} Restart: Fail")
            except ListenerStopError:
                Printer.error(f"{listener} Restart: Fail")
            else:
                self.app.register_listener(listener)
                Printer.success(f"{str(listener)} Restart: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="delete", description="deleting specified listener")
    def listener_delete(self, name: str):
        if listener := self.app.get_listener(name=name):
            Printer.info(f"Deleting listener {listener}")
            self.app.unregister_listener(listener)
            time.sleep(0.5)
            try:
                listener.stop()
            except ListenerStopError:
                pass
            self.app.listeners.remove(listener)
            Printer.success(f"{str(listener)} Delete: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="ssl", description="managing listener ssl certificates")
    def listener_ssl(self, name, action):
        listener = self.app.get_listener(name=name)
        if not listener:
            Printer.warning(f"Listener \"{name}\" not found")
            return

        match action.lower():
            case "ca":
                ca = input_filename("CA")
                if ca is None:
                    return
                if listener.load_ca(ca):
                    Printer.info("CA loaded")
            case "cert":
                cert = input_filename("CERT")
                if cert is None:
                    return
                key = input_filename("KEY")
                if key is None:
                    return

                if listener.load_cert(cert, key or None):
                    Printer.info(f"CERT {cert}{f' and KEY {key} ' if key != '' else ' '}loaded")
            case _:
                Printer.error("Bad action specified, need: [ca, cert]")

    @listener.subcommand(name="enable", description="enables listener autorun")
    def listener_enable_autorun(self, name):
        if listener := self.app.get_listener(name=name):
            if listener.autorun:
                Printer.warning(f"Listener \"{listener.name}\" autorun is already enabled")
            else:
                listener.autorun = True
                Printer.success(f"Listener \"{listener.name}\" autorun enabled")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="disable", description="disables listener autorun")
    def listener_disable_autorun(self, name):
        if listener := self.app.get_listener(name=name):
            if not listener.autorun:
                Printer.warning(f"Listener \"{listener.name}\" autorun is already disabled")
            else:
                listener.autorun = False
                Printer.success(f"Listener \"{listener.name}\" autorun disabled")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="sessions", description="shows sessions accepted by listener")
    def listener_sessions_list(self, name):
        if listener := self.app.get_listener(name=name):
            print(f"Active sessions: {len(listener.sockets)}")
            for sock in listener.sockets:
                if session := self.app.get_session(socket_=sock):
                    print_session(session)
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    def on_command_error(self, *args, **kwargs):
        error = args[0]
        cmd = args[1]
        arg = args[2]
        Printer.error(f"comanderor hok {error}, {cmd}, {arg}")
