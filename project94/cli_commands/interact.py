from .base_command import BaseCommand


class Interact(BaseCommand):
    @property
    def aliases(self) -> list[str]:
        return ["in", "interact"]

    @property
    def description(self) -> str:
        return "start interactive shell"

    @property
    def usage(self) -> str:
        return f"Usage: {self}"

    def __call__(self, *args, **kwargs):
        if self._app.active_session:
            kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))("Enter interactive mode...")
            self._app.active_session.interact()
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
