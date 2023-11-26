import datetime

from project94.commands import Command

from project94.utils.printer import Printer
from project94.utils.printer import print_session

try:
    from prettytable import PrettyTable
except ImportError:
    PrettyTable = None


class SessionCmd(Command):
    def __init__(self, app):
        super().__init__(app, name="session", description="sessions management")

        # listener status
        status_parser = self.add_subcommand("status", "shows information about active or specified session")
        status_parser.add_argument("session_id", metavar="session", nargs='?', type=str, help="session id", default=None)
        status_parser.set_defaults(func=self.status)

        # session list
        list_parser = self.add_subcommand("list", "shows list of sessions and some information about them")
        list_parser.add_argument("-T", "--table", action="store_true", help="format output as table")
        list_parser.set_defaults(func=self.list)

        # session encoding
        encoding_parser = self.add_subcommand("encoding", "changes active session encoding")
        encoding_parser.add_argument("encoding", type=str, help="new encoding")
        encoding_parser.set_defaults(func=self.encoding)
        # session use
        use_parser = self.add_subcommand("use", "switch context to another session")
        use_parser.add_argument("session_id", metavar="session", type=str, help="session id")
        use_parser.set_defaults(func=self.use)

        # session shell
        shell_parser = self.add_subcommand("shell", "starts shell of active or specified session")
        shell_parser.add_argument("session_id", metavar="session", nargs='?', type=str, help="session id", default=None)
        shell_parser.set_defaults(func=self.shell)

        kill_parser = self.add_subcommand("kill", "kill active or specified session")
        kill_parser.add_argument("session_id", metavar="session", nargs='?', type=str, help="session id", default=None)
        kill_parser.set_defaults(func=self.kill)

    def main(self, args):
        if hasattr(args, "func"):
            args.func(args)

    def status(self, args):
        session_id = args.session_id
        if session_id:
            if session := self.app.get_session(id_=session_id):
                print_session(session)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif session := self.app.active_session:
            print_session(session)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    def list(self, args):
        if len(self.app.sessions) == 0:
            Printer.warning("No online sessions")
        elif args.table:
            if PrettyTable:
                t = PrettyTable(["Hash", "Target", "Time", "SSL", "Encoding"])
                for id_ in self.app.sessions:
                    session = self.app.sessions[id_]
                    t.add_row([session.hash[:32], f"{session.rhost}:{session.rport}",
                               datetime.datetime.fromtimestamp(session.timestamp).strftime('%m.%d %H:%M:%S'),
                               session.ssl_enabled, session.encoding])
                print(t)
        else:
            Printer.info("Listing online sessions...")
            Printer.info(f"{len(self.app.sessions)} sessions online")
            for id_ in self.app.sessions:
                print('-' * 0x2A)
                print_session(self.app.sessions[id_])

    def encoding(self, args):
        new_encoding = args.encoding
        if session := self.app.active_session:
            session.encoding = new_encoding
            Printer.info(f"Installed encoding: {session.encoding}")
        else:
            Printer.warning("Current session is FUCKING DEAD")

    def use(self, args):
        session_id = args.session_id
        if not session_id:
            self.app.active_session = None
        elif session := self.app.get_session(id_=session_id):
            self.app.active_session = session
        else:
            Printer.warning(f"Session \"{session_id}\" not found")

    def shell(self, args):
        def enter_shell(session):
            Printer.info(f"{str(session)} : enter shell mode...")

            while not session.recv_data.empty():
                print(session.recv_data.get_nowait(), end='')
            print('-' * 10)
            session.shell_mode = True

        session_id = args.session_id
        if session_id:
            if session := self.app.get_session(id_=session_id):
                if self.app.active_session is not session:
                    self.app.active_session = session
                enter_shell(session)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif self.app.active_session:
            enter_shell(self.app.active_session)
        else:
            Printer.warning("Current session is FUCKING DEAD")

    def kill(self, args):
        session_id = args.session_id
        if session_id:
            if session := self.app.get_session(id_=session_id):
                self.app.close_session(session, its_manual_kill=True)
            else:
                Printer.warning(f"Session \"{session_id}\" not found")
        elif session := self.app.active_session:
            self.app.close_session(session, its_manual_kill=True)
        else:
            Printer.warning("Current session is FUCKING DEAD")
