import os.path

from .module_base import *
import socket
from ..listener import Listener
from ..utils import Printer


class Builtins(Module):
    cmd = Command(name="cmd", description="executes the command in the current or each session")
    session = Command(name="session", description="displays information of specified type")

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
        if app.active_session:
            app.active_session.encoding = new_encoding
            Printer.info(f"Installed encoding: {app.active_session.encoding}")
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
        else:
            if app.active_session:
                app.active_session.kill()
            else:
                Printer.warning("Current session is FUCKING DEAD")

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
                print(f"Hash: {app.sessions[id_].session_hash}")
                print(f"From: {app.sessions[id_].rhost}:{app.sessions[id_].rport}")

    @session.subcommand(name="info", description="shows information about active session")
    def sessions_info(self, **kwargs):
        app = kwargs.get("app")
        if app.active_session:
            print(f"Hash: {app.active_session.session_hash}")
            print(f"From: {app.active_session.rhost}:{app.active_session.rport}")
            print(f"Encoding: {app.active_session.encoding}")
            for ext in app.active_session.extended_info:
                print(f"{ext}: {app.active_session.extended_info[ext]}")
        else:
            Printer.warning("Current session is FUCKING DEAD")
