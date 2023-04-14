from .base_command import BaseCommand


class Exit(BaseCommand):
    @property
    def description(self) -> str:
        return "shutdown project94"

    @property
    def usage(self) -> str:
        return f"Usage: {self}"

    def __call__(self, *args, **kwargs):
        self._app.shutdown()
