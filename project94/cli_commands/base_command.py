import abc


class BaseCommand(abc.ABC):
    def __init__(self, app):
        self._app = app

    @property
    @abc.abstractmethod
    def aliases(self) -> list[str]:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def usage(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def __str__(self) -> str:
        return f"/{self.__class__.__name__.lower()}"


