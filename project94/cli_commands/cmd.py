from .base_command import BaseCommand


class Cmd(BaseCommand):
    @property
    def description(self) -> str:
        return "executes the command in the current or each session"

    @property
    def usage(self) -> str:
        return f"Usage: {self} {{current, each}} CMDLINE"

    @property
    def subcommands(self) -> list[str]:
        return ["current", "each"]

    def __call__(self, *args, **kwargs):
        match args:
            case ("/cmd", "current", *cmdline):
                if 0 == len(cmdline):
                    kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
                    return
                if self._app.active_session:
                    if cmdline:
                        self._app.active_session.send_command(" ".join(cmdline))
                    else:
                        kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")

            case ("/cmd", "each", *cmdline):
                if 0 == len(cmdline):
                    kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
                    return
                for id_ in self._app.sessions:
                    self._app.sessions[id_].send_command(" ".join(cmdline))
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
