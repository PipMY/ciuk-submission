#!/bin/bash
#SBATCH --job-name=hpcg-n16-60s
#SBATCH --account=tc079-clusdur
#SBATCH --partition=standard
#SBATCH --qos=short
#SBATCH --nodes=1
#SBATCH --ntasks=288
#SBATCH --ntasks-per-node=288
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --exclusive
#SBATCH --time=00:02:00
#SBATCH --output=hpcg-%j.out
set -euo pipefail
module load PrgEnv-gnu
cd "$SLURM_SUBMIT_DIR"
run="$PWD/runs/$SLURM_JOB_ID"
mkdir -p "$run"
cp bin/xhpcg contig16-repeat60.slurm modules-build.txt source-commit.txt build.log "$run/"
cp ../setup/Make.CirrusContig "$run/"
cd "$run"
printf '%s\n' 'HPCG benchmark input file' 'CIUK contiguous arrays screening, not a final submission' '16 16 16' '60' '6 6 8' > hpcg.dat
export OMP_NUM_THREADS=1 OMP_DYNAMIC=false OMP_PLACES=cores OMP_PROC_BIND=close
export SRUN_CPUS_PER_TASK="$SLURM_CPUS_PER_TASK"
module list > modules-runtime.txt 2>&1
lscpu > lscpu.txt
sha256sum xhpcg > binary.sha256
scontrol show job "$SLURM_JOB_ID" > allocation.txt
grep -i huge /proc/meminfo > hugepages-system.txt || true
for f in enabled defrag; do
  if [ -r "/sys/kernel/mm/transparent_hugepage/$f" ]; then
    printf '%s: ' "$f" >> hugepages-system.txt
    cat "/sys/kernel/mm/transparent_hugepage/$f" >> hugepages-system.txt
  fi
done
printf 'Starting job %s at %s\n' "$SLURM_JOB_ID" "$(date --iso-8601=seconds)"
srun --hint=nomultithread --distribution=block:block --cpu-bind=cores ./xhpcg
printf 'Finished at %s\n' "$(date --iso-8601=seconds)"
grep -E 'Final Summary::|GFLOP/s Summary::Total' HPCG-Benchmark*.txt
