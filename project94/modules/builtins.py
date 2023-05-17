import os.path
import socket
import time

import charset_normalizer

from .module_base import *
from ..listener import Listener, ListenerInitError, ListenerStartError, ListenerStopError
from ..session import Session
from ..utils.printer import Printer, print_certificate


class Builtins(Module):
    # cmd = Command(name="cmd", description="executes the command in the current or each session")
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
            self.app.register_session(Session(sock, None))

    # @cmd.subcommand(name="current", description="execute CMDLINE in current session")
    # def cmd_current(self, *cmdline):
    #     if not cmdline or len(cmdline) == 0:
    #         Printer.error("cmdline not specified")
    #         return
    #
    #     if session := self.app.active_session:
    #         session.send_command(" ".join(cmdline))
    #     else:
    #         Printer.warning("Current session is FUCKING DEAD")
    #
    # @cmd.subcommand(name="each", description="execute CMDLINE in each sessions")
    # def cmd_each(self, *cmdline):
    #     if not cmdline or len(cmdline) == 0:
    #         Printer.error("cmdline not specified")
    #         return
    #
    #     for id_ in self.app.sessions:
    #         self.app.sessions[id_].send_command(" ".join(cmdline))

    @command(name="encoding", description="changes active session encoding")
    def encoding(self, new_encoding: str):
        if session := self.app.active_session:
            session.encoding = new_encoding
            Printer.info(f"Installed encoding: {session.encoding}")
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @encoding.subcommand(name="autodetect", description="Trying to autodetect encoding")
    def encoding_autodetect(self, *cmdline):
        if session := self.app.active_session:
            if len(cmdline) == 0:
                cmdline = "whoami"
            else:
                cmdline = ' '.join(cmdline)
            data = session.send_command_and_recv(cmdline, True)
            detect = charset_normalizer.detect(data)
            Printer.info(f"Encoding detected {detect['encoding']}. Try it")
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @command(name="exit",
             description="shutdown project94",
             long_description="its really just shutdown\n"
                              "Maybe I shouldn't make it as command. Have fun =)")
    def exit(self):
        self.app.shutdown()

    @command(name="goto",
             description="switch to another session",
             long_description="Session can be identified by ID (hash) or index in sessions list\n"
                              "U can view ID and index using \"session list\" command\n"
                              "ID arg can be specified partially. Ex. session ID - sus0GOvm0Za1100ppa\n"
                              "U can goto this session with \"goto sus0\"")
    def goto(self, session_id: str):
        if new_session := self.app.get_session(id_=session_id, idx=session_id):
            self.app.active_session = new_session
        else:
            Printer.warning(f"Session \"{session_id}\" not found")

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
                print(f"Description: {cmd.description}")
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

    @command(name="interact",
             description="start interactive shell",
             long_description="DO NOT USE KEYBOARD SHORTCUTS =)")
    def interact(self):
        if self.app.active_session:
            Printer.info("Enter interactive mode...")
            self.app.active_session.interactive = True

            if 0 < len(self.app.active_session.recv_data):
                for msg in self.app.active_session.recv_data:
                    print(msg, end='')
                self.app.active_session.recv_data.clear()

        else:
            Printer.warning("Current session is FUCKING DEAD")

    @command(name="kill",
             description="kill active or specified session",
             long_description="Specifying session works as in \"goto\" command")
    def kill(self, session_id: str = ""):
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
            print(f"Listener: {listener.name}")
            print(f"Address: {listener.lhost}:{listener.lport}")
            print(f"State: {listener.state}")
            print(f"Autorun: {'Enabled' if listener.autorun else 'Disabled'}")
            if listener.ssl_enabled:
                print(f"SSL: Enabled")
                stat = listener.ssl_context.cert_store_stats()
                print(f"X509 CA loaded: {stat.get('x509_ca')}")
                print(f"X509 loaded: {stat.get('x509')}")
                print("CA certs:")
                certs = listener.ssl_context.get_ca_certs()
                for cert in certs:
                    print('-' * 0x2A)
                    print_certificate(cert)
            else:
                print(f"SSL: Disabled")

            print(f"Active sessions: {len(listener.sockets)}")
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
        #
        try:
            listener = Listener(name, ip, port)
        except ListenerInitError as ex:
            Printer.error(str(ex))
        else:
            if ans.lower().startswith('y'):
                listener.setup(False, True, True)
                Printer.info(f"U need initialize certificates. Use \"listener ssl setup {name}\" to do it.")
            else:
                listener.setup(False, True)
            Printer.info(f"Listener: {listener} created")
            self.app.listeners.append(listener)

    @listener.subcommand(name="start", description="starting specified listener")
    def listener_start(self, name: str):
        if listener := self.app.get_listener(name=name):
            try:
                sock = listener.start()
            except ListenerStartError as ex:
                Printer.error(str(ex))
            else:
                self.app.add_listener_sock(sock)
                Printer.success(f"Listener {listener} Start: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="stop", description="stops specified listener")
    def listener_stop(self, name: str):
        if listener := self.app.get_listener(name=name):
            self.app.del_listener_sock(listener.listen_socket)
            time.sleep(0.5)
            try:
                listener.stop()
            except ListenerStopError as ex:
                Printer.error(str(ex))
            else:
                Printer.success(f"Listener {listener} Stop: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="restart", description="restarting specified listener")
    def listener_restart(self, name: str):
        if listener := self.app.get_listener(name=name):
            Printer.info(f"Restarting listener {listener}")
            self.app.del_listener_sock(listener.listen_socket)
            time.sleep(0.5)
            try:
                sock = listener.restart()
            except ListenerStartError as ex:
                Printer.error(str(ex))
                Printer.error(f"{listener} Restart: Fail")
            except ListenerStopError:
                Printer.error(f"{listener} Restart: Fail")
            else:
                self.app.add_listener_sock(sock)
                Printer.success(f"Listener {listener} Restart: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="delete", description="deleting specified listener")
    def listener_delete(self, name: str):
        if listener := self.app.get_listener(name=name):
            Printer.info(f"Deleting listener {listener}")
            self.app.del_listener_sock(listener.listen_socket)
            time.sleep(0.5)
            try:
                listener.stop()
            except ListenerStopError as ex:
                pass  # Printer.error(str(ex))
            self.app.listeners.remove(listener)
            Printer.success(f"Listener {listener} Delete: OK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="ssl", description="managing listener ssl certificates")
    def listener_ssl(self, action, name):

        def get_filename_input(prompt):
            value = ""
            while not os.path.isfile(value):
                value = input(f"{prompt}: ")
                if value.strip() == '':
                    return ''
                elif value == "exit":
                    return None
            else:
                value = os.path.normpath(os.path.join(os.getcwd(), os.path.expanduser(value)))
                return value

        listener = self.app.get_listener(name=name)
        if not listener:
            Printer.warning(f"Listener \"{name}\" not found")
            return

        match action.lower():
            case "all" | "setup":
                ca = get_filename_input("CA [ENTER FOR SKIP]")
                if ca is None:
                    return
                cert = get_filename_input("CERT [ENTER FOR SKIP]")
                if cert is None:
                    return
                key = get_filename_input("KEY [ENTER FOR SKIP]")
                if key is None:
                    return

                if action.lower() == "setup":
                    listener.setup_ssl([ca], [(cert, key if key else None)])
                else:
                    if ca:
                        if listener.load_ca(ca):
                            Printer.info(f"CA {ca} loaded")
                    if cert:
                        if listener.load_cert(cert, key or None):
                            Printer.info(f"CERT {cert}{f' and KEY {key} ' if key is not None else ' '}loaded")
            case "ca":
                ca = get_filename_input("CA")
                if ca is None:
                    return
                if ca:
                    if listener.load_ca(ca):
                        Printer.info("CA loaded")
            case "cert" | "key":
                cert = get_filename_input("CERT")
                if cert is None:
                    return
                key = get_filename_input("KEY")
                if key is None:
                    return

                if listener.load_cert(cert, key or None):
                    Printer.info(f"CERT {cert}{f' and KEY {key} ' if key is not None else ' '}loaded")
            case _:
                Printer.error("Bad action specified, need: [all, setup, ca, cert, key]")

    @listener.subcommand(name="enable", description="enables listener autorun")
    def listener_enable_autorun(self, name, setting):
        if listener := self.app.get_listener(name=name):
            if listener.autorun:
                Printer.warning(f"Listener \"{listener.name}\" autorun is already enabled")
            else:
                listener.autorun = True
                Printer.success(f"Listener \"{listener.name}\" autorun enabled")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="disable", description="disables listener autorun")
    def listener_enable_autorun(self, name, setting):
        if listener := self.app.get_listener(name=name):
            if not listener.autorun:
                Printer.warning(f"Listener \"{listener.name}\" autorun is already disabled")
            else:
                listener.autorun = False
                Printer.success(f"Listener \"{listener.name}\" autorun disabled")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

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

    @session.subcommand(name="status", description="shows information about active session")
    def sessions_status(self, session_id: str = ""):
        def print_session(session_obj):
            print(f"Hash: {session_obj.hash}")
            print(f"From: {session_obj.rhost}:{session_obj.rport}")
            print(f"Encoding: {session_obj.encoding}")
            if session_obj.ssl_enabled:
                print(f"SSL: Enabled")
                print("Cert:")
                cert = session_obj.cert
                print_certificate(cert)
            else:
                print(f"SSL: Disabled")

            for ext in session_obj.extended_info:
                print(f"{ext}: {session_obj.extended_info[ext]}")

        if session_id:
            if session := self.app.get_session(id_=session_id, idx=session_id):
                print_session(session)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif session := self.app.active_session:
            print_session(session)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    def on_command_error(self, *args, **kwargs):
        error = args[0]
        cmd = args[1]
        arg = args[2]
        Printer.error(f"{error}, {cmd}, {arg}")
