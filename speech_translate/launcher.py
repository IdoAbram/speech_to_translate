"""Desktop launch and a noninteractive check for packaged executables."""

import sys

from speech_translate import gui


def main(argv=None) -> int:
    """Start the desktop unless an explicit packaging check was requested."""
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and arguments[0] == "--self-test":
        from speech_translate import diagnostics

        return diagnostics.main(arguments[1:])
    return gui.main()
