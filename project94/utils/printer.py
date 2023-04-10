import sys


class Printer:
    colored = True

    @staticmethod
    def _black(line):
        return '\033[30m' + line + '\033[0m'

    @staticmethod
    def _blue(line):
        return '\033[94m' + line + '\033[0m'

    @staticmethod
    def _gray(line):
        return '\033[1;30m' + line + '\033[0m'

    @staticmethod
    def _green(line):
        return '\033[92m' + line + '\033[0m'

    @staticmethod
    def _cyan(line):
        return '\033[96m' + line + '\033[0m'

    @staticmethod
    def _light_purple(line):
        return '\033[94m' + line + '\033[0m'

    @staticmethod
    def _purple(line):
        return '\033[95m' + line + '\033[0m'

    @staticmethod
    def _red(line):
        return '\033[91m' + line + '\033[0m'

    @staticmethod
    def _yellow(line):
        return '\033[93m' + line + '\033[0m'

    @staticmethod
    def _default(line):
        return '\033[0m' + line + '\033[0m'

    @staticmethod
    def _default_bold(line):
        return '\033[1m' + line + '\033[0m'

    @staticmethod
    def _underline(line):
        return '\033[4m' + line + '\033[0m'

    @staticmethod
    def _print(line):
        sys.stdout.write(line)
        sys.stdout.flush()

    @staticmethod
    def info(message: str):
        Printer._print(f"\r[*] {Printer._light_purple(message) if Printer.colored else message}\n")

    @staticmethod
    def warning(message: str):
        Printer._print(f"\r[!] {Printer._yellow(message) if Printer.colored else message}\n")

    @staticmethod
    def error(message: str):
        Printer._print(f"\r[!!!] {Printer._red(message) if Printer.colored else message}\r\n")

    @staticmethod
    def success(message: str):
        Printer._print(f"\r[+] {Printer._green(message) if Printer.colored else message}\n")

    # @staticmethod
    # def context(context: str):
    #     Printer._print(f"\r[{Printer._gray(context) if Printer.colored else context}]")

    @staticmethod
    def context(context: str):
        return f"\r[{Printer._gray(context) if Printer.colored else context}]"
