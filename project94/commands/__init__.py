import argparse


class Command:
    def __init__(self, app, name: str = "", description: str = "", long_description: str = "", parser: argparse.ArgumentParser = None):
        self.__parser = parser or argparse.ArgumentParser(name,
                                                          description=description,
                                                          epilog=long_description,
                                                          formatter_class=argparse.RawDescriptionHelpFormatter)
        self.app = app
        self.__subparsers = None
        self.__mutually_exclusive_group = None
        self.__args_groups = {}
        self.__subcommands = {}

    def __call__(self, args):
        a = self.__parser.parse_args(args)
        self.main(a)

    def main(self, args):
        if hasattr(args, "func"):
            args.func(args)

    def add_argument(self, *args, **kwargs):
        self.__parser.add_argument(*args, **kwargs)

    def add_subcommand(self, name: str, description: str, main: callable = None):
        if not self.__subparsers:
            self.__subparsers = self.__parser.add_subparsers()
        subcommand = Command(self.app, parser=self.__subparsers.add_parser(name, description=description))
        if main:
            subcommand.__parser.set_defaults(func=main)
        self.__subcommands[name] = subcommand
        return subcommand

    def add_argument_group(self, name: str, description: str = None) -> argparse._ArgumentGroup:
        if name not in self.__args_groups:
            self.__args_groups[name] = self.__parser.add_argument_group(name, description)
        return self.__args_groups[name]

    def add_mutually_exclusive_group(self, required: bool = False) -> argparse._MutuallyExclusiveGroup:
        if not self.__mutually_exclusive_group:
            self.__mutually_exclusive_group = self.__parser.add_mutually_exclusive_group(required=required)
        return self.__mutually_exclusive_group

    @property
    def name(self):
        return self.__parser.prog

    @property
    def description(self):
        return self.__parser.description

    @property
    def long_description(self):
        return self.__parser.epilog

    @property
    def help(self):
        return self.__parser.format_help()

    @property
    def usage(self):
        return self.__parser.format_usage()

    @property
    def subcommands(self) -> dict:
        return self.__subcommands

    @property
    def has_subcommands(self):
        return 0 < len(self.__subcommands)
