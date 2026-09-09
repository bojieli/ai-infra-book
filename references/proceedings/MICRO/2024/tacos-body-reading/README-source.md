<!--
## This source code is licensed under the MIT license found in the
## LICENSE file in the root directory of this source tree.
##
## Copyright (c) 2022-2025 Intel Corporation
## Copyright (c) 2022-2025 Georgia Institute of Technology
-->

# 🌮 TACOS
### [T]opology-[A]ware [Co]llective Algorithm [S]ynthesizer for Distributed Machine Learning

## Latest Release
[Latest Release](https://github.com/astra-sim/tacos/releases)

## Project Status
| branch | Build | Test | Format |
|:---:|:---:|:---:|:---:|
| **main** | [![build-ubuntu](https://github.com/astra-sim/tacos/actions/workflows/build-ubuntu.yml/badge.svg?branch=main)](https://github.com/astra-sim/tacos/actions/workflows/build-ubuntu.yml) [![build-macos](https://github.com/astra-sim/tacos/actions/workflows/build-macos.yml/badge.svg?branch=main)](https://github.com/astra-sim/tacos/actions/workflows/build-macos.yml) | [![test-ubuntu](https://github.com/astra-sim/tacos/actions/workflows/test-ubuntu.yml/badge.svg?branch=main)](https://github.com/astra-sim/tacos/actions/workflows/test-ubuntu.yml) [![test-macos](https://github.com/astra-sim/tacos/actions/workflows/test-macos.yml/badge.svg?branch=main)](https://github.com/astra-sim/tacos/actions/workflows/test-macos.yml) | [![format](https://github.com/astra-sim/tacos/actions/workflows/check-clang-format.yml/badge.svg?branch=main)](https://github.com/astra-sim/tacos/actions/workflows/check-clang-format.yml) |
| **develop** | [![build-ubuntu](https://github.com/astra-sim/tacos/actions/workflows/build-ubuntu.yml/badge.svg?branch=develop)](https://github.com/astra-sim/tacos/actions/workflows/build-ubuntu.yml) [![build-macos](https://github.com/astra-sim/tacos/actions/workflows/build-macos.yml/badge.svg?branch=develop)](https://github.com/astra-sim/tacos/actions/workflows/build-macos.yml) | [![test-ubuntu](https://github.com/astra-sim/tacos/actions/workflows/test-ubuntu.yml/badge.svg?branch=develop)](https://github.com/astra-sim/tacos/actions/workflows/test-ubuntu.yml) [![test-macos](https://github.com/astra-sim/tacos/actions/workflows/test-macos.yml/badge.svg?branch=develop)](https://github.com/astra-sim/tacos/actions/workflows/test-macos.yml) | [![format](https://github.com/astra-sim/tacos/actions/workflows/check-clang-format.yml/badge.svg?branch=develop)](https://github.com/astra-sim/tacos/actions/workflows/check-clang-format.yml) |

# Overview
TACOS is a topology-aware collective algorithm synthesizer:
- TACOS receives a network topology description and target collective patterns.
- Then, TACOS autonomously analyzes provided inputs and synthesizes topology-aware collective algorithms.

The below figure summarizes the TACOS framework:
![TACOS Abstraction](https://github.com/astra-sim/tacos/blob/main/docs/tacos_overview.png)

## Constraints
TACOS currently supports:
- Network topology: point-to-point (direct-connect) only. Networks can be asymmetric and heterogeneous.
  - Switch should be unwound to point-to-point connections.
- Target collective pattern: All-Gather
  - Although Reduce-Scatter and All-Reduce can be supported by TACOS, their implementations are currently in progress.
  - All-to-All is not supported in TACOS.
- Output: TACOS currently reports the estimated collective time of the synthesized collective algorithm.
  - MSCCL-XML generation is currently in progress so that the TACOS algorithm can run on real systems via MSCCL (see [MSCCLang Paper](https://dl.acm.org/doi/10.1145/3575693.3575724)).

## Paper
Please find more information about the framework in the TACOS paper [[IEEExplorer]](https://arxiv.org/abs/2304.05301) [[arXiv]](https://arxiv.org/abs/2304.05301).
- You can cite the paper (BibTeX) by clicking the *Cite this repository* button (on the right side toolbar below the *About* tab).


# Contact Us
For any questions about TACOS, please contact [Will Won](mailto:william.won@gatech.edu)
or [Tushar Krishna](mailto:tushar@ece.gatech.edu). You can also search for or create new GitHub issues.

## Contributing
We sincerely appreciate your contribution to the TACOS project! Please see [CONTRIBUTING.md](https://github.com/astra-sim/tacos/blob/main/CONTRIBUTING.md) for contribution guidelines.


# Getting Started
## Prerequisite
TACOS is a C++17-based project, using CMake as the build manager.
- `g++` or `clang`
- `cmake >= 3.26`

### Docker
We also deploy TACOS in Docker Image. You can pull this image via Docker Hub.
```sh
docker pull astrasim/tacos:latest
docker run -it astrasim/tacos:latest
```

Instead, you may build the Docker Image locally via this repository itself.
```sh
./utils/build_docker_image.sh
./utils/start_docker_container.sh
```

## Compiling TACOS
You can compile TACOS using the provided script (`tacos.sh`)
```sh
./tacos.sh configure  # Running CMake to configure the build
./tacos.sh build  # Compiles TACOS
```

After a successful build, the project will compile TACOS as a library file (`libtacos.a`) as well as an example executable file from `src/main.cpp`
```text
build
├── bin
│   └── tacos
└── lib
    └── libtacos.a
```

## Executing TACOS
You can run the compiled example binary (`build/bin/tacos`) either directly or via the provided script.
```sh
./tacos.sh run
```

## Regression Tests
TACOS is also equipped with a small set of simple regression tests (inside the `tests/` directory). You can compile and run these tests via the script.
```sh
./tacos.sh configure --with-tests  # Enables Debug mode and tests/ compilation
./tacos.sh build
./tacos.sh test  # Runs ctest for regression tests
```
Since this builds TACOS with debug mode (which is significantly slower), we recommend to re-compile TACOS without passing the `--with-tests` option to enable compiler optimizations.


# Deeper Dive
## Network Topology
Network topologies are declared inside `include/tacos/topology` and defined inside `src/topology` directories.

One can declare a new network topology file by creating a new header file and a new class inheriting the base `Topology` class. One can add any class member variables as they wish, but often times having only the constructor is sufficient. For example, see the `include/tacos/topology/mesh_2d.h` declaration:
```cpp
#pragma once

#include <tacos/topology/topology.h>

namespace tacos {
class Mesh2D final : public Topology {
  public:
    Mesh2D(int width, int height, Bandwidth bandwidth, Latency latency) noexcept;
};
}  // namespace tacos
```

Then, one can actually define the topology/constructor inside the `src/topology` directory. Important APIs to do this are:
- `setNpusCount_(npusCount)`
  - Set the number of NPUs (i.e., endpoints) inside the topology.
- `connect_(src, dest, bandwidth, latency, bidirectional)`
  - Create a connection between `src -> dest`.
  - This connection's bandwidth and latency is provided in **GiB/s** and **microseconds (us)**, respectively.
  - Note this API constructs a **unidirectional** connection. You may set bidirectional=true to automatically construct `dest -> src` connectivity with the same bandwidth and latency numbers.

For example, the implementation of `width x height` 2D Mesh (`src/topology/mesh_2d.cpp`):
```cpp
#include <tacos/topology/mesh_2d.h>

using namespace tacos;

Mesh2D::Mesh2D(const int width,
               const int height,
               const Bandwidth bandwidth,
               const Latency latency) noexcept : Topology() {

    setNpusCount_(width * height);  // number of NPUs = width * height

    // connect x-axis wise
    for (auto row = 0; row < height; ++row) {
        for (auto col = 0; col < (width - 1); ++col) {
            const auto src = (row * width) + col;
            const auto dest = src + 1;
            connect_(src, dest, bandwidth, latency, true);  // connection
        }
    }

    // connect y-axis wise
    for (auto row = 0; row < (height - 1); ++row) {
        for (auto col = 0; col < width; ++col) {
            const auto src = (row * width) + col;
            const auto dest = src + width;
            connect_(src, dest, bandwidth, latency, true);  // connection
        }
    }
}
```

Finally, make sure to list newly added files inside the `src/CMakeLists.txt` file.
```cmake
add_library(tacos
    ...
    topology/mesh_2d.cpp ${CMAKE_SOURCE_DIR}/include/tacos/topology/mesh_2d.h
    ...
)
```

## Collective Pattern
Currently, TACOS only supports the **All-Gather** collective pattern is being supported, with **Reduce-Scatter** and **All-Reduce** pattern implementations in progress. You can see the signature of the All-Gather pattern inside `include/tacos/collective/all_gather.h`:
```cpp
class AllGather final : public Collective {
  public:
    AllGather(int npusCount, int collectivesCount = 1) noexcept;
```
- `npusCount`: Number of NPUs of the target topology.
  - This can easily be retrieved from the target topology itself via `topology.npusCount()`.
- `collectivesCount`: Number of initial (input) chunks per each NPU.
    - For example, if `npusCount=4` and `collectivesCount=3`, each NPU will start with 3 chunks (input buffer) and end up with 12 chunks (output buffer).
 
## TACOS API
TACOS synthesizer is simply instantiated by calling its constructor without any argument:
```cpp
#include <tacos/synthesizer/synthesizer.h>

using namespace tacos;

int main() {
  auto synthesizer = Synthesizer();
}
```

The synthesizer has `solve(topology, collective, chunkSize) -> time` method to synthesize the target collective algorithm.
- `topology` is the target network topology object.
- `collective` is the target collective communication pattern (for now, an `All-Gather` pattern).
- `chunkSize` is the size of each chunk, in bytes.
  - For example, recall the All-Gather with `npusCount=4` and `collectivesCount=3`. If the `chunkSize` is 1,048,576 (1 MB), the input buffer size of this All-Gather is 3 MB, and the output buffer size is 12 MB.
  - In other words, if you know the input buffer size, `chunkSize` can be deduced via `(chunk size) = (input buffer size) / (collectivesCount)`.
  - Likely, from provided output buffer size, `chunkSize` can be deduced via `(chunk size) = (output buffer size) / (collectivesCount * npusCount)`

`solve(solve(topology, collective, chunkSize) -> time` returns a `time` value, which is the estimated collective time of the synthesized collective algorithm. The unit of time is in microseconds (us).
- TACOS is currently being upgraded to also generate an MSCCL-XML representation, which is a concise representation that holds the actual collective algorithm, not just the estimated collective time.

`src/main.cpp` implements an example TACOS run by instantiating a Mesh2D topology and an All-Gather collective, as below:
```cpp
int main() {
  // create topology
  const auto topology = Mesh2D(4, 3, 50, 0.5);  // 4x3 (12-NPU) Mesh, each link: 50 GiB/s & 0.5 us
  const auto npusCount = topology.npusCount();

  // create collective
  const Collective::ChunkSize outputBufferSize = 12 * (1 << 20);  // 12 MiB
  const auto collectivesCount = 3;  // 3 initial chunks per each NPU
  const auto collective = AllGather(npusCount, collectivesCount);
  const auto chunkSize = outputBufferSize / (npusCount * collectivesCount);

  // run synthesizer
  auto synthesizer = Synthesizer();
  auto collectiveTime = synthesizer.solve(topology, collective, chunkSize);  // TACOS API call
  std::cout << "Collective Time: " << collectiveTime << " us" << std::endl;
}
```
