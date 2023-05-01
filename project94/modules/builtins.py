import os.path
import socket

import charset_normalizer

from .module_base import *
from ..listener import Listener
from ..utils import Printer


class Builtins(Module):
    cmd = Command(name="cmd", description="executes the command in the current or each session")
    session = Command(name="session", description="displays information of specified type")
    listener = Command(name="listener", description="listeners management")

    @command(name="bind_shell", description="connects to bind shell")
    def bind_shell(self, ip: str, port: int, **kwargs):
        app = kwargs.get("app")
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
            app.handle_connection(sock, sock.getpeername())

    @cmd.subcommand(name="current", description="execute CMDLINE in current session")
    def cmd_current(self, *cmdline, **kwargs):
        app = kwargs.get("app")
        if len(cmdline) == 0:
            Printer.error(kwargs.get("command").usage)
            return

        if app.active_session:
            if cmdline:
                app.active_session.send_command(" ".join(cmdline))
            else:
                Printer.error(kwargs.get("command").usage)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @cmd.subcommand(name="each", description="execute CMDLINE in each sessions")
    def cmd_each(self, *cmdline, **kwargs):
        app = kwargs.get("app")
        if len(cmdline) == 0:
            Printer.error(kwargs.get("command").usage)
            return
        for id_ in app.sessions:
            app.sessions[id_].send_command(" ".join(cmdline))

    @command(name="encoding", description="changes active session encoding")
    def encoding(self, new_encoding: str, **kwargs):
        app = kwargs.get("app")
        if session := app.active_session:
            session.encoding = new_encoding
            Printer.info(f"Installed encoding: {session.encoding}")
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @encoding.subcommand(name="autodetect", description="Trying to autodetect encoding")
    def autodetect_encoding(self, *cmd, **kwargs):
        app = kwargs.get("app")
        if session := app.active_session:
            if len(cmd) == 0:
                cmd = "whoami"
            else:
                cmd = ' '.join(cmd)
            data = session.send_command_and_recv(cmd, True)
            detect = charset_normalizer.detect(data)
            Printer.info(f"Encoding detected {detect['encoding']}. Try it")
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @command(name="exit",
             description="shutdown project94",
             long_description="its really just shutdown\n"
                              "Maybe I shouldn't make it as command. Have fun =)")
    def exit(self, **kwargs):
        app = kwargs.get("app")
        app.shutdown()

    @command(name="goto",
             description="switch to another session",
             long_description="Session can be identified by ID (hash) or index in sessions list\n"
                              "U can view ID and index using \"/show sessions\" command\n"
                              "ID arg can be specified partially. Ex. session ID - sus0GOvm0Za1100ppa\n"
                              "U can goto this session with \"/goto sus0\"")
    def goto(self, session_id: str, **kwargs):
        app = kwargs.get("app")
        if new_session := app.get_session(id_=session_id, idx=session_id):
            app.active_session = new_session
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
    def help(self, command_name: str = "", **kwargs):
        app = kwargs.get("app")
        if command_name:
            if cmd := app.commands.get(command_name):
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
                Printer.warning(f"Command {command_name} not found")
        else:
            for cmd in app.commands:
                print(f"{cmd:<20}{app.commands[cmd].description}")

    @command(name="interact",
             description="start interactive shell",
             long_description="DO NOT USE KEYBOARD SHORTCUTS =)")
    def interact(self, **kwargs):
        app = kwargs.get("app")
        if app.active_session:
            Printer.info("Enter interactive mode...")
            app.active_session.interactive = True
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @command(name="kill",
             description="kill active or specified session",
             long_description="Specifying session works as in \"/goto\" command")
    def kill(self, session_id: str = "", **kwargs):
        app = kwargs.get("app")
        if session_id:
            if session_obj := app.get_session(id_=session_id, idx=session_id):
                session_obj.kill()
            else:
                Printer.warning(f"Session {session_id} not found")
        elif session := app.active_session:
            session.kill()
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @listener.subcommand(name="list", description="shows list of listeners and some information about them")
    def listener_list(self, **kwargs):
        app = kwargs.get("app")
        if len(app.listeners) == 0:
            Printer.warning("No available listeners")
        else:
            Printer.info("Listing all listeners...")
            for listener in app.listeners:
                print('-' * 0x2A)
                print(f"Name: {listener.name}")
                print(f"Address: {listener.lhost}:{listener.lport}")
                print(f"State: {listener.state}")
                print(f"Active sessions: {len(listener.sockets)}")

    @listener.subcommand(name="status", description="shows status of specified listener")
    def listener_status(self, name: str, **kwargs):
        app = kwargs.get("app")
        if listener := app.get_listener(name=name):
            print(f"Listener: {listener.name}")
            print(f"Address: {listener.lhost}:{listener.lport}")
            print(f"State: {listener.state}")
            print(f"Autorun: {'Enabled' if listener.autorun else 'Disabled'}")
            print(f"SSL: {'Enabled' if listener.ssl_enabled else 'Disabled'}")
            if listener.ssl_enabled:
                stat = listener.certs_status
                print(f"X509 CA loaded: {stat.get('x509_ca')}")
                print(f"X509 loaded: {stat.get('x509')}")
            print(f"Active sessions: {len(listener.sockets)}")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="create", description="initializing new listener")
    def listener_create(self, **kwargs):
        app = kwargs.get("app")
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
        if ans.lower().startswith('y'):
            listener = Listener(app, name, ip, port, True)
            Printer.info(f"U need initialize certificates. Use \"listener edit_ssl {name} all\" to do it.")
        else:
            listener = Listener(app, name, ip, port, False)

        Printer.info(f"Listener: {listener} created")
        app.listeners.append(listener)

    @listener.subcommand(name="start", description="starting specified listener")
    def listener_start(self, name: str, **kwargs):
        app = kwargs.get("app")
        if listener := app.get_listener(name=name):
            Printer.info(f"Starting listener {listener}")
            s = listener.start()
            if s:
                app.add_listener_sock(s)
            # else:
            #     Printer.error("FUCK")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="stop", description="stops specified listener")
    def listener_stop(self, name: str, **kwargs):
        app = kwargs.get("app")
        if listener := app.get_listener(name=name):
            listener.stop()
            Printer.info(f"Listener {listener} stopped")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="restart", description="restarting specified listener")
    def listener_restart(self, name: str, **kwargs):
        app = kwargs.get("app")
        if listener := app.get_listener(name=name):
            Printer.info(f"Restarting listener {listener}")
            listener.restart()
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="delete", description="deleting specified listener")
    def listener_delete(self, name: str, **kwargs):
        app = kwargs.get("app")
        if listener := app.get_listener(name=name):
            listener.stop()
            app.listeners.remove(listener)
            Printer.info(f"Listener {listener} deleted")
        else:
            Printer.warning(f"Listener \"{name}\" not found")

    @listener.subcommand(name="ssl", description="managing listener ssl certificates")
    def listener_ssl(self, name, choice="", **kwargs):

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

        app = kwargs.get("app")
        listener = app.get_listener(name=name)
        if not listener:
            Printer.warning(f"Listener \"{name}\" not found")
            return

        match choice.lower():
            case "all":
                ca = get_filename_input("CA [ENTER FOR SKIP]")
                if ca is None:
                    return
                cert = get_filename_input("CERT [ENTER FOR SKIP]")
                if cert is None:
                    return
                key = get_filename_input("KEY [ENTER FOR SKIP]")
                if key is None:
                    return

                if ca:
                    if listener.load_ca(ca):
                        Printer.info("CA loaded")
                if cert:
                    if listener.load_cert(cert, key or None):
                        Printer.info("CERT/KEY loaded")
            case "ca":
                ca = get_filename_input("CA")
                if ca is None:
                    return
                if ca:
                    listener.load_ca(ca)
                    Printer.info("Ca is set?")
            case "cert" | "key":
                cert = get_filename_input("CERT")
                if cert is None:
                    return
                key = get_filename_input("KEY")
                if key is None:
                    return

                if cert:
                    listener.load_cert(cert, key or None)
                    Printer.info("Cert is set?")
            case _:
                Printer.error(kwargs.get("command").usage)

    @listener.subcommand(name="autorun", description="enables or disables autorun")
    def listener_autorun_state_change(self, name, state, **kwargs):
        app = kwargs.get("app")
        match state.lower():
            case "e" | "enable" | "1":
                if listener := app.get_listener(name=name):
                    if listener.autorun:
                        Printer.warning(f"Listener \"{listener.name}\" autorun is already enabled")
                    else:
                        listener.autorun = True
                        Printer.success(f"Listener \"{listener.name}\" autorun enabled")
                else:
                    Printer.warning(f"Listener \"{name}\" not found")
            case "d" | "disable" | "0":
                if listener := app.get_listener(name=name):
                    if not listener.autorun:
                        Printer.warning(f"Listener \"{listener.name}\" autorun is already disabled")
                    else:
                        listener.autorun = False
                        Printer.success(f"Listener \"{listener.name}\" autorun disabled")
                else:
                    Printer.warning(f"Listener \"{name}\" not found")
            case _:
                Printer.error("state - enable or disable")

    @session.subcommand(name="list", description="shows list of sessions and some information about them")
    def sessions_list(self, **kwargs):
        app = kwargs.get("app")
        if len(app.sessions) == 0:
            Printer.warning("No online sessions")
        else:
            Printer.info("Listing online sessions...")
            Printer.info(f"{len(app.sessions)} sessions online")
            for id_ in app.sessions:
                print('-' * 0x2A)
                print(f"Index: {list(app.sessions.keys()).index(id_)}")
                print(f"Hash: {app.sessions[id_].hash}")
                print(f"From: {app.sessions[id_].rhost}:{app.sessions[id_].rport}")

    @session.subcommand(name="status", description="shows information about active session")
    def sessions_status(self, session_id: str = None, **kwargs):
        def print_session(session_obj):
            print(f"Hash: {session_obj.hash}")
            print(f"From: {session_obj.rhost}:{session_obj.rport}")
            print(f"Encoding: {session_obj.encoding}")
            print(f"SSL: {'Enabled' if session_obj.ssl_enabled else 'Disabled'}")
            # TODO:
            # if session.ssl_enabled:
            #     print(f"SSL: Enabled")
            #     print(f"Cert: {session.socket.getpeercert()}")
            # else:
            #     print(f"SSL: Disabled")
            for ext in app.active_session.extended_info:
                print(f"{ext}: {app.active_session.extended_info[ext]}")

        app = kwargs.get("app")
        if session_id:
            if session := app.get_session(id_=session_id, idx=session_id):
                print_session(session)
            else:
                Printer.warning(f"Session {session_id} not found")
        elif session := app.active_session:
            print_session(session)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    # @session.subcommand(name="kill",
    #                     description="kill active or specified session")
    # #Specifying session works as in \"/goto\" command
    # def session_kill(self, session_id: str = None, **kwargs):
    #     app = kwargs.get("app")
    #     if session_id:
    #         if session_obj := app.get_session(id_=session_id, idx=session_id):
    #             session_obj.kill()
    #         else:
    #             Printer.warning(f"Session {session_id} not found")
    #     else:
    #         if app.active_session:
    #             app.active_session.kill()
    #         else:
    #             Printer.warning("Current session is FUCKING DEAD")
