import requests

from .module_base import *
from ..utils import Printer
from ..utils import networking


class SessionExtendedInfo(Module):
    detect = Command(name="detect", description="detecting some info in session")

    def on_session_ready(self, *args, **kwargs):
        session = args[0]
        self.__detect_os(session)

        r = requests.get("https://ifconfig.co/json", params={"ip": session.rhost}, timeout=10)
        api_info = r.json()

        session.extended_info["ASN"] = f'{api_info.get("asn", "Unknown")} {api_info.get("asn_org", "Unknown")}'
        session.extended_info["Location"] = f'{api_info.get("country", "Unknown")} {api_info.get("region_name", "Unknown")} {api_info.get("city", "Unknown")}'
        session.extended_info["TZ"] = api_info.get("time_zone", "Unknown")

    @detect.subcommand(name="os", description="automatic detecting os")
    def detect_os(self, session_id: str = ""):
        if session_id and (session := self.app.get_session(id_=session_id, idx=session_id)):
            self.__detect_os(session)
            Printer.info(session.extended_info.get("OS"))
        else:
            Printer.warning(f"Cant find session {session_id}")
            return

        if session := self.app.active_session:
            if os := session.extended_info.get("OS"):
                Printer.info(os)
            else:
                self.__detect_os(session)
                Printer.info(session.extended_info.get("OS"))
        else:
            Printer.warning("Current session is FUCKING DEAD")

    @detect.subcommand(name="software", description="automatic detecting software in PATH")
    def detect_software(self, soft: str):
        if session := self.app.active_session:
            r = self.__detect_software(session, soft)
            if r:
                Printer.success(f"{soft} is present")
            else:
                Printer.warning(f"{soft} is missing")
        else:
            Printer.warning("Current session is FUCKING DEAD")

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
