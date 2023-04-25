import requests

from .module_base import *
from ..utils import networking
from ..utils import Printer


class SessionExtendedInfo(Module):
    def on_session_ready(self, *args, **kwargs):
        session = args[0]
        self.__detect_os(session)

        r = requests.get("https://ifconfig.co/json", params={"ip": session.rhost}, timeout=10)
        api_info = r.json()

        session.extended_info["ASN"] = f'{api_info.get("asn", "Unknown")} {api_info.get("asn_org", "Unknown")}'
        session.extended_info["Location"] = f'{api_info.get("country", "Unknown")} {api_info.get("region_name", "Unknown")} {api_info.get("city", "Unknown")}'
        session.extended_info["TZ"] = api_info.get("time_zone", "Unknown")

    @command(name="detect", description="detecting some info in session")
    @subcommands("os", "software")
    def detect(self, *args, **kwargs):
        app = kwargs.get("app")
        match args:
            case ("os",):
                if app.active_session:
                    if os := app.active_session.extended_info.get("OS"):
                        Printer.info(os)
                    else:
                        self.__detect_os(app.active_session)
                        Printer.info(app.active_session.extended_info.get("OS"))
                else:
                    kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
            case ("os", sesion_id):
                session = app.get_session(id_=sesion_id, idx=sesion_id)
                self.__detect_os(session)
                Printer.info(session.extended_info.get("OS"))
            case ("software", *arg):
                pass
            case _:
                kwargs.get("print_error_callback", lambda x: print(f"[!!!] {x}"))(kwargs.get("command").usage)

    def __detect_os(self, session):
        cmd = 'cat /etc/*release | grep PRETTY_NAME | sed "s/PRETTY_NAME=//"\n\nsysteminfo\n'
        res = session.send_command_and_recv(cmd)
        session.extended_info["OS"] = res.strip()

    def __detect_software(self, session, name: str) -> bool:
        token = networking.random_token()
        if "windows" in session.extended_info.get("OS", "x").lower():
            cmd = f"powershell -Command \"if (Get-Command '{name}' -ErrorAction SilentlyContinue){{Write-Output '{token}'}}\"\n"
        else:
            cmd = f"/bin/bash -c \"if ( hash {name} 2>/dev/null ); then echo '{token}'; else echo ''; fi\"\n"

        res = session.send_command_and_recv(cmd)
        return token in res
