from .base_command import BaseCommand


class Goto(BaseCommand):
    @property
    def description(self) -> str:
        return "switch to another session"

    @property
    def long_description(self):
        return f"{self.description}\n" \
               "Session can be identified by ID (hash) or index in sessions list\n" \
               "U can view ID and index using \"/show sessions\" command\n" \
               "ID arg can be specified partially. Ex. session ID - sus0GOvm0Za1100ppa\n" \
               "U can goto this session with \"/goto sus0\""

    @property
    def usage(self) -> str:
        return f"Usage: {self.name} SESSION_ID | SESSION_INDEX"

    def __call__(self, *args, **kwargs):
        if len(args) != 2:
            kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
            return
        if new_session := self._app.find_session(id_=args[1], idx=args[1]):
            self._app.active_session = new_session
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("This session does not exist")
