#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
root="$PWD"
ranks=${1:?rank count required}
seconds=${2:-10}
case "$ranks" in
1) px=1; py=1; pz=1;;
2) px=2; py=1; pz=1;;
4) px=2; py=2; pz=1;;
8) px=2; py=2; pz=2;;
16) px=4; py=2; pz=2;;
32) px=4; py=4; pz=2;;
64) px=4; py=4; pz=4;;
*) exit 2;;
esac
threads=$((64/ranks))
run="$root/runs/mpi-${ranks}x${threads}-g128-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$run"
cp build-mpi-wrapper/xhpcg rank-exec.py run-mpi.sh "$run/"
printf '%s\n' 'HPCG benchmark input file' 'CIUK fixed global 128^3 experiment' "$((128/px)) $((128/py)) $((128/pz))" "$seconds" "$px $py $pz" > "$run/hpcg.dat"
export OMP_NUM_THREADS="$threads" OMP_PLACES=cores OMP_PROC_BIND=spread OMP_DYNAMIC=false OMP_WAIT_POLICY=PASSIVE
cd "$run"
env | sort > environment.txt
uptime > load-before.txt
/usr/bin/time -v "$root/deps/mpich-shm/bin/mpiexec" -bind-to none -n "$ranks" python3 ./rank-exec.py ./xhpcg > console.log 2> timing.log
uptime > load-after.txt
printf '\n%s\n' "$run"
grep -E 'Final Summary::HPCG result|Machine Summary::|Iteration' HPCG-Benchmark*.txt
