import abc


def command(*, name: str = None, description: str = None):
    def wrapper(func):
        return Command(func, name, description)
    return wrapper


def long_description(content: str):
    def wrapper(cmd):
        if isinstance(cmd, Command):
            cmd._set_long_description(content)
        else:
            cmd.__project94_command_long_description = content
        return cmd
    return wrapper


def subcommands(*options):
    def wrapper(cmd):
        if 0 < len(options):
            r = [str(x) for x in options]
            if isinstance(cmd, Command):
                cmd._set_subcommands(r)
                cmd._update_usage_string()
            else:
                cmd.__project94_command_subcommands = r
        return cmd
    return wrapper


def params(**options):
    def wrapper(cmd):
        if 0 < len(options):
            r = {}
            for opt in options:
                if options[opt]:
                    r[opt] = True
                else:
                    r[opt] = False
            if isinstance(cmd, Command):
                cmd._set_args(r)
                cmd._update_usage_string()
            else:
                cmd.__project94_command_params = r

        return cmd
    return wrapper


class Command:
    def __init__(self, func, name: str = "", description: str = ""):
        self.__func = func
        self.__name = name.lower() if name else func.__name__.lower()
        self.__description = description if description else func.__doc__
        self.__long_description = getattr(func, "__project94_command_long_description") if hasattr(func, "__project94_command_long_description") else func.__doc__
        self.__usage = ""
        self.__subcommands = getattr(func, "__project94_command_subcommands") if hasattr(func, "__project94_command_subcommands") else []
        self.__args = getattr(func, "__project94_command_params") if hasattr(func, "__project94_command_params") else {}
        self._update_usage_string()

    def __call__(self, *args, **kwargs):
        self.__func(*args, command=self, **kwargs)

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
    def subcommands(self):
        return self.__subcommands

    def _update_usage_string(self):
        self.__usage = f"Usage: {self.__name}"
        if self.__subcommands:
            self.__usage += f" {{{' '.join(self.__subcommands)}}}"
        if self.__args:
            if not_required := [arg for arg in self.__args if not self.__args[arg]]:
                self.__usage += f" [{' '.join(not_required)}]"
            if required := [arg for arg in self.__args if self.__args[arg]]:
                self.__usage += f" {' '.join(required)}"

    def _set_subcommands(self, value):
        self.__subcommands = value

    def _set_args(self, value):
        self.__args = value

    def _set_long_description(self, value):
        self.__long_description = value


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

    def on_master_ready(self, *args, **kwargs):
        pass

    def on_master_dead(self, *args, **kwargs):
        pass

    def on_session_ready(self, *args, **kwargs):
        pass

    def on_session_dead(self, *args, **kwargs):
        pass
