# EPCC / CIUK submission checklist

Source: Downloads/EPCC_Cluster_Challenge_2026.pdf. All three downloaded copies are identical.

## Required deliverables, for both HPL and HPCG

- [ ] Compiled binaries used in experiments.
- [ ] Reproducible run scripts and input files.
- [ ] Results tables/plots: runtime, GFLOP/s, joules and GFLOP/s/W.
- [ ] Scaling analysis across 1 to 4 nodes, explaining energy/performance trade-offs.
- [ ] Presentation slides explaining optimisation strategies, best results and lessons learned.
- [ ] Presentation timing: the brief lists 5–7 minutes under each benchmark.
- [ ] HPCG/HPL comparison: memory/communication-bound versus compute-bound behaviour.

## Mandatory run conditions

- Exclusive nodes: #SBATCH --exclusive.
- Maximum four nodes.
- HPCG final submitted jobs: at least 30 minutes; final logs report VALID.
- HPL: no minimum runtime stated in this brief.
- No minimum memory fraction or grid size is stated in this brief.
- Keep short exploratory tests separate from final eligible results.

## Status: HPCG

Available on Cirrus under:
/epccfs/tc079/tc079/tc079mart1/hpcg-work/hpcg

- [x] Reference source identified: 114602d458d1034faa52b71e4c15aba9b3a17698.
- [x] Three build variants retained: build, build-contig, build-rows-fast.
- [x] Per-run binaries, inputs and scripts retained.
- [x] Newer runs include build logs, compiler/runtime modules, hardware information and binary hashes.
- [x] Raw result logs and validation retained.
- [x] Scheduler accounting exported to ../submission-audit/job-accounting.psv.
- [x] Free-node MPI/OpenMP, size/storage and kernel-build experiments retained on IndySCC.
- [ ] Package exact build commands/environment for every retained binary; audit completeness of initial build.
- [x] Controlled same-allocation ABBA comparison confirms an8.01% throughput improvement for rows-fast.
- [ ] Controlled efficiency confirmation: short step energies were inconsistent; cannot infer a firm efficiency gain.
- [ ] Final >=30-minute VALID HPCG measurements at all four node counts. Explicitly approved and queued as572034/572035/572036/572037; completion/validation still pending.
- [ ] Complete1/2/3/4-node scaling evidence, as requested by the team. Short1node completed; short2nodes produced VALID output but jobTIMEOUT during cleanup;3/4nodes cancelled before starting. See results/SCALING.md.
- [ ] Combined machine-readable results with consistent energy boundaries and uncertainty notes.
- [ ] Tables and plots.

Leading candidate, not yet confirmed optimal:
- build-rows-fast/runs/571994
- GNU via CC; -O3 -ffast-math -funroll-loops; HPCG_NO_OPENMP; non-contiguous row storage.
- One exclusive node, 288 MPI ranks, one thread/rank, physical cores only, block:block placement.
- Local grid16x16x16; process grid6x6x8; global96x96x128.
- 60-second target; actual timed phase57.6239seconds; job elapsed72seconds.
- VALID, 546.556GFLOP/s, job energy60525J.
- Whole-job average power840.625W; estimated efficiency0.65018GFLOP/s/W.
- Not final-duration eligible. Cross-node comparisons have not isolated causal improvements.

## Status: HPL

Not inventoried during this work. Do not infer that teammates have not started it.
- [ ] Locate team HPL binaries/scripts/results and establish ownership.
- [ ] Build/compiler and BLAS/library metadata.
- [ ] HPL.dat problem size, block size, process grid and algorithm settings.
- [ ] Successful correctness/residual output.
- [ ] 1-to-4-node performance/energy measurements and analysis.
- [ ] Reproducible scripts, inputs and final binary.

## Data to retain per measured run

Benchmark/version; job ID; node count/hostnames; date; compiler/modules;
binary hash; build flags/options; exact input and command;
MPI ranks/threads and binding; local/global dimensions or HPL N/NB/P/Q;
requested duration and actual benchmark/job durations;
validation; GFLOP/s; raw energy; accounting boundary;
average power; GFLOP/s/W; allocated core-hours; repeat number.

Calculation for our current whole-job convention:
  power_W = job_energy_J / job_elapsed_seconds
  efficiency = HPCG_rating_GFLOPs / power_W
This combines timed-phase performance with whole-job mean power. It is not a
measurement restricted to the timed phase. Do not add overlapping sacct step energies.

## Experiments and evidence

- [x] MPI/OpenMP behaviour and reference smoother source inspection.
- [x] Problem-size and contiguous-storage tests, two repeats each, on IndySCC.
- [x] Build candidate screening, two repeats each, on IndySCC.
- [x] Cirrus short-run screening and one longer repeat.
- [ ] Clearly distinguish observations, hypotheses and transferred assumptions.
- [ ] Do not claim huge pages improved performance: actual application page sizes were not verified.
- [ ] Do not claim 0.904GFLOP/s/W as a stable result; longer repeat gave0.544 with that build.
- [ ] Do not use Intel-node performance as Cirrus energy/scaling evidence.
- [ ] Report changing problem sizes honestly; these are not fixed-workload speedups.

## Allocation and hand-in logistics

- [ ] Confirm total/remaining team budget in SAFE (not exposed by Slurm association limits).
- [x] User explicitly approved final1/2/3/4-node submissions; expected1536core-hours plus setup. Safety-limit ceiling2160core-hours. No automatic retries.
- [ ] Confirm deadline, upload location, archive layout and presentation arrangement.
- [ ] Clarify HPCG scoring formula and any supplementary problem-size rules.
- [ ] Clarify whether node counts1,2,4 suffice for scaling requirements.
- [x] Back up existing artefacts off Cirrus and commit them in a private GitHub repository.
- [ ] Collect final-run artefacts and produce the final submission archive after all results are checked.
- [ ] Test the reproduction instructions from a clean build directory.

Inspected Cirrus jobs now include559188,570811,571937,571962,571966,571972,571976,571994,
572008,572012,572013,572014,572015. Main-job allocated-core-time totals56.24core-hours,
including cancelled570811;572014/572015 were cancelled before allocation.
This is not the full team's usage or SAFE charge total. The latest tuning batch used19.2core-hours.
The prepared32-minute-target HPCG series at1,2,3,4nodes would cost1536core-hours
before setup, so do not start final runs without checking the team budget.
