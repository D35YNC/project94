import time

from project94.commands import Command

from project94.listener import Listener
from project94.listener import ListenerStartError
from project94.listener import ListenerStopError

from project94.utils.printer import Printer
from project94.utils.printer import print_listener
from project94.utils.printer import print_session

try:
    from prettytable import PrettyTable
except ImportError:
    PrettyTable = None


class ListenerCmd(Command):
    def __init__(self, app):
        super().__init__(app, name="listener", description="listeners management")

        # listener create
        create = self.add_subcommand("create", description="initializing new listener", main=self.create)
        create.add_argument("name", type=str, help="listener name")
        create.add_argument("lhost", type=str, help="host for binding")
        create.add_argument("lport", type=int, help="port for binding")
        create.add_argument("-S", "--enable-ssl", action="store_true", help="enable ssl", default=False)
        create.add_argument("-D", "--drop-duplicates", action="store_true", help="drop duplicates connections", default=False)
        create.add_argument("-A", "--autorun", action="store_true", help="run this listener on run project94", default=False)
        create.add_argument("--ssl-cafile", type=str, help="cafile for ssl")
        create.add_argument("--ssl-certfile", type=str, help="certfile for ssl")
        create.add_argument("--ssl-keyfile", type=str, help="keyfile for ssl")

        # listener status
        status = self.add_subcommand("status", description="shows status of specified listener", main=self.status)
        status.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        status.add_argument("-V", "--verbose", action="store_true", help="show more information in list mode", default=False)

        # listener list
        list_ = self.add_subcommand("list", description="shows list of listeners and some information about them", main=self.list)
        list_.add_argument("-T", "--table", action="store_true", help="format output as table")

        # listener start
        start = self.add_subcommand("start", description="starting specified listener", main=self.start)
        start.add_argument("listener_name", metavar="listener", type=str, help="listener id")

        # listener stop
        stop = self.add_subcommand("stop", description="stops specified listener", main=self.stop)
        stop.add_argument("listener_name", metavar="listener", type=str, help="listener id")

        # listener restart
        restart = self.add_subcommand("restart", description="restarting specified listener", main=self.restart)
        restart.add_argument("listener_name", metavar="listener", type=str, help="listener id")

        # listener delete
        delete = self.add_subcommand("delete", description="deleting specified listener", main=self.delete)
        delete.add_argument("listener_name", metavar="listener", type=str, help="listener id")

        # listener ssl
        ssl_ = self.add_subcommand("ssl", description="ssl management", main=self.ssl)
        ssl_.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        ssl_.add_argument("--ssl-cafile", type=str, help="cafile for ssl")
        ssl_.add_argument("--ssl-certfile", type=str, help="certfile for ssl")
        ssl_.add_argument("--ssl-keyfile", type=str, help="keyfile for ssl")

        # listener enable
        enable = self.add_subcommand("enable", description="enable listener autorun", main=self.enable)
        enable.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        enable.add_argument("--autorun", action="store_true", help="enable autorun", default=False)
        enable.add_argument("--drop-duplicates", action="store_true", help="enable drop duplicates connections", default=False)

        # listener disable
        disable = self.add_subcommand("disable", description="disable listener autorun", main=self.disable)
        disable.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        disable.add_argument("--autorun", action="store_true", help="disable autorun", default=False)
        disable.add_argument("--drop-duplicates", action="store_true", help="disable drop duplicates connections", default=False)

        # listener sessions
        sessions = self.add_subcommand("sessions", description="shows sessions accepted by listener", main=self.sessions)
        sessions.add_argument("listener_name", metavar="listener", type=str, help="listener id")

    def create(self, args):
        if args.ssl_keyfile and not args.ssl_certfile:
            self.__parser.error("cant use keyfile without certfile")
            return

        name = args.name
        lhost = args.lhost
        lport = args.lport
        ssl_required = args.enable_ssl
        drop_duplicates = args.drop_duplicates
        autorun = args.autorun
        try:
            listener = Listener(name, lhost, lport)
            listener.setup(autorun, drop_duplicates, ssl_required)
        except Exception as ex:
            Printer.error(str(ex))
            return

        if ssl_required:
            listener.setup_ssl()
            if args.ssl_cafile:
                try:
                    listener.load_ca(args.ssl_cafile)
                except Exception as ex:
                    Printer.error(str(ex))
                else:
                    Printer.success("Ca OK")
            if args.certfile:
                try:
                    listener.load_cert(args.certfile, args.keyfile if args.keyfile else None)
                except Exception as ex:
                    Printer.error(str(ex))
                else:
                    Printer.success("Cert OK")
        else:
            listener.setup(False, True)
        Printer.info(f"{listener} created")
        self.app.listeners.append(listener)

    def status(self, args):
        if listener := self.app.get_listener(listener_id=args.listener_name):
            print_listener(listener)
        else:
            Printer.warning(f"Listener \"{args.listener_name}\" not found")

    def list(self, args):
        if len(self.app.listeners) == 0:
            Printer.warning("No available listeners")
        elif args.table:
            if PrettyTable:
                t = PrettyTable(["State", "Name", "Address", "SSL", "#Sessions", "Autorun", "Drop duplicates"])
                for listener in self.app.listeners:
                    t.add_row(
                        [listener.state, listener.name, f"{listener.lhost}:{listener.lport}", listener.ssl_enabled,
                         len(listener.sockets), listener.autorun, listener.drop_duplicates])
                print(t)
            else:
                Printer.warning("prettytable not installed")
        else:
            Printer.info("Listing all listeners...")
            for listener in self.app.listeners:
                print('-' * 0x2A)
                print(f"Name: {listener.name}")
                print(f"Address: {listener.lhost}:{listener.lport}")
                print(f"State: {listener.state}")
                print(f"Active sessions: {len(listener.sockets)}")

    def start(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
            try:
                listener.start()
            except ListenerStartError as ex:
                Printer.error(str(ex))
            else:
                self.app.register_listener(listener)
                Printer.success(f"{str(listener)} Start: OK")
        else:
            Printer.warning(f"Listener \"{listener_id}\" not found")

    def stop(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
            self.app.unregister_listener(listener)
            time.sleep(0.5)
            try:
                listener.stop()
            except ListenerStopError as ex:
                Printer.error(str(ex))
            else:
                Printer.success(f"{str(listener)} Stop: OK")
        else:
            Printer.warning(f"Listener \"{listener_id}\" not found")

    def restart(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
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
            Printer.warning(f"Listener \"{listener_id}\" not found")

    def delete(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
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
            Printer.warning(f"Listener \"{listener_id}\" not found")

    def ssl(self, args):
        if args.ssl_keyfile and not args.ssl_certfile:
            self.__parser.error("cant use keyfile without certfile")
            return

        listener_id = args.listener_name
        listener = self.app.get_listener(listener_id=listener_id)
        if not listener:
            Printer.warning(f"Listener \"{listener_id}\" not found")
            return

        if args.ssl_cafile:
            if listener.load_ca(args.ssl_cafile):
                Printer.info(f"CA {args.ssl_cafile} loaded")

        if args.ssl_certfile:
            if listener.load_cert(args.ssl_certfile, args.ssl_keyfile if args.ssl_keyfile else None):
                Printer.info(f"CERT {args.ssl_certfile}{f' and KEY {args.ssl_keyfile} ' if args.ssl_keyfile else ' '}loaded")

    def enable(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
            if args.autorun:
                if listener.autorun:
                    Printer.warning(f"Listener \"{listener.name}\" autorun is already enabled")
                else:
                    listener.autorun = True
                    Printer.success(f"Listener \"{listener.name}\" autorun enabled")
            elif args.drop_duplicates:
                if listener.drop_duplicates:
                    Printer.warning(f"Listener \"{listener.name}\" droppin dups is already enabled")
                else:
                    listener.drop_duplicates = True
                    Printer.success(f"Listener \"{listener.name}\" droppin dups enabled")
        else:
            Printer.warning(f"Listener \"{listener_id}\" not found")

    def disable(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
            if args.autorun:
                if not listener.autorun:
                    Printer.warning(f"Listener \"{listener.name}\" autorun is already disabled")
                else:
                    listener.autorun = False
                    Printer.success(f"Listener \"{listener.name}\" autorun disabled")
            elif args.drop_duplicates:
                if not listener.drop_duplicates:
                    Printer.warning(f"Listener \"{listener.name}\" droppin dups is already disabled")
                else:
                    listener.drop_duplicates = False
                    Printer.success(f"Listener \"{listener.name}\" droppin dups disabled")
        else:
            Printer.warning(f"Listener \"{listener_id}\" not found")

    def sessions(self, args):
        listener_id = args.listener_name
        if listener := self.app.get_listener(listener_id=listener_id):
            print(f"Active sessions: {len(listener.sockets)}")
            for sock in listener.sockets:
                if session := self.app.get_session(socket_=sock):
                    print_session(session)
        else:
            Printer.warning(f"Listener \"{listener_id}\" not found")
