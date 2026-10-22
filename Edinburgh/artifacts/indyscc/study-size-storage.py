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

ROOT = Path(__file__).resolve().parent
STUDY = ROOT / 'studies' / ('size-storage-' + time.strftime('%Y%m%dT%H%M%S'))
STUDY.mkdir(parents=True)
RANKS = 64
SIZES = [16, 24, 32, 48, 64]
SECONDS = 15
seed = 20261016
randomiser = random.Random(seed)
schedule = []
for repeat in range(1, 3):
    block = [(size, storage, repeat) for size in SIZES for storage in ['rows', 'contiguous']]
    randomiser.shuffle(block)
    schedule.extend(block)
(STUDY / 'plan.json').write_text(json.dumps({'ranks': RANKS, 'threads': 1,
    'seconds_target': SECONDS, 'seed': seed, 'schedule': schedule}, indent=2))
for command, name in [(['lscpu'], 'lscpu.txt'), (['free', '-h'], 'memory.txt'),
        (['git', '-C', str(ROOT / 'hpcg'), 'rev-parse', 'HEAD'], 'source-commit.txt')]:
    (STUDY / name).write_text(subprocess.check_output(command, text=True))
subprocess.run(['cp', __file__, str(STUDY / 'study.py')], check=True)
rows = []
print(f'STUDY={STUDY}', flush=True)
for size, storage, repeat in schedule:
    run = STUDY / f'n{size}-{storage}-r{repeat}'
    run.mkdir()
    build = ROOT / ('build-mpi-wrapper' if storage == 'rows' else 'build-mpi-contiguous')
    executable = build / 'xhpcg'
    (run / 'binary.sha256').write_text(hashlib.sha256(executable.read_bytes()).hexdigest() + '\n')
    (run / 'hpcg.dat').write_text(f'HPCG benchmark input file\nCIUK size/storage controlled experiment\n{size} {size} {size}\n{SECONDS}\n4 4 4\n')
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', OMP_PLACES='cores', OMP_PROC_BIND='spread',
        OMP_DYNAMIC='false', OMP_WAIT_POLICY='PASSIVE')
    (run / 'environment.json').write_text(json.dumps({k: v for k, v in env.items()
        if k.startswith(('OMP_', 'MPICH_', 'HYDRA_')) or k in ('PATH', 'LD_LIBRARY_PATH')}, indent=2))
    (run / 'load-before.txt').write_text(subprocess.check_output(['uptime'], text=True))
    command = ['/usr/bin/time', '-v', str(ROOT / 'deps/mpich-shm/bin/mpiexec'),
        '-bind-to', 'none', '-n', str(RANKS), 'python3', str(ROOT / 'rank-exec.py'), str(executable)]
    (run / 'command.json').write_text(json.dumps(command))
    start = time.monotonic()
    with (run / 'console.log').open('w') as out, (run / 'timing.log').open('w') as err:
        try:
            status = subprocess.run(command, cwd=run, env=env, stdout=out, stderr=err, timeout=240).returncode
        except subprocess.TimeoutExpired:
            print('TIMEOUT: stopping study rather than overlapping runs', flush=True)
            raise
    wall = time.monotonic() - start
    (run / 'load-after.txt').write_text(subprocess.check_output(['uptime'], text=True))
    logs = list(run.glob('HPCG-Benchmark*.txt'))
    if status != 0 or len(logs) != 1:
        raise RuntimeError(f'Run failed: {run}, exit={status}')
    data = dict(line.rstrip().split('=', 1) for line in logs[0].read_text().splitlines() if '=' in line)
    rating_key = 'Final Summary::HPCG result is VALID with a GFLOP/s rating of'
    if rating_key not in data:
        raise RuntimeError(f'Validation failed: {run}')
    row = {'local_n': size, 'global_n': size * 4, 'storage': storage, 'repeat': repeat,
        'gflops': float(data[rating_key]),
        'timed_seconds': float(data['Benchmark Time Summary::Total']),
        'mg_seconds': float(data['Benchmark Time Summary::MG']),
        'wall_seconds': wall,
        'memory_GB': float(data['Memory Use Information::Total memory used for data (Gbytes)']),
        'reference_iters': data['Iteration Count Information::Reference CG iterations per set'],
        'optimized_iters': data['Iteration Count Information::Optimized CG iterations per set'],
        'residual': data['Reproducibility Information::Scaled residual mean'], 'valid': True}
    rows.append(row)
    with (STUDY / 'results.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)}/20 {storage} local={size} repeat={repeat} GFLOP/s={row["gflops"]:.3f} wall={wall:.1f}s VALID', flush=True)

lines = ['# Size and storage experiment', '',
    '64 MPI ranks x 1 thread; pinned physical cores; fixed compiler flags.',
    'Two repeats, shuffled order; short exploratory runs on a shared node.',
    'No node energy measured: performance rankings are NOT efficiency rankings.', '',
    '| Local n | Global n | Data GB | Rows mean GFLOP/s | Contiguous mean GFLOP/s | Change |',
    '|---:|---:|---:|---:|---:|---:|']
for size in SIZES:
    a = [r['gflops'] for r in rows if r['local_n'] == size and r['storage'] == 'rows']
    b = [r['gflops'] for r in rows if r['local_n'] == size and r['storage'] == 'contiguous']
    memory = next(r['memory_GB'] for r in rows if r['local_n'] == size)
    ma, mb = statistics.mean(a), statistics.mean(b)
    lines.append(f'| {size} | {size*4} | {memory:.3f} | {ma:.3f} | {mb:.3f} | {(mb/ma-1)*100:+.1f}% |')
lines += ['', 'Individual samples and timing breakdowns are in results.csv.',
    'Smallest size may benefit from cache residency; do not infer final-submission eligibility.',
    'Changing size changes work and cache behaviour. It is not a fixed-problem speedup.',
    'Huge-page state was not manipulated; actual allocation page sizes were not verified.']
(STUDY / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines), flush=True)
print('STUDY_COMPLETE', flush=True)
