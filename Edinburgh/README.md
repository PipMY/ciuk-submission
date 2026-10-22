# Edinburgh / EPCC benchmark experiments

Part of https://github.com/PipMY/ciuk-submission. Contains HPCG source,
binaries, inputs, raw results, accounting, experiment scripts and scaling analysis.
HPL is not yet collected here. Run commands below from this `Edinburgh/` directory.

**Final1/2/3/4-node jobs were explicitly approved and queued sequentially:**
572034,572035,572036,572037. At the user's request, execution priority was changed
to **1node -> 4nodes -> 2nodes -> 3nodes**, without interrupting the active1-node job.
See `artifacts/cirrus/experiments/final-execution-order.txt`, `results/FINAL_STATUS.md` and
`results/FINAL_SCALING.md` for collected status, measurements and eligibility.
Do not infer completion from submission. Earlier job570811 was cancelled and
is retained as a cancelled experiment, not a final result.

## Start here

- `CHECKLIST.md`: challenge deliverables and remaining work.
- `FINDINGS.md`: findings, limitations and current candidate.
- `results/SCALING.md`: preliminary 1–2-node weak scaling, including timeout caveat.
- `results/scaling-short.svg`: preliminary scaling plots.
- `results/FINAL_STATUS.md`: latest collected final-job status.
- `results/FINAL_SCALING.md`: final results as they complete; pending rows are not measurements.
- `results/scaling-final.svg`: final-run scaling plot, generated once results exist.
- `results/hpcg-cirrus.csv`: extracted Cirrus results and accounting boundaries.
- `artifacts/cirrus/accounting.psv`: raw Slurm job AND step accounting. Do not sum both.
- `artifacts/cirrus/experiments/runs/572008/`: same-node ABBA build comparison.
- `artifacts/indyscc/studies/`: shuffled repeated free-node experiments.
- `brief/`: original challenge PDF and extracted text.

## Layout

`source/hpcg/` is an upstream source snapshot, including licences, from commit
`114602d458d1034faa52b71e4c15aba9b3a17698` of
https://github.com/hpcg-benchmark/hpcg . No tracked source modifications were made.
Generated architecture files are preserved separately under `artifacts/cirrus/setup/`.

`artifacts/cirrus/` preserves the original build/run layout and every available
experiment binary, `.dat`, job script, build log, validation log and metadata.
Original Cirrus path:
`/epccfs/tc079/tc079/tc079mart1/hpcg-work/hpcg`.

`artifacts/indyscc/` preserves free-node binaries, results, plans, build metadata
and scripts. Original path: `indyscc-pip:/home/pip/ciuk-hpcg`.
Its MPI binaries depend on the user-local MPICH installation there; they are
not expected to run on Cirrus. MPICH configuration is recorded in metadata.
Do not interpret Intel performance as AMD energy or inter-node scaling evidence.

## Leading HPCG candidate

- GNU14.2 through Cray `CC`, cray-mpich8.1.32; full module lists in run directories.
- `-O3 -ffast-math -funroll-loops`, `HPCG_NO_OPENMP`, ordinary row allocations.
- 288MPI ranks/node; one thread/rank; no SMT; core binding; block:block distribution.
- Local16x16x16 on every rank. This is the input reader's minimum local dimension.
- One-minute run571994: numerically VALID,546.556GFLOP/s;
  job72seconds,60525J,estimated0.65018GFLOP/s/W.
- Same-node comparison572008: baseline511.49/511.492 versus candidate554.179/550.764GFLOP/s.
  Candidate mean throughput is8.01% higher. Short step-energy samples do not establish an efficiency winner.

No candidate is proven globally optimal. Small domains deliberately favour cache
reuse; state that in the report. The supplied brief specifies no minimum memory
fraction. Supplementary organiser instructions have not been checked.

## Rebuild on Cirrus

From the `Edinburgh/` directory of a copy of this repository on the Cirrus project filesystem:

```bash
bash scripts/build-cirrus.sh rows-fast
# Or: original / contiguous, each in a separate clean directory.
```

The script selects GNU14.2, creates an architecture file and records modules,
compiler version, build output and binary hash. Rebuilding with different system
modules can change the binary. Original binaries remain under `artifacts/`.

The preserved run scripts expect the original layout: an `experiments/` directory
next to `build-contig/`, `build-rows-fast/` and `setup/`. On Cirrus, that layout still
exists at the path above. For a fresh deployment, recreate it or adapt the explicit
binary/metadata paths in the scripts. Merely copying a job script elsewhere is not sufficient.

## Regenerate analysis locally

```bash
python3 scripts/summarise-cirrus.py
python3 scripts/verify-artifacts.py
```

Uses Python standard library only. Raw inputs are never overwritten by analysis.
The CSV combines HPCG's timed-phase rating with whole-job mean power for standalone
jobs. That is a documented estimate, not a timed-phase-only power measurement.
ABBA step efficiency is deliberately omitted because short-step energy is unreliable.

Weak scaling holds local size and ranks/node fixed, increasing total work with
nodes. `GFLOPs(N)/(N*GFLOPs(1))` is weak-scaling throughput efficiency, not fixed-work
speedup. Job energies from different weak-scaled problems are not equal-work energy-to-solution.

## Remaining scaling and final runs

Short1-node job572012 completed. Short2-node572013 produced a VALID result but was
marked TIMEOUT at61seconds; benchmark and batch steps exited successfully.
Short3/4-node jobs572014/572015 were cancelled before starting after that timeout.
They need a more generous walltime and an agreed budget; they have not been retried.

`scripts/scaling-final.slurm` is the approved final script. It targets1920seconds
(32minutes), requests exclusive nodes and a45-minute safety limit, and requires
`HPCG_FINAL_APPROVED=YES`. It was submitted for1/2/3/4nodes as jobs
572034/572035/572036/572037, chained with afterok dependencies. Do not submit duplicates.
Its default node count is1; each node count requires matching `--nodes` and
`--ntasks=288*nodes` arguments. Deployment uses the original experiments layout.
Jobs run sequentially, never on ten nodes concurrently. A validation/duration
failure blocks later jobs; there are no automatic compute retries.

A32-minute1/2/3/4-node series requires at least1536core-hours before setup.
The template checks actual timed duration>=1800seconds as well as numerical validation;
requested time can exceed actual HPCG timed duration, as our short logs demonstrate.
HPL still needs its own allocation and deliverables. SAFE balance remains unconfirmed.
The45-minute safety limits imply a worst-case2160core-hour ceiling for all four jobs.

## Automatic collection

`scripts/collect-final-results.py` runs locally against the existing authenticated
tmux SSH session. It polls once per minute, exports terminal-job artefacts with a
SHA256-verified transfer, regenerates analysis, commits and pushes to GitHub.
It submits NO compute jobs. A temporary systemd sleep inhibitor is active while
the local collector lives; it ends automatically when that collector exits. Do not
power off or force suspend this machine if automatic GitHub updates are wanted.
A disconnected session or failed push is logged locally at
`/home/pip/ciuk-final-collector.log`.

A second lightweight watcher, `watch-finals-on-cirrus.py`, runs independently on
the Cirrus login node. It preserves final accounting and immutable, hash-addressed
archives even if local SSH disconnects. It holds no GitHub credentials and submits
no compute jobs/retries. Its log and latest export location are in the original
Cirrus `experiments/final-watcher.log` and `experiments/overnight-status.json`.
This fallback cannot push to GitHub; reconnect and collect later if local collection
stops. Both watchers have a24-hour monitoring limit, not a compute-job time limit.
Failed prerequisites block/cancel downstream queued jobs; running jobs are not killed
by the watchers. No automatic retries consume further allocation.

If necessary, restart the local collector after restoring authentication. Do not
start multiple collectors concurrently. `--once --no-push` performs one collection pass.
