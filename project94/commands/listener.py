import time

from project94.commands import Command

from project94.listener import Listener
from project94.listener import ListenerStartError
from project94.listener import ListenerStopError

from project94.utils.printer import Printer
from project94.utils.printer import print_listener
from project94.utils.printer import print_session


class ListenerCmd(Command):
    def __init__(self, app):
        super().__init__(app, name="listener", description="listeners management")

        # listener create
        create_parser = self.add_subcommand("create", description="initializing new listener")
        create_parser.add_argument("name", type=str, help="listener name")
        create_parser.add_argument("lhost", type=str, help="host for binding")
        create_parser.add_argument("lport", type=int, help="port for binding")
        create_parser.add_argument("-S", "--enable-ssl", action="store_true", help="enable ssl", default=False)
        create_parser.add_argument("-D", "--drop-duplicates", action="store_true", help="drop duplicates connections", default=False)
        create_parser.add_argument("-A", "--autorun", action="store_true", help="run this listener on run project94", default=False)
        create_parser.add_argument("--ssl-cafile", type=str, help="cafile for ssl")
        create_parser.add_argument("--ssl-certfile", type=str, help="certfile for ssl")
        create_parser.add_argument("--ssl-keyfile", type=str, help="keyfile for ssl")
        create_parser.set_defaults(func=self.create)

        # listener status
        status_parser = self.add_subcommand("status", description="shows status of specified listener")
        status_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        status_parser.set_defaults(func=self.status)

        # listener list
        list_parser = self.add_subcommand("list", description="shows list of listeners and some information about them")
        list_parser.add_argument("-T", "--table", action="store_true", help="format output as table")
        list_parser.set_defaults(func=self.list)

        # listener start
        start_parser = self.add_subcommand("start", description="starting specified listener")
        start_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        start_parser.set_defaults(func=self.start)

        # listener stop
        stop_parser = self.add_subcommand("stop", description="stops specified listener")
        stop_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        stop_parser.set_defaults(func=self.stop)

        # listener restart
        restart_parser = self.add_subcommand("restart", description="restarting specified listener")
        restart_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        restart_parser.set_defaults(func=self.restart)

        # listener delete
        delete_parser = self.add_subcommand("delete", description="deleting specified listener")
        delete_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        delete_parser.set_defaults(func=self.delete)

        # ssl
        ssl_parser = self.add_subcommand("ssl", description="ssl management")
        ssl_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        ssl_parser.add_argument("--ssl-cafile", type=str, help="cafile for ssl")
        ssl_parser.add_argument("--ssl-certfile", type=str, help="certfile for ssl")
        ssl_parser.add_argument("--ssl-keyfile", type=str, help="keyfile for ssl")
        ssl_parser.set_defaults(func=self.ssl)

        # enable
        enable_parser = self.add_subcommand("enable", description="enable listener autorun")
        enable_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        enable_parser.add_argument("--autorun", action="store_true", help="enable autorun", default=False)
        enable_parser.add_argument("--drop-duplicates", action="store_true", help="enable drop duplicates connections", default=False)
        enable_parser.set_defaults(func=self.enable)

        # disable
        disable_parser = self.add_subcommand("disable", description="disable listener autorun")
        disable_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        disable_parser.add_argument("--autorun", action="store_true", help="disable autorun", default=False)
        disable_parser.add_argument("--drop-duplicates", action="store_true", help="disable drop duplicates connections", default=False)
        disable_parser.set_defaults(func=self.disable)

        sessions_parser = self.add_subcommand("sessions", description="shows sessions accepted by listener")
        sessions_parser.add_argument("listener_name", metavar="listener", type=str, help="listener id")
        sessions_parser.set_defaults(func=self.sessions)

    def main(self, args):
        if hasattr(args, "func"):
            args.func(args)

    def create(self, args):
        if args.ssl_keyfile and not args.ssl_certfile:
            self.parser.error("cant use keyfile without certfile")
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
            self.parser.error("cant use keyfile without certfile")
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
