# 网页配图原件

从明确选取的官方网页下载配图，保留原始图像，不重绘或修改。来源网页快照与每幅图的校验值见 [manifest.json](manifest.json)。这些配图不另计作论文或规格文档。

维护命令：`python3 references/fetch_figures.py 资料ID ...`。仅处理指定的已归档网页，不递归抓取站点；已有且校验通过的图片不重复下载。

## Inside the Eighth-Generation TPU: An Architecture Deep Dive

[本地正文](../files/specs/google-tpu8.html) · [官方来源](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)

- [1_v4.max-1600x1600.png](google-tpu8-efb12c0471ce.png)
- [2_TPU_8t_rack_level_connectivity_to_Virgo_.max-2000x2000.png](google-tpu8-333253b6a57b.png)
- [3_rq0yjyX.max-2000x2000.png](google-tpu8-347d56803913.png)
- [4_v1_nUZDsJM.max-1800x1800.png](google-tpu8-8c23ee7ebf97.png)
- [5_I1mUzjb.max-1300x1300.png](google-tpu8-3c98b1d8bbc3.png)
- [6_Qu7H2lI.max-1300x1300.png](google-tpu8-e0b83cd51005.png)

## IPU Hardware Overview

[本地正文](../files/documents/graphcore-hardware.html) · [官方来源](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/latest/about_ipu.html)

- [Example of an IPU-Machine. The Bow-2000 is a building block for Bow Pod systems.](graphcore-hardware-a20b3638d71b.jpg)
- [IPU internal architecture](graphcore-hardware-cbd58c8c2ff4.png)
- [IPU memory architecture](graphcore-hardware-87ad33b7ea50.png)
- [Phases of task execution](graphcore-hardware-d6b3e23f1ada.png)
- [Multiple phases in steps](graphcore-hardware-e8f1ec5d6a7f.png)
- [Sync, exchange and compute activity across tiles](graphcore-hardware-7df31497332c.png)
- [Execution activity of all tiles in IPU](graphcore-hardware-d1685912c8e0.png)
- [IPU tile memory](graphcore-hardware-49aadbcceef9.png)
- [Host to IPU communication](graphcore-hardware-0be1cf5cf64b.png)

## IPU Programming Model

[本地正文](../files/documents/graphcore-programming.html) · [官方来源](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/latest/programming_model.html)

- [Programs running on a set of IPUs](graphcore-programming-1bb345dd2b5c.png)
- [A variable and its mapping to tiles](graphcore-programming-fe23833c2409.png)
- [Multiple views on the same variable](graphcore-programming-abfb89de6ad1.png)
- [A compute set](graphcore-programming-464255ef9a33.png)
- [The entire system of IPUs runs a single program](graphcore-programming-048fdaf514d7.png)
- [The vertices within a compute sets](graphcore-programming-008f1f52e038.png)
- [Graph representation of variables and processing](graphcore-programming-9c65a042d274.png)
- [A program splitting into parallel sub-programs](graphcore-programming-e20849ac1095.png)
- [Parallel execution of I/O](graphcore-programming-eb726c43b98e.png)
- [Loading programs on to the IPU](graphcore-programming-49272d298fa4.png)
- [Selecting a control program to run](graphcore-programming-ec750e4b48cc.png)
- [A typical framework lowering to run on an IPU](graphcore-programming-9e4dd8e797a1.png)
- [Lowering a program to explicit sync, exchange and compute steps](graphcore-programming-59c4c9728eb2.png)
- [Lowering a program to multiple tiles](graphcore-programming-b490fbf148d2.png)
- [Live variable memory over time](graphcore-programming-99641d5ce2fe.png)

## AWS Trainium3 Architecture

[本地正文](../files/specs/aws-trainium3.html) · [官方来源](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium3.html)

- [../../../_images/neuroncore-v4-overview.png](aws-trainium3-946fbb339674.png)

## Trainium3 Architecture Guide for NKI

[本地正文](../files/documents/aws-trainium3-nki.html) · [官方来源](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/guides/architecture/trainium3_arch.html)

- [../../../_images/nki-trn3-arch-1.png](aws-trainium3-nki-1f9ce33c45df.png)
- [../../../_images/nki-trn3-arch-2.png](aws-trainium3-nki-ca50b02912c9.png)
- [../../../_images/nki-trn3-arch-3.png](aws-trainium3-nki-151a617e353a.png)
- [../../../_images/nki-trn3-arch-4.png](aws-trainium3-nki-f8b8b77ca6cf.png)
- [../../../_images/nki-trn3-arch-5.png](aws-trainium3-nki-c32a18ac4f9c.png)
- [../../../_images/nki-trn3-arch-6.png](aws-trainium3-nki-b49b306e615d.png)
- [../../../_images/nki-trn3-arch-7.png](aws-trainium3-nki-fd3b460ddc8b.png)
- [../../../_images/nki-trn3-arch-8.png](aws-trainium3-nki-f9aa8610dfd2.png)
- [../../../_images/nki-trn3-arch-9.png](aws-trainium3-nki-443b7168e174.png)
- [../../../_images/nki-trn3-arch-10.png](aws-trainium3-nki-cd2898f7f080.png)
- [../../../_images/nki-trn3-arch-11.png](aws-trainium3-nki-47618f5b676b.png)
- [../../../_images/nki-trn3-arch-12.png](aws-trainium3-nki-f5da8e720c0c.png)
- [../../../_images/nki-trn3-arch-13.png](aws-trainium3-nki-62e0c66e865d.png)
- [../../../_images/nki-trn3-arch-14.png](aws-trainium3-nki-169000590ef4.png)
- [../../../_images/nki-trn3-arch-15.png](aws-trainium3-nki-9d7820c1ed85.png)
