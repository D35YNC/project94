from .base_command import BaseCommand


class Encoding(BaseCommand):
    @property
    def description(self) -> str:
        return "changes current session encoding"

    @property
    def usage(self) -> str:
        return f"Usage: {self} NEW_ENCODING"

    def __call__(self, *args, **kwargs):
        if len(args) != 2:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if self._app.active_session:
            self._app.active_session.encoding = args[1]
            kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))(f"Installed encoding: {self._app.active_session.encoding}")
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
