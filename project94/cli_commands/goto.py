from .base_command import BaseCommand


class Goto(BaseCommand):
    @property
    def description(self) -> str:
        return "switch to another session"

    @property
    def usage(self) -> str:
        return f"Usage: {self} SESSION_ID | SESSION_INDEX"

    def __call__(self, *args, **kwargs):
        if len(args) != 2:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if new_session := self._app.find_session(id_=args[1], idx=args[1]):
            self._app.active_session = new_session
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("This session does not exist")
