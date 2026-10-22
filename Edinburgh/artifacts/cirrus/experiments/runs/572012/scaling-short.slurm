#!/bin/bash
#SBATCH --job-name=hpcg-scaling
#SBATCH --account=tc079-clusdur
#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=288
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --exclusive
#SBATCH --time=00:01:00
#SBATCH --output=scaling-%j.out
set -euo pipefail
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
cp "$SLURM_SUBMIT_DIR/scaling-short.slurm" "$run/"
cp "$root/setup/Make.CirrusRowsFast" "$run/"
cp "$root/build-rows-fast/build.log" "$root/build-rows-fast/modules-build.txt" "$run/"
git -C "$root" rev-parse HEAD > "$run/source-commit.txt"
cd "$run"
printf '%s\n' 'HPCG benchmark input file' 'CIUK short weak scaling, not final' '16 16 16' '20' "$grid" > hpcg.dat
export OMP_NUM_THREADS=1 OMP_DYNAMIC=false OMP_PLACES=cores OMP_PROC_BIND=close
export SRUN_CPUS_PER_TASK="$SLURM_CPUS_PER_TASK"
module list > modules-runtime.txt 2>&1
scontrol show job "$SLURM_JOB_ID" > allocation.txt
scontrol show hostnames "$SLURM_JOB_NODELIST" > nodes.txt
sha256sum xhpcg > binary.sha256
printf 'Starting %s nodes at %s\n' "$nodes" "$(date --iso-8601=seconds)"
srun --hint=nomultithread --distribution=block:block --cpu-bind=cores ./xhpcg
printf 'Finished at %s\n' "$(date --iso-8601=seconds)"
grep -E 'Final Summary::|GFLOP/s Summary::Total' HPCG-Benchmark*.txt
