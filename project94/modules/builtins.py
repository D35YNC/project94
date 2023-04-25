from .module_base import *
import socket


class Builtins(Module):
    @command(name="bind_shell", description="connects to bind shell")
    @params(IP=True, PORT=True)
    def bind_shell(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case (ip, port):
                try:
                    port = int(port)
                except ValueError:
                    kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(f"Cant convert {port} to int")
                    return
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect((ip, port))
                except socket.error:
                    kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(f"Cant connect to {ip}:{port}")
                else:
                    app.handle_connection(sock, sock.getpeername())

            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)

    @command(name="cmd", description="executes the command in the current or each session")
    @subcommands("current", "each")
    @params(CMDLINE=True)
    def cmd(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case ("current", *cmdline):
                if 0 == len(cmdline):
                    kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)
                    return
                if app.active_session:
                    if cmdline:
                        app.active_session.send_command(" ".join(cmdline))
                    else:
                        kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")

            case ("each", *cmdline):
                if 0 == len(cmdline):
                    kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)
                    return
                for id_ in app.sessions:
                    app.sessions[id_].send_command(" ".join(cmdline))
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)

    @command(name="encoding", description="changes active session encoding")
    @params(NEW_ENCODING=True)
    def encoding(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case (encoding,):
                if app.active_session:
                    app.active_session.encoding = encoding
                    kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))(f"Installed encoding: {app.active_session.encoding}")
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")

            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)

    @command(name="exit", description="shutdown project94")
    @long_description("its really just shutdown\n"
                      "Maybe I shouldn't make it as command. Because u can delete it xdd\n"
                      "Have fun =)")
    def exit(self, *args, **kwargs):
        app = kwargs.get("app")
        app.shutdown()

    @command(name="goto", description="switch to another session")
    @long_description("Session can be identified by ID (hash) or index in sessions list\n"
                      "U can view ID and index using \"/show sessions\" command\n"
                      "ID arg can be specified partially. Ex. session ID - sus0GOvm0Za1100ppa\n"
                      "U can goto this session with \"/goto sus0\"")
    @params(SESSION_ID=True, SESSION_INDEX=True)
    def goto(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case (session_id,):
                if new_session := app.get_session(id_=session_id, idx=session_id):
                    app.active_session = new_session
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("This session does not exist")
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)

    @command(name="help", description="display help message")
    @long_description("IM A FUCKING PSYCHO\n"
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
    @params(COMMAND=False)
    def help(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case (cmd_name,):
                if cmd := app.commands.get(cmd_name):
                    kwargs.get("print_info_callback", lambda x: print(f"[!] {x}"))(f"Help: {cmd.name}")
                    print(f"Description: {cmd.description}")
                    if cmd.long_description:
                        print(cmd.long_description)
                    print(cmd.usage)
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))(f"Command {cmd_name} not found")
            case _:
                for cmd in app.commands:
                    print(f"{cmd:<20}{app.commands[cmd].description}")

    @command(name="interact", description="start interactive shell")
    @long_description("DO NOT USE KEYBOARD SHORTCUTS =)")
    def interact(self, *args, **kwargs):
        app = kwargs.get("app")
        if app.active_session:
            kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))("Enter interactive mode...")
            app.active_session.interactive = True
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")

    @command(name="kill", description="kill active or specified session")
    @long_description("Specifying session works as in \"/goto\" command")
    @params(SESSION_ID=True, SESSION_INDEX=True)
    def kill(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case (session_id,):
                if session_obj := app.get_session(id_=session_id, idx=session_id):
                    session_obj.kill()
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))(f"Session {session_id} not found")
            case _:
                if app.active_session:
                    app.active_session.kill()
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")

    @command(name="show", description="displays information of specified type")
    @long_description("sessions - shows list of sessions and information about them\n"
                      "info     - shows information about active session")
    @subcommands("sessions", "info")
    def show(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case ("info", ):
                if app.active_session:
                    print(f"Hash: {app.active_session.session_hash}")
                    print(f"From: {app.active_session.rhost}:{app.active_session.rport}")
                    print(f"Encoding: {app.active_session.encoding}")
                    for ext in app.active_session.extended_info:
                        print(f"{ext}: {app.active_session.extended_info[ext]}")
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
            case ("sessions", ):
                if len(app.sessions) == 0:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("No online sessions")
                else:
                    kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))("Listing online sessions...")
                    kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))(f"{len(app.sessions)} sessions online")
                    for id_ in app.sessions:
                        print('-' * 0x2A)
                        print(f"Index: {list(app.sessions.keys()).index(id_)}")
                        print(f"Hash: {app.sessions[id_].session_hash}")
                        print(f"From: {app.sessions[id_].rhost}:{app.sessions[id_].rport}")
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)
