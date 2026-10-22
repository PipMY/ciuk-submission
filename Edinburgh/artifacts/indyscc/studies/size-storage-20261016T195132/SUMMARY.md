# Size and storage experiment

64 MPI ranks x 1 thread; pinned physical cores; fixed compiler flags.
Two repeats, shuffled order; short exploratory runs on a shared node.
No node energy measured: performance rankings are NOT efficiency rankings.

| Local n | Global n | Data GB | Rows mean GFLOP/s | Contiguous mean GFLOP/s | Change |
|---:|---:|---:|---:|---:|---:|
| 16 | 64 | 0.189 | 130.935 | 118.281 | -9.7% |
| 24 | 96 | 0.635 | 90.829 | 98.536 | +8.5% |
| 32 | 128 | 1.503 | 71.478 | 76.020 | +6.4% |
| 48 | 192 | 5.068 | 64.036 | 68.330 | +6.7% |
| 64 | 256 | 12.008 | 62.268 | 66.474 | +6.8% |

Individual samples and timing breakdowns are in results.csv.
Smallest size may benefit from cache residency; do not infer final-submission eligibility.
Changing size changes work and cache behaviour. It is not a fixed-problem speedup.
Huge-page state was not manipulated; actual allocation page sizes were not verified.
