import abc
import argparse


class Command(abc.ABC):
    @abc.abstractmethod
    def __init__(self, app, name: str = "", description: str = "", long_description: str = ""):
        self.parser = argparse.ArgumentParser(name,
                                              description=description,
                                              epilog=long_description,
                                              formatter_class=argparse.RawDescriptionHelpFormatter,
                                              exit_on_error=False)
        self.subparsers = None
        self.app = app
        self.__subcommands = []

    def __call__(self, args):
        a = self.parser.parse_args(args)
        self.main(a)

    @abc.abstractmethod
    def main(self, args):
        raise NotImplementedError()

    @property
    def name(self):
        return self.parser.prog

    @property
    def description(self):
        return self.parser.description

    @property
    def long_description(self):
        return self.parser.epilog

    @property
    def help(self):
        return self.parser.format_help()

    @property
    def usage(self):
        return self.parser.format_usage()

    @property
    def subcommands(self) -> list[str]:
        return self.__subcommands

    @property
    def has_subcommands(self):
        return 0 < len(self.__subcommands)

    def add_subcommand(self, name, description) -> argparse.ArgumentParser:
        self.__subcommands.append(name)
        if not self.subparsers:
            self.subparsers = self.parser.add_subparsers()
        return self.subparsers.add_parser(name, description=description)
