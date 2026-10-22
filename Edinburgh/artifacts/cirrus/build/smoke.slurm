#!/bin/bash
#SBATCH --job-name=hpcg-smoke
#SBATCH --account=tc079-clusdur
#SBATCH --partition=standard
#SBATCH --qos=short
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --cpus-per-task=12
#SBATCH --hint=nomultithread
#SBATCH --exclusive
#SBATCH --time=00:10:00
#SBATCH --output=hpcg-%j.out

   set -euo pipefail
   module load PrgEnv-gnu

   cd "$SLURM_SUBMIT_DIR"
   run="$SLURM_SUBMIT_DIR/runs/$SLURM_JOB_ID"
   mkdir -p "$run"
   cp bin/xhpcg "$run/"
   cp smoke.slurm "$run/"
   cd "$run"

   printf '%s\n' \
       'HPCG benchmark input file' \
       'Sandia National Laboratories; University of Tennessee, Knoxville' \
       '64 64 64' \
       '60' > hpcg.dat

   export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
   export OMP_PLACES=cores
   export OMP_PROC_BIND=close
   export SRUN_CPUS_PER_TASK="$SLURM_CPUS_PER_TASK"

   module list > modules.txt 2>&1

   echo "Starting HPCG on $(hostname) at $(date)"

   srun --hint=nomultithread \
        --distribution=block:block \
        --cpu-bind=cores ./xhpcg

   echo "Finished at $(date)"
