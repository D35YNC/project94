from .base_command import BaseCommand


class Info(BaseCommand):
    @property
    def aliases(self) -> list[str]:
        return ["i", "info"]

    @property
    def description(self) -> str:
        return "display info about current session"

    @property
    def usage(self) -> str:
        return f"Usage: {self}"

    def __call__(self, *args, **kwargs):
        if self._app.active_session:
            print(f"{'-' * 0x2A}")
            print(f"Hash: {self._app.active_session.session_hash}")
            print(f"From: {self._app.active_session.rhost}:{self._app.active_session.rport}")
            print(f"ASN: {self._app.active_session.asn} {self._app.active_session.asn_org}")
            print(f"Location: {self._app.active_session.country}, {self._app.active_session.region}, "
                  f"{self._app.active_session.city}")
            print(f"TZ: {self._app.active_session.timezone}")
            print(f"{'-' * 0x2A}")
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
