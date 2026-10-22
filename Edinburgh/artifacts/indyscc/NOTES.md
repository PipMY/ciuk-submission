# Initial HPCG experiments

Host: scc-connect-21-gpu01. Two Intel Xeon Gold 6548Y+ sockets,
32 physical cores each, SMT2, two NUMA domains. Shared system, not reserved.

Build: upstream reference implementation, GCC 13.3, -O3 -DNDEBUG,
OpenMP enabled, MPI disabled. Exact commit in metadata/source-commit.txt.
No source modifications. Reproduce with ./run-omp.sh THREADS 128 10.
OMP_PLACES=cores, OMP_PROC_BIND=spread, OMP_DYNAMIC=false.

Fixed global grid 128^3, reported data footprint 1.49881 GB.
One sample per configuration; these are exploratory, not stable rankings.

| Threads | HPCG GFLOP/s | Raw SpMV GFLOP/s | Raw MG GFLOP/s |
|---:|---:|---:|---:|
| 1 | 1.81801 | 1.91528 | 1.80136 |
| 32 | 2.38094 | 21.4001 | 2.04656 |
| 64 | 2.20729 | 27.4284 | 1.91516 |

All runs numerically VALID; short duration makes them ineligible for submission.
Requested timed duration 10 seconds; actual timed phases 15.8--21.1 seconds,
and total process wall time 60--75 seconds due to setup/calibration/validation.

Source inspection: ComputeSYMGS_ref.cpp performs sequential forward and
backward sweeps with no OpenMP parallel loops. This is part of multigrid,
which scales poorly here even though SpMV scales substantially.
Do not naively add omp parallel for: in-place Gauss-Seidel has dependencies.

Next hypothesis: multiple MPI ranks allow independent local smoother work,
possibly outperforming a heavily threaded single rank. Requires an MPI build.
This does not establish the best Cirrus rank/thread configuration. Larger MPI
rank counts also change the preconditioner and can change iteration counts.

No node energy measurements obtained. No Cirrus jobs submitted for this work.

## MPI decomposition experiment

Installed user-local MPICH 4.2.3, ch3:nemesis (shared-memory transport),
under deps/mpich-shm; no system packages changed. MPI wrapper build is
build-mpi-wrapper (upstream CMake did not propagate MPI include directories
when using plain g++). GCC -O3 -DNDEBUG, no source changes.

All MPI experiments: 64 physical cores, fixed global grid 128x128x128,
explicit process grid, rank-disjoint physical CPU masks in 0--63,
OMP_PLACES=cores, OMP_PROC_BIND=spread, OMP_WAIT_POLICY=PASSIVE.
Each 2-or-more-rank process is confined to one socket. No SMT used.
The original OMP-only series did not explicitly set WAIT_POLICY; use the
MPI series, not cross-series comparisons, for controlled rank/thread conclusions.

Initial 10-second target sweep (actual phase may exceed target):

| Ranks x threads | HPCG GFLOP/s |
|---|---:|
| 1 x 64 | 1.65746 |
| 2 x 32 | 4.3102 |
| 4 x 16 | 8.3325 |
| 8 x 8 | 14.5021 |
| 16 x 4 | 23.8081 |
| 32 x 2 | 33.5115 |
| 64 x 1 | 71.0237 |

Two additional 30-second-target measurements each, interleaved order:
8x8: 15.728, 15.2728; 32x2: 33.6348, 33.621;
64x1: 71.0947, 71.0332 GFLOP/s.
All numerically VALID, reference and optimized iteration counts per set=50.
Total iteration counts differ because faster runs execute more sets; these
are not convergence penalties. Results CSV includes residuals and timings.

Cirrus read-only audit: exact same source commit
114602d458d1034faa52b71e4c15aba9b3a17698 and same smoother SHA256.
Original Cirrus run: 24x12, global128x256x192, data4.5029GB,
93.8506GFLOP/s. It is not directly comparable to Intel GFLOP/s or geometry.

Transferable hypothesis: reference smoother favours more MPI ranks and fewer
threads. Not transferable: exact speedup, optimal rank count, MPI transport
costs, energy or inter-node scaling. Intel has 2 NUMA domains; Cirrus has
8 NUMA domains, 24 CCDs, 288 cores and Cray MPI/Slingshot.

Proposed Cirrus screening, NOT submitted: fixed global192^3, 24x12,
72x4, 288x1, 60-second target. Explicit process grids 2x3x4, 3x4x6,
6x6x8 respectively give local96x64x48,64x48x32,32x32x24.
All dimensions divisible by8 for three coarse levels. Approx5.1GB data,
well above total L3, but only a screening size: do not assume optimal.
One exclusive node; 3 timed minutes alone cost14.4 core-hours plus setup.
Use actual elapsed and whole-job energy; avoid adding overlapping sacct steps.
Do not run until team budget and submission authorisation are settled.
Final challenge runs: exclusive, <=4nodes, >=1800sec and numerical VALID,
retain binaries/scripts/inputs; demonstrate scaling and energy trade-offs.
