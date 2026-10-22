#!/usr/bin/env python3
"""Local background collector for the existing authenticated tmux SSH session.

Never submits compute jobs. Exports finished finals, verifies their transfer,
regenerates analysis and commits/pushes results. Keep this machine and SSH alive.
"""
import argparse
import base64
import datetime
import fcntl
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time
import uuid

parser = argparse.ArgumentParser()
parser.add_argument('--once', action='store_true')
parser.add_argument('--no-push', action='store_true')
parser.add_argument('--interval', type=int, default=60)
args = parser.parse_args()
repo = Path(__file__).resolve().parent.parent
remote_script = '/epccfs/tc079/tc079/tc079mart1/hpcg-work/hpcg/experiments/remote-export-finals.py'
terminal_states = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY', 'NODE_FAIL', 'BOOT_FAIL', 'PREEMPTED', 'DEADLINE', 'REVOKED'}

def state(row):
    return row.get('State', '').split()[0].rstrip('+')

def exchange(command, timeout=120):
    with open('/tmp/ciuk-cirrus-terminal.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        token = uuid.uuid4().hex
        begin, end = '__BEGIN_' + token + '__', '__END_' + token + '__'
        shell = f"printf '\\n{begin}\\n'; {command}; printf '\\n{end}\\n'"
        subprocess.run(['tmux', '-L', 'cirrus-agent', 'send-keys', '-t', 'cirrus', '-l', shell], check=True)
        subprocess.run(['tmux', '-L', 'cirrus-agent', 'send-keys', '-t', 'cirrus', 'Enter'], check=True)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(1)
            tail = subprocess.check_output(['tmux', '-L', 'cirrus-agent', 'capture-pane', '-p', '-J', '-t', 'cirrus', '-S', '-100'], text=True)
            if end in tail.splitlines():
                break
        else:
            raise TimeoutError('SSH command did not complete; no jobs will be resubmitted')
        output = subprocess.check_output(['tmux', '-L', 'cirrus-agent', 'capture-pane', '-p', '-J', '-t', 'cirrus', '-S', '-200000'], text=True).splitlines()
        start = output.index(begin)
        finish = output.index(end, start + 1)
        return '\n'.join(output[start + 1:finish]).strip()

def remote(export=False):
    command = 'python3 ' + shlex.quote(remote_script) + (' --export' if export else '')
    output = exchange(command)
    return json.loads(output.splitlines()[-1])

def update_manifest():
    lines = []
    for path in sorted((repo / 'artifacts').rglob('*')):
        if path.is_file() and path.name in {'xhpcg', 'baseline', 'candidate'}:
            lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + str(path.relative_to(repo)))
    (repo / 'BINARY_SHA256SUMS').write_text('\n'.join(lines) + '\n')

def collect():
    info = remote(export=True)
    raw = exchange('base64 -w 76 ' + shlex.quote(info['archive']))
    data = base64.b64decode(''.join(raw.splitlines()), validate=True)
    if hashlib.sha256(data).hexdigest() != info['sha256']:
        raise RuntimeError('Archive transfer hash mismatch; refusing to extract')
    target = repo / 'artifacts/cirrus'
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or member.issym() or member.islnk():
                raise RuntimeError('Unsafe archive member: ' + member.name)
        archive.extractall(target, filter='data')
    update_manifest()
    subprocess.run(['python3', str(repo / 'scripts/verify-artifacts.py')], check=True)
    subprocess.run(['python3', str(repo / 'scripts/summarise-cirrus.py')], check=True)
    (repo / 'results/final-status.json').write_text(json.dumps(info['jobs'], indent=2) + '\n')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    lines = ['# Final-job status', '', 'Collected: ' + stamp, '',
        '| Nodes | Job | State | Allocated elapsed seconds |', '|---:|---:|---|---:|']
    for row in info['jobs']:
        lines.append(f'| {row["requested_nodes"]} | {row["JobID"]} | {row.get("State", "UNKNOWN")} | {row.get("ElapsedRaw", "")} |')
    lines += ['', 'See FINAL_SCALING.md for actual-duration/numerical eligibility and energy measurements.',
        'No automatic retries. Failed prerequisites block and cancel downstream queued final jobs.']
    (repo / 'results/FINAL_STATUS.md').write_text('\n'.join(lines) + '\n')
    subprocess.run(['git', 'add', 'artifacts/cirrus', 'results', 'BINARY_SHA256SUMS'], cwd=repo, check=True)
    changed = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=repo).returncode
    if changed:
        subprocess.run(['git', 'commit', '--quiet', '-m', 'Collect final HPCG job status and scaling results'], cwd=repo, check=True)
    return info

def push():
    if not args.no_push:
        subprocess.run(['git', '-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential',
            'push', 'origin', 'main'], cwd=repo, check=True, timeout=120)

last = None
push_pending = False
failures = 0
started = time.monotonic()
while True:
    try:
        info = remote()
        signature = [(r['JobID'], r.get('State'), r.get('ConsumedEnergyRaw') if state(r) in terminal_states else '') for r in info['jobs']]
        print(datetime.datetime.now(datetime.timezone.utc).isoformat(), signature, flush=True)
        if signature != last:
            info = collect()
            last = signature
            push_pending = True
        if push_pending:
            push()
            push_pending = False
        failures = 0
        done = all(state(r) in terminal_states for r in info['jobs'])
        energies_ready = all(state(r) != 'COMPLETED' or float(r.get('ConsumedEnergyRaw') or 0) > 0 for r in info['jobs'])
        if args.once or (done and energies_ready):
            print('Collection pass complete' if args.once else 'All final jobs terminal; results collected and pushed', flush=True)
            break
    except Exception as error:
        failures += 1
        print('COLLECTOR ERROR:', repr(error), flush=True)
        if args.once or failures >= 10:
            raise
    if time.monotonic() - started > 24 * 3600:
        raise TimeoutError('Collector stopped after 24 hours; raw runs remain on Cirrus')
    time.sleep(args.interval)
