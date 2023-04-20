import abc


class BaseCommand(abc.ABC):
    def __init__(self, app):
        self._app = app

    @property
    def name(self) -> str:
        """
        :return: Command base name
        """
        return f"/{self.__class__.__name__.lower()}"

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """
        :return: One line command description
        """
        raise NotImplementedError()

    @property
    def long_description(self) -> str:
        """
        :return: Multiline command description
        """
        return self.description

    @property
    @abc.abstractmethod
    def usage(self) -> str:
        """
        :return: Usage string
        """
        raise NotImplementedError()

    @property
    def subcommands(self) -> list[str]:
        """
        :return: List of subcommands
        """
        return []

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError()
