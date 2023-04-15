from .base_command import BaseCommand


class Interact(BaseCommand):
    @property
    def description(self) -> str:
        return "start interactive shell"

    @property
    def long_description(self):
        return f"{self.description}\n" \
               f"DO NOT USE KEYBOARD SHORTCUTS =)"

    @property
    def usage(self) -> str:
        return f"Usage: {self.name}"

    def __call__(self, *args, **kwargs):
        if self._app.active_session:
            kwargs.get("print_info_callback", lambda x: print(f"[*] {x}"))("Enter interactive mode...")
            self._app.active_session.interactive = True
        else:
            kwargs.get("print_warning_callback", lambda x: print(f"[!] {x}"))("Current session is FUCKING DEAD")
