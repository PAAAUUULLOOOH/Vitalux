#!/usr/bin/env python3
"""Create or verify the current launcher's private restart handoff."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux.restart_protocol import initialize,requested

if __name__=='__main__':
    action,*arguments=sys.argv[1:]
    try:
        if action=='init':print(initialize(*arguments))
        elif action=='check':raise SystemExit(0 if requested(*arguments) else 1)
        else:raise ValueError('Unknown restart operation')
    except (OSError,RuntimeError,ValueError) as error:
        print('Vitalux restart handoff: '+str(error),file=sys.stderr)
        raise SystemExit(1)
