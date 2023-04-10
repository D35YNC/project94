from .base_command import BaseCommand


class Help(BaseCommand):
    @property
    def aliases(self) -> list[str]:
        return ["h", "help", "?"]

    @property
    def description(self) -> str:
        return "display help message"

    @property
    def usage(self) -> str:
        return f"Usage: {self} [CMD]"

    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            if cmd := self._app.commands.get(args[0]):
                print(f"{'Command':<20}Description")
                print(f"{str(cmd):<20}{cmd.description}")
                print(cmd.usage)
            else:
                kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Command not found")
                return
        else:
            for cmd in self._app.commands:
                print(f"{cmd:<20}{self._app.commands[cmd].description}")
        # print('-' * 0x2A)
