import abc
import inspect


def command(*, name: str = None, description: str = None, long_description: str = None):
    def wrapper(func):
        return Command(func=func, name=name, description=description, long_description=long_description)
    return wrapper


class Command:
    def __init__(self, parent=None, func: callable = None, name: str = "", description: str = "", long_description: str = ""):
        if parent and isinstance(parent, Command):
            self.__parent = parent
        else:
            # TODO: exception
            self.__parent = None

        self.__func = func if func else lambda *args, **kwargs: print(f"Usage: {self.usage}")
        self.__name = name.lower() if name else func.__name__.lower()
        self.__description = description
        self.__long_description = long_description

        self.__subcommands = []
        self.__args = {}
        self.__args_required_count = 0
        self.__unlimited_args = False
        self.__usage = ""

        func_info = inspect.getfullargspec(self.__func)
        params = func_info.args or []
        defaults = func_info.defaults or []
        for param in params:
            if param == "self":
                continue
            if len(params) - params.index(param) <= len(defaults):
                self.__args[param.upper()] = defaults[params.index(param) - len(params)]
            else:
                self.__args[param.upper()] = None

        if func_info.varargs:
            self.__args[func_info.varargs.upper()] = None
            self.__unlimited_args = True

        if self.__parent:
            parent.subcommands.append(self)

        self._update_usage_string()

    def __call__(self, *args, **kwargs):
        # TODO:
        #  Unlimited nesting of commands
        if self.has_subcommands and 1 < len(args):
            for subcmd in self.__subcommands:
                if args[0] == self.name and args[1] == subcmd.name:
                    if subcmd.required_args_count <= len(args[2:]) <= subcmd.args_count or subcmd.args_count == -1:
                        subcmd(*(args[2:]), **kwargs)
                    else:
                        print(f"Use: ", subcmd.usage)
                    return

        if 0 == len(args) == self.args_count:
            self.__func(self, **kwargs)
        elif (self.required_args_count <= len(args) <= self.args_count or self.args_count == -1) and self.is_subcommand:
            self.__func(self, *args, **kwargs)
        elif (self.required_args_count <= len(args) - 1 <= self.args_count or self.args_count == -1) and not self.is_subcommand:
            self.__func(self, *args[1:], **kwargs)
        else:
            print("Use:", self.usage)

    def subcommand(self, *, name: str = None, description: str = None, long_description: str = None):
        def wrapper(func):
            c = Command(self, func, name, description, long_description)
            self._update_usage_string()
            return c
        return wrapper

    def _update_usage_string(self):
        self.__usage = ""
        if self.is_subcommand:
            self.__usage += f" {self.__parent.name}"

        self.__usage += f" {self.__name}"

        if self.has_subcommands:
            self.__usage += f" {{{' '.join(subcmd.name for subcmd in self.__subcommands)}}}"

        if self.__args:
            if required := [arg for arg in self.__args if self.__args[arg] is None]:
                self.__usage += f" {' '.join(required)}"
                self.__args_required_count = len(required)
            if not_required := [arg for arg in self.__args if self.__args[arg] is not None]:
                self.__usage += f" [{' '.join(not_required)}]"

    @property
    def module(self):
        return self.__module__

    @property
    def name(self):
        return self.__name.lower()

    @property
    def usage(self):
        return self.__usage

    @property
    def description(self):
        return self.__description

    @property
    def long_description(self):
        return self.__long_description

    @property
    def parent(self):
        return self.__parent

    @property
    def is_subcommand(self):
        return self.__parent is not None

    @property
    def has_subcommands(self):
        return len(self.__subcommands) > 0

    @property
    def subcommands(self):
        return self.__subcommands

    @property
    def args_count(self):
        return len(self.__args) if not self.__unlimited_args else -1

    @property
    def required_args_count(self):
        return self.__args_required_count


class Module(abc.ABC):
    def __init__(self, app):
        self._app = app
        self.__commands: dict[str, Command] = {}

    @property
    def name(self):
        return self.__class__.__name__

    def get_commands(self) -> dict[str, Command]:
        if len(self.__commands) == 0:
            for attr in dir(self):
                if not attr.startswith("_"):
                    cmd = getattr(self, attr)
                    if isinstance(cmd, Command):
                        self.__commands[cmd.name] = cmd
        return self.__commands

    def on_ready(self, *args, **kwargs):
        pass

    def on_shutdown(self, *args, **kwargs):
        pass

    def on_session_ready(self, *args, **kwargs):
        pass

    def on_session_dead(self, *args, **kwargs):
        pass
