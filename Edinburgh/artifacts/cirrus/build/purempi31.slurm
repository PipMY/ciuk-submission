#!/bin/bash
#SBATCH --job-name=hpcg-288x1
#SBATCH --account=tc079-clusdur
#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks=288
#SBATCH --ntasks-per-node=288
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --exclusive
#SBATCH --time=00:45:00
#SBATCH --output=hpcg-%j.out

set -euo pipefail
module load PrgEnv-gnu
cd "$SLURM_SUBMIT_DIR"
run="$SLURM_SUBMIT_DIR/runs/$SLURM_JOB_ID"
mkdir -p "$run"
cp bin/xhpcg "$run/"
cp purempi31.slurm "$run/"
cp ../setup/Make.Cirrus "$run/"
git rev-parse HEAD > "$run/source-commit.txt"
git diff > "$run/source.diff"
scontrol show job "$SLURM_JOB_ID" > "$run/allocation.txt"
cd "$run"
printf '%s\n' 'HPCG benchmark input file' 'CIUK EPCC: one node, pure MPI, 31-minute target' '64 64 64' '1860' '6 6 8' > hpcg.dat
export OMP_NUM_THREADS=1
export OMP_DYNAMIC=false
export OMP_PLACES=cores
export OMP_PROC_BIND=close
export SRUN_CPUS_PER_TASK="$SLURM_CPUS_PER_TASK"
module list > modules.txt 2>&1
lscpu > lscpu.txt
sha256sum xhpcg > binary.sha256
printf 'Job %s starting at %s\n' "$SLURM_JOB_ID" "$(date --iso-8601=seconds)"
printf '288 ranks x 1 thread; local 64^3; global 384x384x512; target 1860 seconds\n'
start=$(date +%s)
srun --hint=nomultithread --distribution=block:block --cpu-bind=cores ./xhpcg
end=$(date +%s)
printf 'srun_elapsed_seconds=%s\n' "$((end-start))" > elapsed.txt
printf 'Finished at %s\n' "$(date --iso-8601=seconds)"
grep -E 'Final Summary::|GFLOP/s Summary::Total' HPCG-Benchmark*.txt
