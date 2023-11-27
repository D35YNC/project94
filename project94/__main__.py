import signal

from project94.project94 import Project94, __version__
from project94.utils.banners import get_banner


def entry():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version",
                        action='version',
                        version=f"%(prog)s v{__version__}")
    parser.add_argument("-c", "--config",
                        type=str,
                        help="load specified config",
                        default="94.conf")
    parser.add_argument("-l", "--listeners",
                        type=str,
                        help="load listeners from string",
                        default=None)
    parser.add_argument("--disable-config",
                        action="store_true",
                        help="disable config save-load",
                        default=False)
    parser.add_argument("--disable-colors",
                        action="store_true",
                        help="disable colored output",
                        default=False)

    a = parser.parse_args()

    if a.listeners:
        a.disable_config = True

    print(f"\n{get_banner()}")

    signal.signal(signal.SIGINT, lambda *args: args)

    app = Project94(a)
    app.main()


if __name__ == '__main__':
    entry()
