# Durham challenge

Use the revised brief dated **14 October 2026**: task 2 is Grid, not STREAM.
The local copy is `~/Downloads/Durham_Cluster_Challenge_2026-1.pdf`.

## Requirements

- Characterise compute throughput and memory bandwidth on both DINE and DINE2 using `likwid-bench`.
- Build the CPU version of Grid, with no MPI decomposition (`--mpi=1,1,1,1`). Source changes are out of scope.
- Test at least lattice sizes 24 and 32, varying OpenMP thread counts; plot strong scaling for each size.
- Profile selected configurations with `likwid-perfctr` for bandwidth and FLOP/s.
- Compare the two machines and interpret Grid performance using the LIKWID measurements and roofline model.
- Submit a report of no more than two A4 pages; it is assessed alongside the presentation.

## Access and limits

Log in to `login8.cosma.dur.ac.uk`. Submit jobs with account `do022` to
`ciuk-dine` or `ciuk-dine2`. Use exclusive nodes; do not benchmark on login nodes.

Queues close at **16:00 on Friday 23 October 2026**. Jobs submitted before the
cut-off may run afterwards. Maximum job duration is one hour. The brief specifies
no numerical compute budget; verify allocation and queue limits rather than assuming unlimited use.

## Status

No Durham builds or measurements have been collected in this repository yet.
