# Findings and evidence

## Method and machines

Cirrus:288physical cores/node, dual AMD EPYC9825,8NUMA domains,24CCDs,
Cray MPICH/Slingshot. Dedicated nodes required by challenge.
IndySCC:64physical cores/node, dual Intel Xeon Gold6548Y+,2NUMA domains,
user-local MPICH4.2.3 ch3:nemesis, shared unreserved system.
Source revision is identical on both. No reference kernel source changes.

## Established observations

1. Reference ComputeSYMGS_ref.cpp has serial forward/backward sweeps.
   OpenMP does not parallelise this dominant multigrid work.
2. IndySCC fixed-global128^3 experiment strongly favours more MPI ranks:
   1x64:1.66;2x32:4.31;4x16:8.33;8x8:14.50;16x4:23.81;
   32x2:33.51;64x1:71.02GFLOP/s. Selected configurations repeated.
3. Size/storage study:64pinned ranks, two shuffled repeats each.

| Local n | Approx data GB | Rows mean GFLOP/s | Contiguous mean GFLOP/s |
|---:|---:|---:|---:|
|16|0.189|130.935|118.281|
|24|0.635|90.829|98.536|
|32|1.503|71.478|76.020|
|48|5.068|64.036|68.330|
|64|12.008|62.268|66.474|

   Contiguous arrays help larger tested cases by6–8%, but not the smallest.
   Size changes workload; this is not fixed-workload speedup.
4. IndySCC kernel/build screening, two repeats each at local16^3:
   contig+OMP115.024;rows+OMP121.388;contig-noOMP119.46;
   rows-noOMP118.128;contig-fast129.986;rows-fast138.768GFLOP/s.
   Fast variants combine noOMP,fast-maths and unrolling. Cannot attribute all
   improvement to one flag. Validation passed; iterations/set remained50.
5. Cirrus same-node ABBA job572008 confirms a throughput improvement:
   contig+OMP511.490/511.492;rows-fast554.179/550.764GFLOP/s.
   Mean gain8.01%. All VALID. Not proof of an efficiency gain.

## Cirrus efficiency observations and limitations

Standalone jobs use rating/(ConsumedEnergyRaw/job_elapsed_seconds).
This combines timed-phase rating with whole-job mean power, including setup.
Node-to-node and short sampling-window effects are not controlled in these jobs.

- Initial24x12,local64^3:93.8506GFLOP/s,~0.117GFLOP/s/W.
- Contiguous288x1,local64^3:146.266,~0.175.
- Contiguous288x1,local32^3:166.659,~0.241.
- Contiguous288x1,local24^3:275.173,~0.526.
- Contiguous288x1,local16^3,10-second target:506.49,~0.904.
- Same configuration,60-second target:501.353,~0.544.
- Rows-fast288x1,local16^3,60-second target:546.556,~0.650.

The0.904 observation did NOT survive the longer repeat; do not advertise it as
stable or compare it directly to minute-long results. Performance around500+
GFLOP/s is more repeatable than those short-job energy estimates.
ABBA step0/step3 used the same binary and similar runtime but reported10160J and
13391J respectively. This is why per-step efficiency is not used to declare a winner.

## Preliminary weak scaling

See results/SCALING.md and raw accounting for authoritative numbers.
One node:548.80GFLOP/s. Two nodes:1004.60GFLOP/s,~91.5% throughput efficiency.
Two-node benchmark VALID, but overall jobTIMEOUT at61seconds during completion;
retain that qualification. Three/four-node jobs cancelled before running.
No inter-node scaling conclusion beyond two nodes is supported yet.

## Not established

- Globally optimal compiler, flags, core count, placement or problem size.
- Actual use or benefit of huge pages: system THP enabled is not process-level proof.
- A stable energy-efficiency winner under controlled same-node, sufficiently long measurement.
- Final-duration validation/performance/efficiency at any node count.
- Three/four-node scaling or any HPL results.

## Budget and stop conditions

This final tuning/packaging batch used19.2recorded core-hours:
comparison6.72;short1node2.72;short2nodes9.76.
Queued3/4node tests were cancelled before allocation. No automatic retries.
All inspected Cirrus jobs together used56.24core-hours, not the full team usage.
SAFE balance remains unconfirmed. The user subsequently explicitly approved the final
1/2/3/4-node series:jobs572034/572035/572036/572037,32-minute targets,45-minute
safety limits, afterok chain. Their outcomes are recorded separately in
results/FINAL_STATUS.md and FINAL_SCALING.md as collected; they are not assumed complete.
