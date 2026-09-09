#!/usr/bin/env bash
set -euo pipefail
# Linux x86_64; installs privately and does not change drivers or system packages.
target_dir="${1:-$PWD/nsys-local}"
mkdir -p "$target_dir"
cd "$target_dir"
curl -fL --retry 2 -o nsys-cli.deb 'https://developer.nvidia.com/downloads/assets/tools/secure/nsight-systems/2026_4/NsightSystems-linux-cli-public-2026.4.1.191-3860507.deb'
echo 'b896cb2b9586ddf617c363a43bababad0a015dff4c77d8f0fbb9c26144056a69  nsys-cli.deb' | sha256sum -c -
dpkg-deb -x nsys-cli.deb extracted
realpath extracted/opt/nvidia/nsight-systems-cli/2026.4.1/target-linux-x64/nsys
