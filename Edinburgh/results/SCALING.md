# Preliminary short-run weak scaling

Local16^3,288ranks/node,one thread/rank. Work increases with node count.
This is not fixed-workload speedup or equal-work energy-to-solution.
GFLOP/s/W combines timed-phase rating with whole-job mean power.
Two-node benchmark VALID, but overall jobTIMEOUT during cleanup.
Short3/4-node jobs cancelled before allocation. Short-run energy is uncertain.

| Nodes | Job | State | GFLOP/s | Mean W | GFLOP/s/W | Weak efficiency | Job s | Joules | Eligible final duration |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 572012 | COMPLETED | 548.80 | 718.4 | 0.764 | 100.0% | 34 | 24424 | No |
| 2 | 572013 | TIMEOUT | 1004.60 | 1280.7 | 0.784 | 91.5% | 61 | 78125 | No |
| 3 | 572014 | CANCELLED by 10332 | | | | | | | No |
| 4 | 572015 | CANCELLED by 10332 | | | | | | | No |
