#!/bin/bash
#SBATCH --job-name=hpcg-compare
#SBATCH --account=tc079-clusdur
#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks=288
#SBATCH --ntasks-per-node=288
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --exclusive
#SBATCH --time=00:02:00
#SBATCH --output=compare-%j.out
set -euo pipefail
module load PrgEnv-gnu
root=$(realpath "$SLURM_SUBMIT_DIR/..")
run="$SLURM_SUBMIT_DIR/runs/$SLURM_JOB_ID"
mkdir -p "$run"
cp "$root/build-contig/bin/xhpcg" "$run/baseline"
cp "$root/build-rows-fast/bin/xhpcg" "$run/candidate"
cp "$SLURM_SUBMIT_DIR/compare-builds.slurm" "$run/"
cp "$root/setup/Make.CirrusContig" "$root/setup/Make.CirrusRowsFast" "$run/"
git -C "$root" rev-parse HEAD > "$run/source-commit.txt"
module list > "$run/modules.txt" 2>&1
scontrol show job "$SLURM_JOB_ID" > "$run/allocation.txt"
sha256sum "$run/baseline" "$run/candidate" > "$run/binaries.sha256"
export OMP_NUM_THREADS=1 OMP_DYNAMIC=false OMP_PLACES=cores OMP_PROC_BIND=close
export SRUN_CPUS_PER_TASK="$SLURM_CPUS_PER_TASK"
step=0
for label in baseline candidate candidate baseline; do
    stepdir="$run/$step-$label"
    mkdir -p "$stepdir"
    cd "$stepdir"
    printf '%s\n' 'HPCG benchmark input file' 'CIUK controlled ABBA comparison' '16 16 16' '10' '6 6 8' > hpcg.dat
    printf 'Starting step %s %s at %s\n' "$step" "$label" "$(date --iso-8601=seconds)"
    srun --hint=nomultithread --distribution=block:block --cpu-bind=cores "$run/$label" > console.log 2>&1
    grep -E 'Final Summary::HPCG result|Final Summary::Results are valid' HPCG-Benchmark*.txt
    step=$((step+1))
done
printf 'Completed ABBA at %s\n' "$(date --iso-8601=seconds)"
