from project94.commands import Command
from project94.utils.printer import Printer


class HelpCmd(Command):
    def __init__(self, app):
        super().__init__(app, name="help",
                         description="display help message",
                         long_description="IM A FUCKING PSYCHO\n"
                                          "         ⠀⠀⠀⠀⠀⠀⣀⣀⣤⣤⣤⣤⣤⣤⣤⣤⣄⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                                          "         ⠀⠀⠀⠀⣠⠞⠁⠀⡀⠄⣒⠨⠭⠭⠭⠉⢀⣒⣒⣚⠋⠙⢛⠶⣄⡀⠀⠀⠀\n"
                                          "         ⠀⠀⠀⢰⠇⠀⠀⢎⠰⡱⣆⣉⣉⡉⠇⠀⠀⠀⠰⠶⠆⠰⢀⠀⠀⢹⡀⠀⠀\n"
                                          "         ⠀⠀⢀⡞⠀⠀⠁⠢⠊⠱⢀⣀⣀⠠⠉⠢⠀⠀⢘⠠⠒⡒⢒⠒⡠⡘⣇⠀⠀\n"
                                          "         ⢀⡴⠟⢒⣒⣂⡒⢇⠀⡀⠻⠿⠿⠂⡪⢤⠃⢤⣆⠰⠀⢴⣿⡦⢀⣘⢌⢳⡀\n"
                                          "         ⡞⠈⣰⠋⠀⣎⡙⠋⠉⠂⠴⠤⠤⠅⠒⠁⠀⠀⢿⡲⠅⣠⣐⡢⡐⠺⢰⠡⡇\n"
                                          "         ⣇⠀⢻⡐⠻⡏⠙⠲⣤⣀⡒⠒⠊⣟⢩⣤⡀⠀⠀⣹⡦⢀⠀⠀⣧⠠⣊⢴⠇\n"
                                          "         ⠸⣎⠶⡀⠀⣿⣷⣀⣷⠈⠉⠿⢶⣏⣀⠀⠀⠰⡾⠁⠀⢀⣰⡿⣾⡏⢀⡏⠀\n"
                                          "         ⠀⠘⢧⡀⠀⢸⣿⣿⣿⣷⣶⣤⣞⡀⠉⠉⡟⠛⢻⠛⠛⢹⠁⣟⣽⡇⢸⠀⠀\n"
                                          "         ⠀⠀⠈⢧⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⠀⠀\n"
                                          "         ⠀⠀⠀⠈⠳⣄⠻⡝⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⠀⠀\n"
                                          "         ⠀⠀⠀⠀⢠⠏⠳⡝⢾⡃⠈⠙⢻⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠘⡇⠀\n"
                                          "         ⠀⠀⠀⠀⣿⠀⠀⠸⡆⠹⣶⣀⡏⠀⠀⠀⡏⠉⠿⡿⠿⡿⢿⣏⣏⡏⠀⡇⠀\n"
                                          "         ⠀⠀⠀⠀⢻⠀⠀⠀⠈⠢⣄⡙⠓⠶⠤⢤⣧⣀⣰⣃⣴⡧⠾⠶⠚⠀⡼⠁⠀\n"
                                          "         ⠀⠀⠀⡴⠙⢖⠒⠢⢄⡀⠀⠉⠓⠲⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠴⠚⠁⠀⠀\n")
        self.parser.add_argument("command", type=str, help="command for extended help", nargs='?', default=None)

    def main(self, args):
        command_name = args.command
        if command_name:
            if cmd := self.app.commands.get(command_name):
                Printer.info(f"Help: {cmd.name}")
                print(cmd.help)
                # print(cmd.description)
                # if cmd.long_description:
                #     print(cmd.long_description)
                # if cmd.has_subcommands:
                #     for subcmd in cmd.subcommands:
                #         print(f"{subcmd.name:<10} - {subcmd.description}")
                #         if subcmd.long_description:
                #             print(subcmd.long_description)
                # print("Usage:")
                # print(cmd.usage)
                # if cmd.has_subcommands:
                #     for subcmd in cmd.subcommands:
                #         print(subcmd.usage)
            else:
                Printer.warning(f"Command \"{command_name}\" not found")
        else:
            for cmd in self.app.commands:
                print(f"{cmd:<20}{self.app.commands[cmd].description}")
