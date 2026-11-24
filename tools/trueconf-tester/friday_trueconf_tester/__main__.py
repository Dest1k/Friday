import sys
from importlib.util import find_spec


def _main():
    if find_spec(f"{__package__}._stock_observer") is None:
        print('{"state":"REFUSED","reason":"tester_observer_not_assembled"}', file=sys.stderr)
        return 2
    from .entrypoint import main

    return main()


raise SystemExit(_main())
