from .base_command import BaseCommand


class Kill(BaseCommand):
    __args_count = 1

    @property
    def aliases(self) -> list[str]:
        return ["k", "kill"]

    @property
    def description(self) -> str:
        return "kill active or specified session"

    @property
    def usage(self) -> str:
        return f"Usage: {self} SESSION_ID | SESSION_INDEX"

    def __call__(self, *args, **kwargs):
        if len(args) != 1:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if not args[0] and self._app.active_session:
            self._app.active_session.kill()
        elif args[0] and (session_obj := self._app.find_session(id_=args[0], idx=args[0])):
            session_obj.kill()
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Session not found")
