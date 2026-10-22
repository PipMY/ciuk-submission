#!/usr/bin/env python3
"""Run on the Cirrus login node: status/accounting and completed-job export only."""
import argparse
import csv
import hashlib
import io
import json
import fcntl
import tempfile
from pathlib import Path
import subprocess
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--export', action='store_true')
args = parser.parse_args()
experiments = Path(__file__).resolve().parent
root = experiments.parent
manifest = experiments / 'final-scaling-jobs.txt'
finals = {job: int(nodes) for nodes, job in (line.split() for line in manifest.read_text().splitlines())}
if len(finals) != 4 or set(finals.values()) != {1, 2, 3, 4} or not all(j.isdigit() for j in finals):
    raise SystemExit('Invalid final-job manifest')
previous = ['559188', '570811', '571937', '571962', '571966', '571972', '571976', '571994', '572008', '572012', '572013', '572014', '572015']
command = ['sacct', '-P', '-j', ','.join(previous + list(finals)),
    '--format=JobID,Account,State,ElapsedRaw,AllocCPUS,NNodes,NodeList,ConsumedEnergyRaw,ExitCode,Start,End']
accounting = subprocess.check_output(command, text=True)
rows = {r['JobID']: r for r in csv.DictReader(io.StringIO(accounting), delimiter='|')}
status = [{**rows.get(job, {'JobID': job, 'State': 'UNKNOWN'}), 'requested_nodes': nodes}
    for job, nodes in finals.items()]
terminal = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY', 'NODE_FAIL', 'BOOT_FAIL', 'PREEMPTED', 'DEADLINE', 'REVOKED'}
def state(row):
    return row.get('State', '').split()[0].rstrip('+')
# A failed prerequisite must not leave downstream jobs pending indefinitely.
if any(state(row) in terminal - {'COMPLETED'} for row in status):
    blocked = [row['JobID'] for row in status if state(row) in {'PENDING', 'CONFIGURING'}]
    if blocked:
        subprocess.run(['scancel', *blocked], check=True)
        print(json.dumps({'cancelled_blocked_jobs': blocked}))
result = {'jobs': status}
if args.export:
    audit = root.parent / 'submission-audit'
    audit.mkdir(exist_ok=True)
    with (audit / 'final-export.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        (audit / 'accounting.psv').write_text(accounting)
        (experiments / 'final-status.json').write_text(json.dumps(status, indent=2) + '\n')
        with tempfile.NamedTemporaryFile(dir=audit, suffix='.tar.gz', delete=False) as temporary:
            archive = Path(temporary.name)
        with tarfile.open(archive, 'w:gz') as tar:
            tar.add(audit / 'accounting.psv', arcname='accounting.psv')
            for name in ['final-scaling-jobs.txt', 'final-status.json', 'scaling-final.slurm', 'remote-export-finals.py']:
                path = experiments / name
                tar.add(path, arcname='experiments/' + name)
            for row in status:
                if state(row) not in terminal:
                    continue
                job = row['JobID']
                for path in [experiments / f'final-{job}.out', experiments / 'runs' / job]:
                    if path.exists():
                        tar.add(path, arcname=str(path.relative_to(root)))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        snapshot = audit / f'final-export-{digest}.tar.gz'
        archive.replace(snapshot)
        result.update(archive=str(snapshot), sha256=digest, bytes=snapshot.stat().st_size)
print(json.dumps(result))
