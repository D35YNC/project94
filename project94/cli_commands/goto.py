from .base_command import BaseCommand


class Goto(BaseCommand):
    __args_count = 1

    @property
    def aliases(self) -> list[str]:
        return ["g", "goto"]

    @property
    def description(self) -> str:
        return "switch to another session"

    @property
    def usage(self) -> str:
        return f"Usage: {self} SESSION_ID | SESSION_INDEX"

    def __call__(self, *args, **kwargs):
        if len(args) != self.__args_count:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if new_session := self._app.find_session(id_=args[0], idx=args[0]):
            self._app.active_session = new_session
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("This session does not exist")
