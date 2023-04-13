from .base_command import BaseCommand


class Command(BaseCommand):
    @property
    def aliases(self) -> list[str]:
        return ["c", "cmd", "command"]

    @property
    def description(self) -> str:
        return "execute single command in current session"

    @property
    def usage(self) -> str:
        return f"Usage: {self} CMDLINE"

    def __call__(self, *args, **kwargs):
        if 0 >= len(args):
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if self._app.active_session:
            if args:
                self._app.active_session.send_command(" ".join(args))
            else:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
