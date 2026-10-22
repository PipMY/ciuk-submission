#!/usr/bin/env python3
"""Lightweight login-node fallback: retain accounting/archives without local SSH.

No compute submissions or retries. This watcher does not hold GitHub credentials.
"""
import datetime
import fcntl
import json
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parent
lock = (root / 'final-watcher.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
terminal = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY', 'NODE_FAIL', 'BOOT_FAIL', 'PREEMPTED', 'DEADLINE', 'REVOKED'}
last = None
started = time.monotonic()
while time.monotonic() - started < 24 * 3600:
    try:
        output = subprocess.check_output(['python3', str(root / 'remote-export-finals.py')], text=True, timeout=90)
        info = json.loads(output.splitlines()[-1])
        def state(row):
            return row.get('State', '').split()[0].rstrip('+')
        signature = [(r['JobID'], r.get('State'), r.get('ConsumedEnergyRaw') if state(r) in terminal else '') for r in info['jobs']]
        if signature != last:
            output = subprocess.check_output(['python3', str(root / 'remote-export-finals.py'), '--export'], text=True, timeout=90)
            info = json.loads(output.splitlines()[-1])
            (root / 'overnight-status.json').write_text(json.dumps(info, indent=2) + '\n')
            print(datetime.datetime.now(datetime.timezone.utc).isoformat(), signature, info['archive'], flush=True)
            last = signature
        if all(state(r) in terminal for r in info['jobs']) and all(
                state(r) != 'COMPLETED' or float(r.get('ConsumedEnergyRaw') or 0) > 0 for r in info['jobs']):
            print('All final jobs terminal; accounting and archive retained on Cirrus', flush=True)
            break
    except Exception as error:
        print('WATCHER ERROR:', repr(error), flush=True)
    time.sleep(60)
else:
    print('Watcher24-hour limit reached; no compute jobs were cancelled or resubmitted', flush=True)
