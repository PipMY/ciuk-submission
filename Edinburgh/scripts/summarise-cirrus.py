#!/usr/bin/env python3
"""Extract HPCG logs/accounting and regenerate short and final weak-scaling results."""
import csv
from pathlib import Path
import statistics
from xml.sax.saxutils import escape

repo = Path(__file__).resolve().parent.parent
root = repo / 'artifacts/cirrus'
results = repo / 'results'
results.mkdir(exist_ok=True)
with (root / 'accounting.psv').open() as f:
    accounting = {row['JobID']: row for row in csv.DictReader(f, delimiter='|')}
rows = []
for log in sorted(root.rglob('HPCG-Benchmark*.txt')):
    parts = log.relative_to(root).parts
    if 'runs' not in parts:
        continue
    job = parts[parts.index('runs') + 1]
    if not job.isdigit():
        continue
    data = dict(line.rstrip().split('=', 1) for line in log.read_text().splitlines() if '=' in line)
    key = 'Final Summary::HPCG result is VALID with a GFLOP/s rating of'
    step = next((part for part in parts if part.split('-')[0].isdigit() and '-' in part), '')
    account_id = job + '.' + step.split('-')[0] if step else job
    account = accounting.get(account_id, {})
    energy = float(account.get('ConsumedEnergyRaw') or 0)
    elapsed = float(account.get('ElapsedRaw') or 0)
    rating = float(data[key]) if key in data else 0
    power = energy / elapsed if energy > 0 and elapsed > 0 else 0
    timed = float(data.get('Benchmark Time Summary::Total', 0))
    local = [data.get(f'Local Domain Dimensions::{axis}', '') for axis in ['nx', 'ny', 'nz']]
    global_shape = [data.get(f'Global Problem Dimensions::Global {axis}', '') for axis in ['nx', 'ny', 'nz']]
    rows.append(dict(job_id=job, step=step, state=account.get('State', ''),
        nodes=accounting.get(job, {}).get('NNodes', ''),
        ranks=int(data.get('Machine Summary::Distributed Processes', 0)),
        threads=data.get('Machine Summary::Threads per processes', ''),
        local_grid='x'.join(local), global_grid='x'.join(global_shape),
        memory_GB=data.get('Memory Use Information::Total memory used for data (Gbytes)', ''),
        valid=key in data, timed_seconds=timed, job_or_step_seconds=elapsed,
        gflops=rating, energy_J=energy,
        energy_scope='step-short-unreliable' if step else 'whole-job', average_W=power,
        gflops_per_W=rating / power if power and not step else '',
        allocated_core_hours=elapsed * float(account.get('AllocCPUS') or 0) / 3600,
        final_duration_eligible=(timed >= 1800 and elapsed >= 1800 and key in data
            and account.get('State') == 'COMPLETED' and not step),
        log=str(log.relative_to(repo))))
if rows:
    with (results / 'hpcg-cirrus.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)

def scaling_report(manifest_name, stem, title, notes):
    manifest = root / 'experiments' / manifest_name
    if not manifest.exists():
        return 0
    jobs = {job: int(nodes) for nodes, job in (line.split() for line in manifest.read_text().splitlines())}
    measured = sorted((dict(r) for r in rows if r['job_id'] in jobs), key=lambda r: jobs[r['job_id']])
    baseline = next((r['gflops'] for r in measured if jobs[r['job_id']] == 1 and r['valid']), 0)
    for row in measured:
        row['weak_scaling_efficiency'] = row['gflops'] / (jobs[row['job_id']] * baseline) if baseline else ''
    if measured:
        with (results / f'{stem}.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=measured[0])
            writer.writeheader()
            writer.writerows(measured)
    md = ['# ' + title, '',
        'Local16^3,288ranks/node,one thread/rank. Work increases with node count.',
        'This is not fixed-workload speedup or equal-work energy-to-solution.',
        'GFLOP/s/W combines timed-phase rating with whole-job mean power.', *notes, '',
        '| Nodes | Job | State | GFLOP/s | Mean W | GFLOP/s/W | Weak efficiency | Job s | Joules | Eligible final duration |',
        '|---:|---:|---|---:|---:|---:|---:|---:|---:|---|']
    by_job = {r['job_id']: r for r in measured}
    def number(value, places=2):
        return f'{value:.{places}f}' if isinstance(value, (int, float)) else 'n/a'
    for job, nodes in sorted(jobs.items(), key=lambda pair: pair[1]):
        row = by_job.get(job)
        if row is None:
            state = accounting.get(job, {}).get('State', 'AWAITING RESULTS')
            md.append(f'| {nodes} | {job} | {state} | | | | | | | No |')
            continue
        weak = number(100 * row['weak_scaling_efficiency'], 1) + '%' if row['weak_scaling_efficiency'] != '' else 'n/a'
        md.append(f'| {nodes} | {job} | {row["state"]} | {row["gflops"]:.2f} | {row["average_W"]:.1f} | {number(row["gflops_per_W"], 3)} | {weak} | {row["job_or_step_seconds"]:.0f} | {row["energy_J"]:.0f} | {"Yes" if row["final_duration_eligible"] else "No"} |')
    (results / ('SCALING.md' if stem == 'scaling-short' else 'FINAL_SCALING.md')).write_text('\n'.join(md) + '\n')
    if not measured:
        return 0
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360">',
        '<rect width="960" height="360" fill="white"/><g font-family="sans-serif" fill="#222">']
    for panel, (field, label) in enumerate([('gflops', 'Performance (GFLOP/s)'), ('gflops_per_W', 'Whole-job GFLOP/s/W'), ('weak_scaling_efficiency', 'Weak-scaling efficiency')]):
        left = 55 + panel * 315
        points_rows = [r for r in measured if isinstance(r[field], (int, float))]
        ymax = max((float(r[field]) for r in points_rows), default=0) * 1.15 or 1
        svg.append(f'<text x="{left}" y="30" font-size="14">{escape(label)}</text>')
        svg.append(f'<path d="M {left} 55 V 280 H {left+235}" fill="none" stroke="#555"/>')
        for tick in range(5):
            value, y = ymax * tick / 4, 280 - tick * 225 / 4
            svg.append(f'<text x="{left-8}" y="{y+4}" font-size="10" text-anchor="end">{value:.2g}</text>')
        points = []
        for row in points_rows:
            n = jobs[row['job_id']]
            x, y = left + (n-1) * 235 / 3, 280 - float(row[field]) * 225 / ymax
            points.append(f'{x},{y}')
            svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#245b8a"/><text x="{x}" y="300" font-size="11" text-anchor="middle">{n}</text>')
        svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#245b8a" stroke-width="2"/>')
        svg.append(f'<text x="{left+105}" y="320" font-size="12">Nodes</text>')
    svg.append(f'<text x="55" y="346" font-size="11">{escape(title)}: consult result table for state, duration eligibility and measurement caveats.</text></g></svg>')
    (results / f'{stem}.svg').write_text('\n'.join(svg))
    return len(measured)

short_count = scaling_report('short-scaling-jobs.txt', 'scaling-short', 'Preliminary short-run weak scaling', [
    'Two-node benchmark VALID, but overall jobTIMEOUT during cleanup.',
    'Short3/4-node jobs cancelled before allocation. Short-run energy is uncertain.'])
final_count = scaling_report('final-scaling-jobs.txt', 'scaling-final', 'Final-run weak scaling', [
    'Only rows marked eligible meet numerical validation, actual timed duration>=1800seconds and COMPLETED state.',
    'Missing rows are pending, running or failed: do not treat them as measurements.'])
for label in ['baseline', 'candidate']:
    values = [r['gflops'] for r in rows if r['step'].endswith(label)]
    if values:
        print(label, 'mean GFLOP/s', statistics.mean(values), 'samples', values)
print(f'Extracted {len(rows)} logs; {short_count} short and {final_count} final-scaling results.')
