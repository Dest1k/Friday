"""The only indexed ordinary namespace entry; no supplied arguments/modules."""
from pathlib import Path
import os
import sys

if __name__=='__main__':
    code=Path('/tmp/friday-metric-work/code')
    if (os.getpid()!=1 or len(sys.argv)!=1 or Path(__file__).resolve()!=code/'ordinary_entry.py'
            or not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode
            or 'hermes_cli' in sys.modules):
        raise SystemExit(2)
    sys.path.insert(0,str(code))
    from hermes_cli.friday_workspace_calc_native_supervisor import main
    raise SystemExit(main())
