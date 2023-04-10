from .base_command import BaseCommand


class Encoding(BaseCommand):
    __args_count = 1

    @property
    def aliases(self) -> list[str]:
        return ["e", "encoding", "chenc"]

    @property
    def description(self) -> str:
        return "changes current session encoding"

    @property
    def usage(self) -> str:
        return f"Usage: {self} NEW_ENCODING"

    def __call__(self, *args, **kwargs):
        if len(args) != self.__args_count:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if self._app.active_session:
            if args[0]:
                self._app.active_session.encoding = args[0] or "utf-8"
            else:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
