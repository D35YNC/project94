from .base_command import BaseCommand


class Exit(BaseCommand):
    @property
    def description(self) -> str:
        return "shutdown project94"

    @property
    def long_description(self):
        return "its really just shutdown\n" \
               "Maybe I shouldn't put it in a single module. Because u can delete it xdd.\n" \
               "Have fun =)"

    @property
    def usage(self) -> str:
        return f"Usage: {self.name}"

    def __call__(self, *args, **kwargs):
        self._app.shutdown()
