from .base_command import BaseCommand


class MultiCommand(BaseCommand):
    @property
    def aliases(self) -> list[str]:
        return ["mc", "mcmd", "multicommand"]

    @property
    def description(self) -> str:
        return "execute single command in all sessions"

    @property
    def usage(self) -> str:
        return f"Usage: {self} CMDLINE"

    def __call__(self, *args, **kwargs):
        if 0 >= len(args):
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        for id_ in self._app.sessions:
            self._app.sessions[id_].send_command(" ".join(args[0]))
