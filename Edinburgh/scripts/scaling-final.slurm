#!/bin/bash
#SBATCH --job-name=hpcg-final
#SBATCH --account=tc079-clusdur
#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=288
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --exclusive
#SBATCH --time=00:45:00
#SBATCH --output=final-%j.out
set -euo pipefail
# Explicit user approval is required before submission.
[[ "${HPCG_FINAL_APPROVED:-NO}" == YES ]] || { echo "Final run not approved" >&2; exit 1; }
module load PrgEnv-gnu
root=$(realpath "$SLURM_SUBMIT_DIR/..")
nodes="$SLURM_JOB_NUM_NODES"
[[ "$SLURM_NTASKS" -eq $((288*nodes)) ]]
case "$nodes" in
    1) grid='6 6 8';;
    2) grid='8 8 9';;
    3) grid='8 9 12';;
    4) grid='8 12 12';;
    *) exit 2;;
esac
run="$SLURM_SUBMIT_DIR/runs/$SLURM_JOB_ID"
mkdir -p "$run"
cp "$root/build-rows-fast/bin/xhpcg" "$run/"
cp "$SLURM_SUBMIT_DIR/scaling-final.slurm" "$run/"
cp "$root/setup/Make.CirrusRowsFast" "$run/"
cp "$root/build-rows-fast/build.log" "$root/build-rows-fast/modules-build.txt" "$run/"
git -C "$root" rev-parse HEAD > "$run/source-commit.txt"
cd "$run"
printf '%s\n' 'HPCG benchmark input file' 'CIUK final weak scaling, 32-minute target' '16 16 16' '1920' "$grid" > hpcg.dat
export OMP_NUM_THREADS=1 OMP_DYNAMIC=false OMP_PLACES=cores OMP_PROC_BIND=close
export SRUN_CPUS_PER_TASK="$SLURM_CPUS_PER_TASK"
module list > modules-runtime.txt 2>&1
lscpu > lscpu.txt
ldd xhpcg > libraries.txt
printf 'OMP_NUM_THREADS=%s\nOMP_PLACES=%s\nOMP_PROC_BIND=%s\n' "$OMP_NUM_THREADS" "$OMP_PLACES" "$OMP_PROC_BIND" > placement.txt
scontrol show job "$SLURM_JOB_ID" > allocation.txt
scontrol show hostnames "$SLURM_JOB_NODELIST" > nodes.txt
sha256sum xhpcg > binary.sha256
printf 'Starting %s nodes at %s\n' "$nodes" "$(date --iso-8601=seconds)"
srun --hint=nomultithread --distribution=block:block --cpu-bind=cores ./xhpcg
printf 'Finished at %s\n' "$(date --iso-8601=seconds)"
grep -E 'Final Summary::|GFLOP/s Summary::Total' HPCG-Benchmark*.txt
python3 - <<'PY'
from pathlib import Path
logs = list(Path('.').glob('HPCG-Benchmark*.txt'))
if len(logs) != 1:
    raise SystemExit('Expected exactly one HPCG result')
data = dict(line.rstrip().split('=', 1) for line in logs[0].read_text().splitlines() if '=' in line)
if 'Final Summary::HPCG result is VALID with a GFLOP/s rating of' not in data:
    raise SystemExit('HPCG validation failed')
if float(data['Benchmark Time Summary::Total']) < 1800:
    raise SystemExit('Actual timed phase below 30 minutes')
print('Final numerical validation and actual duration checks passed')
PY
