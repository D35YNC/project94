from .base_command import BaseCommand


class Kill(BaseCommand):
    @property
    def description(self) -> str:
        return "kill active or specified session"

    @property
    def long_description(self):
        return f"{self.description}\n" \
               f"Specifying session works as in \"/goto\" command"

    @property
    def usage(self) -> str:
        return f"Usage: {self.name} [SESSION_ID | SESSION_INDEX]"

    def __call__(self, *args, **kwargs):
        match args:
            case ("/kill",):
                if self._app.active_session:
                    self._app.active_session.kill()
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
            case ("/kill", id_):
                if session_obj := self._app.find_session(id_=id_, idx=id_):
                    session_obj.kill()
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))(f"Session {id_} not found")
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)

