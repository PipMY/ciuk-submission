# Final-run weak scaling

Local16^3,288ranks/node,one thread/rank. Work increases with node count.
This is not fixed-workload speedup or equal-work energy-to-solution.
GFLOP/s/W combines timed-phase rating with whole-job mean power.
Only rows marked eligible meet numerical validation, actual timed duration>=1800seconds and COMPLETED state.
Missing rows are pending, running or failed: do not treat them as measurements.

| Nodes | Job | State | GFLOP/s | Mean W | GFLOP/s/W | Weak efficiency | Job s | Joules | Eligible final duration |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 572034 | COMPLETED | 537.34 | 1004.8 | 0.535 | 100.0% | 1867 | 1876027 | Yes |
| 2 | 572035 | CANCELLED by 10332 | | | | | | | No |
| 3 | 572036 | CANCELLED by 10332 | | | | | | | No |
| 4 | 572037 | FAILED | 2010.66 | 4031.9 | 0.499 | 93.5% | 1762 | 7104128 | No |
