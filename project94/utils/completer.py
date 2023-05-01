import readline


def _make_options(commands) -> list[str]:
    r = []
    for cmd_name in commands:
        if commands[cmd_name].subcommands:
            for subcmd in commands[cmd_name].subcommands:
                r.append(f"{cmd_name} {subcmd.name} ")
        r.append(f"{cmd_name} ")
    return r


class CommandsCompleter:
    def __init__(self, options):
        self.options = sorted(_make_options(options))
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            if text:
                self.matches = [line for line in self.options if line and line.startswith(text)]
            else:
                self.matches = self.options

        if 0 <= state < len(self.options):
            return self.matches[state]

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
