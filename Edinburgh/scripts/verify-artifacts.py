#!/usr/bin/env python3
import hashlib
from pathlib import Path
import sys

repo = Path(__file__).resolve().parent.parent
checked = 0
errors = []
for manifest in (repo / 'artifacts/cirrus').rglob('*.sha256'):
    if manifest.name not in ('binary.sha256', 'binaries.sha256'):
        continue
    for line in manifest.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        path = manifest.parent / Path(name.strip().lstrip('*')).name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(str(path))
        checked += 1
manifest = repo / 'BINARY_SHA256SUMS'
if manifest.exists():
    for line in manifest.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        path = repo / name.strip()
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(str(path))
        checked += 1
if errors:
    print('FAILED:', *errors, sep='\n', file=sys.stderr)
    sys.exit(1)
print(f'Verified {checked} binary hash records.')
