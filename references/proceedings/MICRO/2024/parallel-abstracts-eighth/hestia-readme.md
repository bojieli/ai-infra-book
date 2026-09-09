# Hestia: An Efficient Cross-level Debugger for High-level Synthesis

## Introduction
High-level synthesis offers an opportunity to design hardware at the software level, which automatically transforms high-level specifications into RTL designs. However, HLS compilers are often considered complex black-box procedures, lacking transparency for designers and hindering the debugging process. Programmers often rely on simulating the HLS design to comprehend the behavior of the generated hardware. RTL simulation, the prevalent hardware debugging method, is time-consuming and inundates designers with excessive details when applied to HLS designs. Conversely, software-level simulation sacrifices hardware-specific details, resulting in inaccurate results. The debugging challenge primarily stems from the semantic gap between software descriptions and RTL implementations.

This project proposes Hestia, an efficient cross-level debugger enabling debugging HLS designs at different abstraction levels. Hestia provides a multi-level interpreter, aiding in debugging various issues in the HLS procedure with less hardware details and lower time costs. With an equivalent mapping across different levels, Hestia facilitates bug identification and localization, providing breakpoints and stepping at multiple granularities. 

## [Artifact](https://github.com/pku-liang/hestia-artifact)
Examples about interactive debugging using Hestia are shown in the artifact repo above.

## Citing Hestia
```latex
@inproceedings{Hestia,
  author = {Ruifan, Xu and Jin, Luo and Yanwen, Zhang and Yibo, Lin and Runsheng, Wang and Ru, Huang and Yun, Liang},
  title = {Hestia: An Efficient Cross-level Debugger for High-level Synthesis},
  booktitle = {MICRO '24: 55th IEEE/ACM International Symposium on Microarchitecture},
  publisher = {IEEE},
  year = {2024},
}
```

## Introduction

High-level synthesis offers an opportunity to design hardware at the software level, which automatically transforms high-level specifications into RTL designs. However, HLS compilers are often considered complex black-box procedures, lacking transparency for designers and hindering the debugging process. Programmers often rely on simulating the HLS design to comprehend the behavior of the generated hardware. RTL simulation, the prevalent hardware debugging method, is time-consuming and inundates designers with excessive details when applied to HLS designs. Conversely, software-level simulation sacrifices hardware-specific details, resulting in inaccurate results. The debugging challenge primarily stems from the semantic gap between software descriptions and RTL implementations. 

This project presents Hestia, an efficient cross-level debugger enabling debugging HLS designs at different abstraction levels. Hestia provides a multi-level interpreter, aiding in debugging various issues in the HLS procedure with less hardware details and lower time costs. With an equivalent mapping across different levels, Hestia facilitates bug identification and localization, providing breakpoints and stepping at multiple granularities. We demonstrate the effectiveness of Hestia from three aspects: simulation efficiency, debugging capability, and scalability.

# Setup

## Install Rust

```bash
curl https://sh.rustup.rs -sSf | sh
```

## Build Hestia

```bash
git clone https://github.com/pku-liang/hestia.git
cargo build --all --release
```

## Error Encountered When Building Hestia

If you encounter the following error:
```bash
Error[E0658]: #[diagnostic] attribute name space is experimental
```

You can resolve this by installing and setting the nightly version of Rust:

```bash
rustup install nightly
rustup default nightly
```
