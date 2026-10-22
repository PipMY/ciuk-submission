#!/usr/bin/env python3
import csv
from pathlib import Path

root = Path(__file__).resolve().parent
rows = []
for path in sorted((root / 'runs').glob('*/HPCG-Benchmark*.txt')):
    data = dict(line.rstrip().split('=', 1) for line in path.read_text().splitlines() if '=' in line)
    def get(key):
        return data.get(key, '')
    rows.append({
        'run': path.parent.name,
        'ranks': get('Machine Summary::Distributed Processes'),
        'threads': get('Machine Summary::Threads per processes'),
        'global_grid': 'x'.join(get(f'Global Problem Dimensions::Global n{axis}') for axis in 'xyz'),
        'memory_GB': get('Memory Use Information::Total memory used for data (Gbytes)'),
        'gflops': get('Final Summary::HPCG result is VALID with a GFLOP/s rating of'),
        'reference_iters_per_set': get('Iteration Count Information::Reference CG iterations per set'),
        'optimized_iters_per_set': get('Iteration Count Information::Optimized CG iterations per set'),
        'timed_seconds': get('Benchmark Time Summary::Total'),
        'mg_seconds': get('Benchmark Time Summary::MG'),
        'residual_mean': get('Reproducibility Information::Scaled residual mean'),
    })
with (root / 'results.csv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f'Wrote {len(rows)} runs to {root / "results.csv"}')
