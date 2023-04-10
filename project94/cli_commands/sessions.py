from .base_command import BaseCommand


class Sessions(BaseCommand):
    @property
    def aliases(self) -> list[str]:
        return ["s", "sessions"]

    @property
    def description(self) -> str:
        return "display sessions list"

    @property
    def usage(self) -> str:
        return f"Usage: {self}"

    def __call__(self, *args, **kwargs):
        if len(self._app.sessions) == 0:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("No online sessions")
        else:
            kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))("Listing online sessions...")
            kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))(f"{len(self._app.sessions)} sessions online")
            for id_ in self._app.sessions:
                print(f"{'-' * 0x2A}")
                print(f"Index: {list(self._app.sessions.keys()).index(id_)}")
                print(f"Hash: {self._app.sessions[id_].session_hash}")
                print(f"From: {self._app.sessions[id_].rhost}:{self._app.sessions[id_].rport}")
                print(f"ASN: {self._app.sessions[id_].asn} {self._app.sessions[id_].asn_org}")
                print(f"Location: {self._app.sessions[id_].country}, {self._app.sessions[id_].region}, "
                      f"{self._app.sessions[id_].city}")
            print(f"{'-' * 0x2A}")
