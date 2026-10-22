#!/usr/bin/env python3
import os
import sys
rank = int(os.environ['PMI_RANK'])
threads = int(os.environ['OMP_NUM_THREADS'])
cpus = set(range(rank * threads, (rank + 1) * threads))
os.sched_setaffinity(0, cpus)
with open(f'affinity-rank-{rank}.txt', 'w') as f:
    f.write(f'rank={rank} cpus={sorted(os.sched_getaffinity(0))}\n')
os.execv(sys.argv[1], sys.argv[1:])
