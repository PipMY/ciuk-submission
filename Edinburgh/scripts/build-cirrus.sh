#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
variant=${1:?Usage: build-cirrus.sh original|contiguous|rows-fast}
case "$variant" in
    original) options=''; flags='-O3 -fopenmp';;
    contiguous) options='-DHPCG_CONTIGUOUS_ARRAYS'; flags='-O3 -fopenmp';;
    rows-fast) options='-DHPCG_NO_OPENMP'; flags='-O3 -ffast-math -funroll-loops';;
    *) echo 'Unknown variant' >&2; exit 2;;
esac
module restore
module load PrgEnv-gnu/8.6.0 gcc-native/14.2
source="$repo/source/hpcg"
arch="CIUK_${variant}"
build="$repo/rebuild/$variant"
if [[ -e "$build/Makefile" ]]; then
    echo "Refusing to reuse an existing configured build: $build" >&2
    exit 1
fi
cp "$source/setup/Make.MPI_GCC_OMP" "$source/setup/Make.$arch"
printf '\n%s\n' 'CXX = CC' "HPCG_OPTS = $options" \
    'CXXFLAGS = $(HPCG_DEFS) '"$flags" \
    'LINKER = $(CXX)' 'LINKFLAGS = $(CXXFLAGS)' >> "$source/setup/Make.$arch"
mkdir -p "$build"
cd "$build"
"$source/configure" "$arch"
make -j8 2>&1 | tee build.log
module list > modules-build.txt 2>&1
CC --version > compiler.txt 2>&1
sha256sum bin/xhpcg > binary.sha256
