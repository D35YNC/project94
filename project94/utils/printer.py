import datetime


def _inject_time(func):
    def wrapper(message):
        t = datetime.datetime.now()
        func(f"[{t.strftime('%H:%M:%S')}] {message}")
    return wrapper


def print_certificate(cert):
    for k in cert:
        print(f"{k[0].upper() + k[1:]}:", end=' ')
        if isinstance(cert[k], tuple):
            print()
            for field in cert[k]:
                print(f"{field[0][0]:>25}: {field[0][1]}")
        else:
            print(f"{cert[k]}")


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
