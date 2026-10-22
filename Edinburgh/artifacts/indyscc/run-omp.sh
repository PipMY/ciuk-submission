#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
threads=${1:?thread count required}
size=${2:-128}
seconds=${3:-10}
run="$PWD/runs/omp-${threads}-n${size}-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$run"
cp build-omp/xhpcg "$run/"
cp run-omp.sh "$run/"
printf '%s\n' 'HPCG benchmark input file' 'CIUK development test' "$size $size $size" "$seconds" > "$run/hpcg.dat"
export OMP_NUM_THREADS="$threads" OMP_PLACES=cores OMP_PROC_BIND=spread OMP_DYNAMIC=false
export OMP_DISPLAY_ENV=VERBOSE
cd "$run"
env | sort > environment.txt
/usr/bin/time -v ./xhpcg > console.log 2> timing.log
printf '\n%s\n' "$run"
grep -E 'Final Summary::|Machine Summary::|Memory Use Information::Total' HPCG-Benchmark*.txt
