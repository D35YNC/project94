from .base_command import BaseCommand


class Help(BaseCommand):
    @property
    def description(self) -> str:
        return "display help message"

    @property
    def usage(self) -> str:
        return f"Usage: {self} [CMD]"

    def __call__(self, *args, **kwargs):
        match args:
            case ("/help", cmd_name):
                if cmd := self._app.commands.get(cmd_name):
                    kwargs.get("print_info_callback", lambda x: print(f"[!] {x}"))(f"Help: {cmd}")
                    print(f"Description: {cmd.description}")
                    # print(f"Aliases: {', '.join(cmd.aliases)}.")
                    print(cmd.usage)
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))(f"Command {cmd_name} not found")
            case _:
                for cmd in self._app.commands:
                    print(f"{cmd:<20}{self._app.commands[cmd].description}")
