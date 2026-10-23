import sys

from orbe.handoff import try_handoff

if try_handoff(sys.argv):
    sys.exit(0)

from orbe.app import main  # noqa: E402

sys.exit(main())
