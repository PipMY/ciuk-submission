#!/usr/bin/env python3
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import time

root = Path(__file__).resolve().parent
study = root / 'studies' / ('kernel-' + time.strftime('%Y%m%dT%H%M%S'))
study.mkdir(parents=True)
configs = {
    'contig-omp': 'build-mpi-contiguous',
    'rows-omp': 'build-mpi-wrapper',
    'contig-noomp': 'build-contig-noomp',
    'rows-noomp': 'build-rows-noomp',
    'contig-fast': 'build-contig-fast',
    'rows-fast': 'build-rows-fast',
}
schedule = []
rng = random.Random(20261017)
for repeat in (1, 2):
    names = list(configs)
    rng.shuffle(names)
    schedule.extend((name, repeat) for name in names)
(study / 'plan.json').write_text(json.dumps(schedule, indent=2))
(study / 'study.py').write_text(Path(__file__).read_text())
rows = []
print(f'STUDY={study}', flush=True)
for name, repeat in schedule:
    run = study / f'{name}-r{repeat}'
    run.mkdir()
    exe = root / configs[name] / 'xhpcg'
    (run / 'binary.sha256').write_text(hashlib.sha256(exe.read_bytes()).hexdigest())
    (run / 'flags.make').write_text((root / configs[name] / 'CMakeFiles/xhpcg.dir/flags.make').read_text())
    (run / 'hpcg.dat').write_text('HPCG benchmark input file\nCIUK kernel screening\n16 16 16\n20\n4 4 4\n')
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', OMP_PLACES='cores', OMP_PROC_BIND='spread',
        OMP_DYNAMIC='false', OMP_WAIT_POLICY='PASSIVE')
    command = ['/usr/bin/time', '-v', str(root / 'deps/mpich-shm/bin/mpiexec'),
        '-bind-to', 'none', '-n', '64', 'python3', str(root / 'rank-exec.py'), str(exe)]
    (run / 'command.json').write_text(json.dumps(command))
    start = time.monotonic()
    with (run / 'console.log').open('w') as out, (run / 'timing.log').open('w') as err:
        status = subprocess.run(command, cwd=run, env=env, stdout=out, stderr=err, timeout=180).returncode
    logs = list(run.glob('HPCG-Benchmark*.txt'))
    if status or len(logs) != 1:
        raise RuntimeError(f'Run failed: {run}')
    data = dict(line.rstrip().split('=', 1) for line in logs[0].read_text().splitlines() if '=' in line)
    key = 'Final Summary::HPCG result is VALID with a GFLOP/s rating of'
    row = {'config': name, 'repeat': repeat, 'valid': key in data,
        'gflops': float(data.get(key, 'nan')), 'wall_seconds': time.monotonic() - start,
        'timed_seconds': data['Benchmark Time Summary::Total'],
        'reference_iters': data['Iteration Count Information::Reference CG iterations per set'],
        'optimized_iters': data['Iteration Count Information::Optimized CG iterations per set']}
    rows.append(row)
    with (study / 'results.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=row)
        writer.writeheader()
        writer.writerows(rows)
    print(row, flush=True)
for name in configs:
    values = [r['gflops'] for r in rows if r['config'] == name and r['valid']]
    print(name, 'mean', statistics.mean(values) if values else 'INVALID', 'samples', values, flush=True)
print('STUDY_COMPLETE', flush=True)
