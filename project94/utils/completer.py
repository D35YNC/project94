import readline

from ..modules.module_base import Command


class CommandsCompleter:
    def __init__(self, commands):
        self.__tree = CommandsCompleter.__make_options(commands)
        self.__matches = []
        self.__listeners = {}

    def traverse(self, tokens, tree):
        if tree is None or len(tokens) == 0:
            return []
        if len(tokens) == 1:
            return [x + ' ' for x in tree if x.startswith(tokens[0])]
        else:
            if tokens[0] in tree.keys():
                trase = self.traverse(tokens[1:], tree[tokens[0]])
                return [f"{tokens[0]} {x}" for x in trase]
        return []

    def complete(self, text, state):
        tokens = readline.get_line_buffer().split(' ')
        self.__matches = self.traverse(tokens, self.__tree)
        return self.__matches[state]

    def display_matches(self, substitution, matches, longest_match_length):
        line_buffer = readline.get_line_buffer()
        print()

        tpl = "{:<" + str(int(max(map(len, matches)) * 1.2)) + "}"
        buffer = ""
        for match in matches:
            match = tpl.format(match)
            if len(buffer + match) > 80:
                print(buffer)
                buffer = ""
            buffer += match
        if buffer:
            print(buffer)
        print(f">> {line_buffer}", end='', flush=True)

    def update_listeners(self, listeners: dict[str, bool]):
        self.__listeners = listeners

    @staticmethod
    def __make_options(commands: dict[str, Command]) -> dict[str, dict]:
        res = {}
        for command_name in commands:
            if commands[command_name].subcommands:
                res[command_name] = {}
                for subcommand in commands[command_name].subcommands:
                    res[command_name][subcommand.name] = {}
                    res[command_name].update(CommandsCompleter.__make_options({subcommand.name: subcommand}))
            else:
                res[command_name] = None
        return res
