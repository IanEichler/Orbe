"""Entry point for PyInstaller and for `python run.py`."""
import sys

from orbe.handoff import try_handoff

if __name__ == "__main__":
    if try_handoff(sys.argv):
        sys.exit(0)
    from orbe.app import main
    sys.exit(main())
