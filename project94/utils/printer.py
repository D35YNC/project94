import datetime
import os


def input_filename(prompt):
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


def print_certificate(cert):
    for k in cert:
        print(f"{k[0].upper() + k[1:]}:", end=' ')
        if isinstance(cert[k], tuple):
            print()
            for field in cert[k]:
                print(f"{field[0][0]:>25}: {field[0][1]}")
        else:
            print(f"{cert[k]}")


def print_listener(listener, verbose=False):
    print(f"Listener: {listener.name}")
    print(f"Address: {listener.lhost}:{listener.lport}")
    print(f"State: {listener.state}")
    print(f"Autorun: {'Enabled' if listener.autorun else 'Disabled'}")
    if listener.ssl_enabled:
        print(f"SSL: Enabled")
        if verbose:
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
    if verbose:
        print("Last 10 log records:")
        for record in listener.log[-10:]:
            print(record)


def print_session(session, verbose=False):
    print(f"Hash: {session.hash}")
    print(f"From: {session.rhost}:{session.rport}")
    if verbose:
        print(f"Listener: {session.listener}")
    print(f"When: {datetime.datetime.fromtimestamp(session.timestamp).strftime('%m.%d %H:%M:%S')}")
    print(f"Encoding: {session.encoding}")
    if session.ssl_enabled:
        print(f"SSL: Enabled")
        if verbose:
            print("Cert:")
            print_certificate(session.cert)
    else:
        print(f"SSL: Disabled")


def _inject_time(func):
    def wrapper(message):
        t = datetime.datetime.now()
        func(f"[{t.strftime('%H:%M:%S')}] {message}")
    return wrapper


class Printer:
    colored = True

    @staticmethod
    def paint_black(line):
        return '\033[30m' + line + '\033[0m'

    @staticmethod
    def paint_blue(line):
        return '\033[94m' + line + '\033[0m'

    @staticmethod
    def paint_gray(line):
        return '\033[1;30m' + line + '\033[0m'

    @staticmethod
    def paint_green(line):
        return '\033[92m' + line + '\033[0m'

    @staticmethod
    def paint_cyan(line):
        return '\033[96m' + line + '\033[0m'

    @staticmethod
    def paint_light_purple(line):
        return '\033[94m' + line + '\033[0m'

    @staticmethod
    def paint_purple(line):
        return '\033[95m' + line + '\033[0m'

    @staticmethod
    def paint_red(line):
        return '\033[91m' + line + '\033[0m'

    @staticmethod
    def paint_yellow(line):
        return '\033[93m' + line + '\033[0m'

    @staticmethod
    def drop_color(line):
        return '\033[0m' + line + '\033[0m'

    @staticmethod
    def _default_bold(line):
        return '\033[1m' + line + '\033[0m'

    @staticmethod
    def _underline(line):
        return '\033[4m' + line + '\033[0m'

    @staticmethod
    @_inject_time
    def info(message: str):
        print(f"\r[*] {Printer.paint_light_purple(message) if Printer.colored else message}", flush=True)

    @staticmethod
    @_inject_time
    def warning(message: str):
        print(f"\r[!] {Printer.paint_yellow(message) if Printer.colored else message}", flush=True)

    @staticmethod
    @_inject_time
    def error(message: str):
        print(f"\r[ERROR] {Printer.paint_red(message) if Printer.colored else message}", flush=True)

    @staticmethod
    @_inject_time
    def success(message: str):
        print(f"\r[+] {Printer.paint_green(message) if Printer.colored else message}", flush=True)

    @staticmethod
    def context(context: str):
        return f"\r[{Printer.paint_gray(context) if Printer.colored else context}]"
