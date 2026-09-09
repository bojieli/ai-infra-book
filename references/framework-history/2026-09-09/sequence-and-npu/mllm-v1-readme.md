<h1 align="center">
mllm
</h1>

<h3 align="center">
fast and lightweight <ins>multimodal LLM</ins> inference engine for mobile and edge devices
</h3>

<h4 align="center">
| Arm CPU | X86 CPU | Qualcomm NPU(QNN) |
</h4>

<h4 align="center">

[![Website](https://img.shields.io/badge/website-visit-green)](https://ubiquitouslearning.github.io/mllm_website/)
[![Documentation](https://img.shields.io/badge/view-docs-blue)](https://ubiquitouslearning.github.io/mllm_website/introduction/getstarted/)
[![Android App](https://img.shields.io/badge/android-app-pink)](https://github.com/lx200916/ChatBotApp/)
[![Actions Status](https://github.com/UbiquitousLearning/mllm/workflows/Tests/badge.svg)](https://github.com/UbiquitousLearning/mllm/actions)
</h4>

- Plain C/C++ implementation without dependencies
- Optimized for multimodal LLMs like Qwen2-VL and LLaVA
- Supported: ARM NEON, x86 AVX2, Qualcomm NPU (QNN), etc
- Various quantization schemes
- End-to-end Android app demo
- Advanced support: MoE, Prompt Cache, etc..

mllm is a lightweight, fast, and easy-to-use (multimodal) on-device LLM inference engine for mobile devices (mainly supporting CPU/NPU), initiated by the research groups led by [Mengwei Xu](https://xumengwei.github.io/) (BUPT) and [Xuanzhe Liu](http://www.liuxuanzhe.com/) (PKU).

## Recent update

- [2025 July 30] Add Rotation Quantization method for QNN backend models and support Qwen-2-VL 2B
- [2025 August 28] 🔥🔥🔥 Support for MLLM V1 is ending soon. Before its retirement, V1 will integrate the following features: GPT-OSS and NPU QWEN2-VL. MLLM will then transition to V2, which can be viewed on the V2 branch.
V2 will include brand-new capabilities:
    - A more Pythonic model authoring approach with eager execution
    - Compilation support and MLLM IR for easier NPU integration
    - Support for parallel execution of multiple models
    - A more refined engineering implementation



### Contents
- [Android Demo](#android-demo)
- [Support models](#support-models)
- [Quick Start](#quick-start)
    - [Get the Code](#get-the-code)
    - [Check prerequisites](#check-prerequisites)
    - [Run Qwen with Hexagon NPU accelerating using QNN](#run-qwen-with-hexagon-npu-accelerating-using-qnn)
    - [Run with the CPU of Android](#run-with-the-cpu-of-android)
    - [Run for Linux](#run-for-linux)
- [Customization](#customization)
    - [Convert models](#convert-models)
    - [Convert vocabulary](#convert-vocabulary)
    - [Quantize models](#quantize-models)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Contribution](#contribution)
- [Acknowledgments](#acknowledgments)
- [License](#license)


## Android Demo

<table>
    <tr>
<!--         <td>Chatting</td> -->
        <td>Android Intent Invocation</td>
        <td>Image Understanding</td>
    </tr>
    <tr>
<!--         <td>  <video src="https://github.com/user-attachments/assets/972b3bad-d659-4d76-9141-64ad0ad34d64"> </td> -->
        <td>  <video src="https://github.com/user-attachments/assets/deb99f8d-9727-4519-9ca7-c39deb7c5b47"> </td>
        <td>  <video src="https://github.com/user-attachments/assets/55321a43-8484-4f74-b7b2-d4495f3626d9"> </td>
    </tr>
    <tr>
        <td>Chat CPU</td>
        <td>Chat NPU</td>
    </tr>    
    <tr>
        <td>  <video src="https://github.com/user-attachments/assets/2b0ab0d6-6727-4b85-9ee3-b39d23de5dde"> </td>
        <td>  <video src="https://github.com/user-attachments/assets/395f8e6e-2ab9-40bc-bf26-164ba5695c64"> </td>
    </tr>
</table>

## Support models

### Language models

| Model                                                                       | CPU <br> FP32 | CPU <br> INT4  | Hexagon NPU <br> INT8 |
|-----------------------------------------------------------------------------|------|-----|----------------------------|
| [LLaMA 2 7B](https://github.com/facebookresearch/llama)                   | [✔️](https://huggingface.co/mllmTeam/llama-2-7b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/llama-2-7b-mllm/tree/main)   |  |
| [LLaMA 3 1B](https://github.com/meta-llama/llama3)                   | [✔️](https://huggingface.co/mllmTeam/llama-3.2-1b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/llama-3.2-1b-mllm/tree/main)   |  |
| [LLaMA 3 3B](https://github.com/meta-llama/llama3)                   | [✔️](https://huggingface.co/mllmTeam/llama-3.2-3b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/llama-3.2-3b-mllm/tree/main)   |  |
| [Alpaca 7B](https://github.com/ymcui/Chinese-LLaMA-Alpaca-2)                | [✔️](https://huggingface.co/mllmTeam/chinese-alpaca-7b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/chinese-alpaca-7b-mllm/tree/main)   |  |
| [TinyLLaMA 1.1B](https://github.com/jzhang38/TinyLlama)                     | [✔️](https://huggingface.co/mllmTeam/tinyllama-1.1b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/tinyllama-1.1b-mllm/tree/main)   |  |
| [LLaVA 7B](https://github.com/haotian-liu/LLaVA)                            | [✔️](https://huggingface.co/mllmTeam/llava-1.5-7b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/llava-1.5-7b-mllm/tree/main)   |  |
| [Gemma 2B](https://github.com/google/gemma_pytorch)                         | [✔️](https://huggingface.co/mllmTeam/gemma-2b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/gemma-2b-mllm/tree/main)   |  |
| [Gemma 2 2B](https://github.com/google/gemma_pytorch)                         | [✔️](https://huggingface.co/mllmTeam/gemma-2-2b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/gemma-2-2b-mllm/tree/main)   |  |
| [Qwen 1.5 0.5B](https://github.com/QwenLM/Qwen)                                 | [✔️](https://huggingface.co/mllmTeam/qwen-1.5-0.5b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/qwen-1.5-0.5b-mllm/tree/main)   | ✔️ |
| [Qwen 1.5 1.8B](https://github.com/QwenLM/Qwen)                            | [✔️](https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm)  | [✔️](https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm)   | [✔️](https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm) |
| [Qwen 2.5 1.5B](https://github.com/QwenLM/Qwen2.5) | [✔️](https://huggingface.co/mllmTeam/qwen-2.5-1.5b-mllm/tree/main) | [✔️](https://huggingface.co/mllmTeam/qwen-2.5-1.5b-mllm/tree/main) | ✔️ |
| [Qwen 3 0.6B](https://github.com/QwenLM/Qwen3) | [✔️](https://huggingface.co/mllmTeam/qwen-3-0.6b-mllm/tree/main) | [✔️](https://huggingface.co/mllmTeam/qwen-3-0.6b-mllm/tree/main) | |
| [Mistral 7B](https://github.com/mistralai/mistral-src)                      | [✔️](https://huggingface.co/mllmTeam/mistral-7b-instruct-v0.2-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/mistral-7b-instruct-v0.2-mllm/tree/main)   |  |
| [Yi 6B](https://huggingface.co/01-ai/Yi-1.5-6B)                             | [✔️](https://huggingface.co/mllmTeam/yi-1.5-6b-chat-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/yi-1.5-6b-chat-mllm/tree/main)   |  |
| [StableLM 2 1.6B](https://github.com/Stability-AI/StableLM)                     | [✔️](https://huggingface.co/mllmTeam/stablelm-2-1.6b-chat-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/stablelm-2-1.6b-chat-mllm/tree/main)   |  |
| [OPT 1.3B](https://github.com/facebookresearch/metaseq/tree/main/projects/OPT)                     | [✔️](https://huggingface.co/mllmTeam/opt-1.3b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/opt-1.3b-mllm/tree/main)   |  |
| [Phi 3 mini 3.8B](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)                     |  [✔️](https://huggingface.co/mllmTeam/phi-3-mini-instruct-mllm/tree/main)   | [✔️](https://huggingface.co/mllmTeam/phi-3-mini-instruct-mllm/tree/main)   |  |
| [MiniCPM 2B](https://huggingface.co/openbmb/MiniCPM-2B-dpo-fp32)                     |  [✔️](https://huggingface.co/mllmTeam/minicpm-2b-dpo-mllm/tree/main)   | [✔️](https://huggingface.co/mllmTeam/minicpm-2b-dpo-mllm/tree/main)   |  |
| [MiniCPM 3 4B](https://huggingface.co/openbmb/MiniCPM3-4B)                     |  [✔️](https://huggingface.co/mllmTeam/minicpm3-4b-mllm/tree/main)   | [✔️](https://huggingface.co/mllmTeam/minicpm3-4b-mllm/tree/main)   |  |
| [MiniCPM MoE 8x2B](https://huggingface.co/openbmb/MiniCPM-MoE-8x2B)                     |  [✔️](https://huggingface.co/mllmTeam/minicpm-moe-8x2b-mllm/tree/main)   | [✔️](https://huggingface.co/mllmTeam/minicpm-moe-8x2b-mllm/tree/main)   |  |
| [SmolLM 1.7B](https://huggingface.co/HuggingFaceTB/SmolLM-1.7B-Instruct)                     |  [✔️](https://huggingface.co/mllmTeam/smollm-1.7b-instruct-mllm/tree/main)   | [✔️](https://huggingface.co/mllmTeam/smollm-1.7b-instruct-mllm/tree/main)   |  |
| [DCLM 1B](https://huggingface.co/TRI-ML/DCLM-1B) | [✔️](https://huggingface.co/mllmTeam/dclm-1b-mllm/tree/main)| [✔️](https://huggingface.co/mllmTeam/dclm-1b-mllm/tree/main)| |
| [OpenELM 1.1B](https://github.com/apple/corenet/tree/main/projects/openelm) | [✔️](https://huggingface.co/mllmTeam/openelm-1.1b-mllm/tree/main)| [✔️](https://huggingface.co/mllmTeam/openelm-1.1b-mllm/tree/main)| |
[PhoneLM 1.5B](https://github.com/UbiquitousLearning/PhoneLM) | [✔️](https://huggingface.co/mllmTeam/phonelm-1.5b-mllm/tree/main)| [✔️](https://huggingface.co/mllmTeam/phonelm-1.5b-mllm/tree/main)| [✔️](https://huggingface.co/mllmTeam/phonelm-1.5b-mllm/tree/main)|

### Multimodal models

| Model                                                                       | CPU <br> FP32 | CPU <br> INT4  | Hexagon NPU <br> INT8 |
|-----------------------------------------------------------------------------|------|-----|----------------------------|
| [Fuyu 8B](https://www.adept.ai/blog/fuyu-8b)                                | [✔️](https://huggingface.co/mllmTeam/fuyu-8b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/fuyu-8b-mllm/tree/main)   |  
| [Vision Transformer](https://github.com/google-research/vision_transformer) | [✔️](https://huggingface.co/mllmTeam/vit-base-patch16-224-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/vit-base-patch16-224-mllm/tree/main)   | 
| [CLIP](https://github.com/openai/CLIP)                                      | [✔️](https://huggingface.co/mllmTeam/clip-vit-base-patch32-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/clip-vit-base-patch32-mllm/tree/main)   |
| [ImageBind](https://github.com/facebookresearch/ImageBind) (3 modalities)   | [✔️](https://huggingface.co/mllmTeam/imagebind_huge-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/imagebind_huge-mllm/tree/main)   | 
| [LLaVA 7B](https://github.com/haotian-liu/LLaVA)                            | [✔️](https://huggingface.co/mllmTeam/llava-1.5-7b-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/llava-1.5-7b-mllm/tree/main)   |
| [Phi-3-Vision](https://huggingface.co/microsoft/Phi-3-vision-128k-instruct)                            | [✔️](https://huggingface.co/mllmTeam/phi-3-vision-instruct-mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/phi-3-vision-instruct-mllm/tree/main)   |
| [Qwen2-VL 2B](https://github.com/QwenLM/Qwen2-VL)                            | [✔️](https://huggingface.co/mllmTeam/qwen-2-vl-2b-instruct--mllm/tree/main)  | [✔️](https://huggingface.co/mllmTeam/qwen-2-vl-2b-instruct--mllm/tree/main)   | ✔️ |


## Quick Start

### Get the Code

```bash
git clone https://github.com/UbiquitousLearning/mllm
cd mllm
git submodule update --init --recursive \
  third_party/googletest \
  mllm/backends/cpu/third_party/kleidiai
```

### Check prerequisites

Building mllm requires following tools:

- gcc(11.4+) / clang (11.0+)
- CMake >= 3.18
- Android NDK Toolchains >= 26


> Note that building OpenMP libs on macOS may fail due to Apple LLVM compiler, so we disable OpenMP on macOS by default, you may experience slower performance on macOS. Build mllm is more recommended on Linux.

### Run Qwen with Hexagon NPU accelerating using QNN

*`NOTE:` The QNN backend is preliminary version which can do end-to-end inference. It is still under active development for better performance and more supported models.*

We support running several Qwen family models including Qwen-2-vl using [Qualcomm QNN](https://www.qualcomm.com/developer/software/qualcomm-ai-engine-direct-sdk) to get Hexagon NPU acceleration on devices with Snapdragon 8 Gen3. The details of QNN environment set up and design is [here](./mllm/backends/qnn/README.md). The prefilling stage is performered by QNN & CPU, and the inference stage is performed by CPU.

Specifically, we support the following models (similar architecture models are also supported):
- Qwen 1.5 1.8B (demo_qwen_npu, demo_qwen_pipeline)
- Qwen 2.5 1.5B (demo_qwen_npu, demo_qwen_pipeline)
- Qwen 2 VL (demo_qwen2_vl_npu and demo_qwen2_vl_npuvit)

Build the target with QNN backend.

```bash
cd ../script
./build_qnn_android.sh
```

Download the model from [here](https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm/blob/main/), or using the following instructions to download the model. You can also export Pytorch models for QNN backend with int8 weight quantization and apply rotation quantization. Details can be found in backend specific [README](./mllm/backends/qnn/README.md).

```bash
mkdir ../models && cd ../models
# Download int8 model used by npu & q4k model used by cpu
wget https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm/resolve/main/qwen-1.5-1.8b-chat-int8.mllm?download=true  -O qwen-1.5-1.8b-chat-int8.mllm
wget https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm/resolve/main/qwen-1.5-1.8b-chat-q4k.mllm?download=true  -O qwen-1.5-1.8b-chat-q4k.mllm
```

Currently, QNN backend uses models with W8A8 or W8A16 quantization. (It is determined by Quantize & Dequantize ops in modeling class, you can refer to `mllm/models/qwen/modeling_qwen_npu_v2.hpp` for more details.)

Run on an android phone with at least 16GB of memory as building the QNN graphs on device will consume a lot of memory. After building and saving QNN graphs to qnn_context.bin, the runtime memory usage will meet the expectation. The `demo_qwen_pipeline.cpp` will show the pipeline parallel execution for QNN models, which will nearly has 1.5x speedup compared with the original execution.

```bash
cd ../script
./run_qwen_qnn.sh
```

Result are as followed:

```
> ./demo_qwen_npu
[Q] <|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Give me a short introduction to large language model.<|im_end|>
<|im_start|>assistant

[A] A short introduction to a large language model is a type of artificial intelligence language model that is designed to understand and generate human language text. These models are typically trained on large amounts of text data, such as books, articles, and other written materials, to learn the patterns and structures of human language. They use a combination of natural language processing (NLP)
```

### Run with the CPU of Android

#### Build

  ```bash
  export ANDROID_NDK=/path/to/your/ndk
  cd scripts
  ./build_android.sh
  ```

#### Run Fuyu-8B

Download the model from [here](https://huggingface.co/mllmTeam/fuyu-8b-mllm/tree/main/), or using the following instructions

```bash
mkdir ../models && cd ../models
# Download fuyu-8b-q4_k.mllm
wget https://huggingface.co/mllmTeam/fuyu-8b-mllm/resolve/main/fuyu-8b-q4_k.mllm?download=true  -O fuyu-8b-q4_k.mllm
```

Run on an android phone with at least 12GB of memory.

```bash
cd ../script
./run_fuyu.sh
```

Result are as followed:

```
> ./demo_fuyu
[Q] [../assets/bus.png]Generate a coco-style caption.

[A]  A blue bus driving down▁the▁road next▁to a sidewalk.
[Q] [../assets/two_cats.jpg]What's this?

[A]  Two cats laying on▁top▁of a pink blanket.
```

#### Run LLaMA-2-7B

Download model from [here](https://huggingface.co/mllmTeam/llama-2-7b-mllm/tree/main/), or using the following instructions

```bash
mkdir ../models && cd ../models
# Dowload llama-2-7b-chat-q4_k.mllm
wget https://huggingface.co/mllmTeam/llama-2-7b-mllm/resolve/main/llama-2-7b-chat-q4_k.mllm?download=true  -O llama-2-7b-chat-q4_k.mllm
```

Run on an android phone with at least 12GB of memory.

```bash
cd ../script
./run_llama.sh
```

Result are as followed:

```
> ./demo_llama
[Q]  Hello, who are you?
[A]

I am a bot, I'm here to help answer your questions and provide information. I'm just an AI, I don't have personal experiences or feelings like humans do, but I'm here to help you with any questions you may have. Is there something specific you would like to know or talk about?
[Q]  What can you do?
[A]
I can help with a wide range of tasks, including:
  
* Answering questions on various topics, such as science, history, technology, and more.
* Providing information on different subjects, such as culture, entertainment, and lifestyle.
* Helping with language-related tasks, such as translating text or improving grammar and syntax.
* Generating text, such as articles, stories, or even entire books.
* Assisting with coding
[Q]  Please introduce Beijing University of Posts and Telecommunications.
[A]
Beijing University of Posts and Telecommunications (BUPT) is a public research university located in Beijing, China. It was established in 1955 and is one of the top universities in China, with a strong focus on engineering, technology, and telecommunications.
BUPT offers a wide range of undergraduate and graduate programs in fields such as computer science, electrical engineering, software engineering, and communication engineering. The university
```

#### Run ImageBind

Download model from [here](https://huggingface.co/mllmTeam/imagebind_huge-mllm/tree/main), or using the following instructions

```bash
mkdir ../models && cd ../models
# Download imagebind_huge-q4_k.mllm
wget https://huggingface.co/mllmTeam/imagebind_huge-mllm/resolve/main/imagebind_huge-q4_k.mllm?download=true -O imagebind_huge-q4_k.mllm 
```

Run on an android phone with at least 4GB of memory.

```bash
cd ../script
./run_imagebind.sh
```

Result are as followed:
```
> ./demo_imagebind 
vision X text :
0.9985647 0.0013827 0.0000526 
0.0000365 0.9998636 0.0000999 
0.0000115 0.0083149 0.9916736 
vision X audio :
0.8054272 0.1228001 0.0717727 
0.0673458 0.8429284 0.0897258 
0.0021967 0.0015335 0.9962698 
```


### Run for Linux

#### Build
```bash
cd scripts
./build.sh
 ```

#### Run Fuyu-8B

```bash
cd ./bin
./demo_fuyu -m ../models/fuyu-8b-q4_k.mllm -v ../vocab/fuyu_vocab.mllm
 ```

#### Run LLaMA-2-7B

```bash
cd ./bin
./demo_llama -m ../models/llama-2-7b-chat-q4_k.mllm -v ../vocab/llama2_vocab.mllm
```


#### Run ImageBind

```bash
cd ./bin
./demo_imagebind -m ../models/imagebind_huge-q4_k.mllm -v ../vocab/clip_vocab.mllm
```


## Customization

### Convert models

You can download models from [here](https://huggingface.co/mllmTeam), or you can convert a pytorch/safetensor model to
mllm model by yourself.

```bash
cd tools/convertor
pip install -r ./requirements.txt

# for one file pytorch model
python converter.py --input_model=model.pth --output_model=model.mllm --type=torch

# for multi-file pytorch model
python converter.py --input_model=pytorch_model.bin.index.json --output_model=model.mllm --type=torch

# for one file safetensor model
python converter.py --input_model=model.bin --output_model=model.mllm --type=safetensor

# for multi-file safetensor model
python converter.py --input_model=model.safetensors.index.json --output_model=model.mllm --type=safetensor
``` 

### Convert vocabulary

You can convert vocabulary to mllm vocabulary as followed.

```bash
cd tools/convertor
python vocab.py --input_file=tokenizer.json --output_file=vocab.mllm --type=BPE
```

### Quantize models

You can quantize mllm model to int4 model by yourself.
mllm only support two quantize modes: Q4_0 and Q4_K.

```bash
cd bin
./quantize model.mllm model_q4_k.mllm Q4_K
```

## Roadmap

- More backends like QNN
- More models like PandaGPT
- More optimizations like LUT-GEMM
- [More..](https://ubiquitouslearning.github.io/mllm_website/roadmap/roadmap/)

## Documentation

See the [documentation](https://ubiquitouslearning.github.io/mllm_website/introduction/getstarted/) here for more
information

## Contribution

Read the [contribution](https://ubiquitouslearning.github.io/mllm_website/contributing/contributing/) before you
contribute.

## Acknowledgments

mllm reuses many low-level kernel implementation from [ggml](https://github.com/ggerganov/ggml) on ARM CPU.
It also utilizes [stb](https://github.com/nothings/stb) and [wenet](https://github.com/wenet-e2e/wenet) for
pre-processing images and audios.
mllm also has benefitted from following projects: [llama.cpp](https://github.com/ggerganov/llama.cpp)
and [MNN](https://github.com/alibaba/MNN).

## License

### Overall Project License

This project is licensed under the terms of the MIT License. Please see the [LICENSE](LICENSE) file in the root
directory for the full text of the MIT License.

### Apache 2.0 Licensed Components

Certain component([wenet](https://github.com/wenet-e2e/wenet)) of this project is licensed under the Apache License 2.0.
These component is clearly identified in their respective subdirectories along with a copy of the Apache License 2.0.
For the full text of the Apache License 2.0, please refer to the [LICENSE-APACHE](third_party/wenet_audio/LICENSE) file
located in the relevant subdirectories.

## Citation
```
@article{xu2025fast,
  title={Fast On-device LLM Inference with NPUs},
  author={Xu, Daliang and Zhang, Hao and Yang, Liming and Liu, Ruiqi and Huang, Gang and Xu, Mengwei and Liu, Xuanzhe},
  booktitle={International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)},
  year={2025}
}
@misc{yi2023mllm,
  title = {mllm: fast and lightweight multimodal LLM inference engine for mobile and edge devices},
  author = {Rongjie Yi and Xiang Li and Zhenyan Lu and Hao Zhang and Daliang Xu and Liming Yang and Weikai Xie and Chenghua Wang and Xuanzhe Liu and Mengwei Xu},
  year = {2023},
  publisher = {mllm Team},
  url = {https://github.com/UbiquitousLearning/mllm}
}
```


