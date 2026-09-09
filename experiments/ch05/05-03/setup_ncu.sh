#!/usr/bin/env bash
set -euo pipefail
target_dir="${1:-$PWD/ncu-local}"
mkdir -p "$target_dir"
cd "$target_dir"
curl -fL --retry 2 -o ncu.deb 'https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/nsight-compute-2026.2.1_2026.2.1.5-1_amd64.deb'
echo '6829651ceeb0c3f65890b9f727b74d1e550fed58c454e11c2c87442295e4eb70  ncu.deb' | sha256sum -c -
dpkg-deb -x ncu.deb extracted
realpath extracted/opt/nvidia/nsight-compute/2026.2.1/ncu
