from project94.commands import Command


class ExitCmd(Command):
    def __init__(self, app):
        super().__init__(app, name="exit", description="shutdown project94", long_description="its really just shutdown")

    def main(self, args):
        self.app.shutdown()
