import readline

from project94.commands import Command


class CommandsCompleter:
    def __init__(self, commands):
        self.__tree = CommandsCompleter.__make_tree(commands)
        # self.__matches = []

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
        # self.__matches = self.traverse(tokens, self.__tree)
        # return self.__matches[state]
        return self.traverse(tokens, self.__tree)[state]

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

    @staticmethod
    def __make_tree(commands: dict[str, Command]) -> dict[str, dict]:
        res = {}
        for cmd_name, cmd in commands.items():
            if cmd.has_subcommands:
                res[cmd_name] = {}
                for subcmd_name, subcmd in cmd.subcommands.items():
                    res[cmd_name][subcmd_name] = {}
                    res[cmd_name].update(CommandsCompleter.__make_tree({subcmd_name: cmd.subcommands[subcmd_name]}))
            else:
                res[cmd_name] = None
        return res
