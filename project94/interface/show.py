from .base_command import BaseCommand


class Show(BaseCommand):
    @property
    def description(self):
        return "displays information of specified type"

    @property
    def long_description(self) -> str:
        return f"{self.description}\n" \
               "sessions - shows list of sessions and information about them\n" \
               "info     - shows information about active session"

    @property
    def usage(self) -> str:
        return f"Usage: {self.name} {{sessions, info}}"

    @property
    def subcommands(self) -> list[str]:
        return ["info", "sessions"]

    def __call__(self, *args, **kwargs):
        match args:
            case ("/show", "info",):
                if self._app.active_session:
                    print(f"Hash: {self._app.active_session.session_hash}")
                    print(f"From: {self._app.active_session.rhost}:{self._app.active_session.rport}")
                    print(f"ASN: {self._app.active_session.asn} {self._app.active_session.asn_org}")
                    print(f"Location: {self._app.active_session.country}, {self._app.active_session.region}, "
                          f"{self._app.active_session.city}")
                    print(f"TZ: {self._app.active_session.timezone}")
                    print(f"Encoding: {self._app.active_session.encoding}")
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")

            case ("/show", "sessions",):
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
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(self.usage)
