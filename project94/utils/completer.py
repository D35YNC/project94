import readline

class CustomCompleter:
    def __init__(self, options):
        self.options = sorted(options)
        self.matches = []

    def complete(self, text, state):
        if text in self.options:
            return None

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
