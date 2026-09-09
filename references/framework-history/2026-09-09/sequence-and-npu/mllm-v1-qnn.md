# Qualcomm AI Engine Direct(QNN/QAIRT) backend

QNN Backend has supported running 1-3B LLMs and VLMs with full NPU vision encoder offload. Due to the memory constraint of online computation graph building, larger models may not be supported. Also, the QNN backend currently only speedups the prefilling stage of the LLM, thus needing another CPU model to do the decoding stage. Future support for QNN graph switching and decoding is under development. 

Below describes how to set up the QNN environment, compile the QNN op package, convert the model, build and run the project with QNN backend.

## QNN Environment Set Up
This section is basically following the QNN documentation, for more details, see: [QNN Linux Setup](https://docs.qualcomm.com/bundle/publicresource/topics/80-63442-50/linux_setup.html).
The QNN backend relies on the Qualcomm QNN SDK and Hexagon SDK to compile QNN Backends and LLM-specific operators. The QNN SDK can be downloaded [here](https://www.qualcomm.com/developer/software/qualcomm-ai-engine-direct-sdk). The Hexagon SDK can be downloaded using [QPM](https://qpm.qualcomm.com/). The compiling environment only supports Linux now.

Version requirements:
* QNN: [Linux v2.34+](https://qpm.qualcomm.com/#/main/tools/details/qualcomm_neural_processing_sdk)
* Hexagon SDK: [Linux 5.x](https://qpm.qualcomm.com/#/main/tools/details/HexagonSDK5.x)  (Some accounts may have no permission to access this SDK and may need to contact Qualcomm for support.)

**NOTE:** After downloading the QNN SDK, unzip the file and move the folder name like `qairt/v2.34.0.250424` to `mllm/backends/qnn/` and rename the version to 'sdk'. The folder structure should be like `mllm/backends/qnn/sdk`.

After downloading and installing the two SDKs use "qpm-cli", set up the sdk environment by running the following commands:

```bash
source <path-to-qnn-sdk>/bin/envsetup.sh
source <path-to-hexagon-sdk>/setup_sdk_env.source
```

After setting up the environment, you will have following ENV variables:

* QNN_SDK_ROOT=/path/to/your/qnn/sdk
* HEXAGON_SDK_ROOT=/path/to/your/hexagon/sdk

## Op Package Compile

To use QNN offload, the CPU & HTP QNN op package are needed, the following scripts will build QNN op package needed by the project. `QNN_SDK_ROOT`, `HEXAGON_SDK_ROOT` and `ANDROID_NDK_ROOT` should be set in the environment.

```bash
cd mllm/mllm/backends/qnn/LLaMAOpPackageHtp/LLaMAPackage/
make htp_aarch64 && make htp_v75
```

## Model Conversion

The model used by QNN prefilling is in int8 format, with static per-tensor quantization. We have two techniques to improve the accuracy of the model:

**Shadow Outlier Execution**: This technique selectively preserves the precision of specific layers by identifying outlier activations and applying a threshold-based selection (using `t01m_clip_threshold`, which refers to the activation scale threshold after removing the top 0.1% outliers compared to the original scale). By doing so, it accelerates computation on low-precision NPUs while minimizing accuracy loss.

![Shadow Execution](../../../assets/shadow_execution.png)

**Rotation**: Rotation quantization is a technique used to improve model quantization performance by applying rotational transformations to model weights and activations before quantization. This reduces quantization error and improves the accuracy of quantized models.

The rotation quantization process is an implementation of [SpinQuant](https://arxiv.org/abs/2405.16406) and [QuaRot](https://arxiv.org/abs/2404.00456) for different models like Qwen. We are not intented to do exactly the same things as SpinQuant and QuaRot, instead we provide a framework to customize rotation operations for any models you want to use.

![Rotation](../../../assets/rotation.png)

The tools are under `tools/qnn_convertor` and `tools/rotation`. Below describes the usage of the tools.

The quantization process consists of three main steps:

1. Profile Activation Distributions: Collect statistical information about layer activations and generate rotation matrices
2. Export QNN Model: Quantize the model using collected statistics and export in QNN-compatible format
3. Export FP32 Rotated Model: Export the rotated FP32 model for CPU deployment

Use the get_distribution.py script to collect activation distribution information and generate rotation matrices:

```bash
# under tools/qnn_convertor
python get_distribution.py --config_file config/qwen1.5-1.8b.json
```

The profiling step requires a representative dataset to collect activation statistics.
In our example configuration:
```json
"profile_config": {
    "dataset_path": "path/to/pile-val-backup/",
    ...
}
```
we use a subset of The Pile dataset (pile-val-backup).
The original hosting site for The Pile (the-eye.eu) has permanently removed the dataset due to copyright concerns.
You can use an uncopyrighted subset of The Pile as a drop-in replacement, which is available on HuggingFace:[HuggingFace: pile-uncopyrighted](https://huggingface.co/datasets/monology/pile-uncopyrighted).

Example configuration file (config/qwen1.5-1.8b.json):
```json
{
    "profile_config": {
        "dataset_path": "path/to/pile-val-backup/",
        "output_path": "./dis/qwen1.5-1.8b-rot-dis.json",
        "num_samples": 2,
        "no_bias": true,
        "model_config": {
            "model_type": "qwen2",
            "tokenizer_name": "path/to/Qwen1.5-1.8B-Chat",
            "model_name": "path/to/Qwen1.5-1.8B-Chat",
            "online_rotation": true,
            "random_rotate": true,
            "save_rotation": "./R/qwen1.5-1.8b-rotation-matrix.bin",
            "R_path": "see explanation below"
        }
    },
    ...
}
```

Key parameters:

- dataset_path: Path to the dataset used for analysis
- output_path: Path to save activation distribution information
- num_samples: Number of samples to analyze
- no_bias: Whether to ignore bias terms
- online_rotation: Whether to rotate the model online(rotate after loading model). Note that `online_rotation` should be set to true if we are going to convert an original model that has not been rotated. Otherwise, `online_rotation` should be set to false.
- random_rotate: Whether to use random rotation matrices
- save_rotation: Path to save rotation matrices
- R_path:  Path to predefined rotation matrix. When specifying the rotation matrix, `random_rotate` and `R_path` are mutually exclusive

Use export_qnn_model.py to export the quantized QNN model:
```bash
python export_qnn_model.py --config_file config/qwen1.5-1.8b.json
```

The export_config section in the configuration file:
```json
{
    ...
    "export_config": {
        "scale_file": "./dis/qwen1.5-1.8b-rot-dis.json",
        "output_model": "./models/qwen1.5-1.8b-qnn.bin",
        "t01m_clip_threshold": 64,
        "quant_bias": false,
        "model_config": {
            "model_type": "qwen2",
            "tokenizer_name": "path/to/Qwen1.5-1.8B-Chat",
            "model_name": "path/to/Qwen1.5-1.8B-Chat",
            "online_rotation": true,
            "R_path": "./R/qwen1.5-1.8b-rotation-matrix.bin"
        }
    }
}
```
Key parameters:

- scale_file: Path to activation distribution file
- output_model: Output model path
- t01m_clip_threshold: Quantization clipping threshold
- quant_bias: Whether to quantize bias terms
- online_rotation: rotate after loading model
- R_path: Path to predefined rotation matrix

To export an FP32 rotated .pth model for CPU deployment (still using CPU for decoding, which requires the FP32 rotated model) and performing CPU quantization methods use:

```bash
python export_rotate_model.py --config_file config/qwen1.5-1.8b.json
```

`NOTE` It's recommended to set a new output model path in json file to avoid overwriting the exported .pth model for QNN.

Now you can convert the int8 .pth model to .mllm format:

```bash
python converter.py --input_model=model.pth --output_model=model.mllm --type=torch
```

## Build & Run

Example to modify demo_qwen_npu.cpp:
```cpp
{
    ...
    cmdParser.add<string>("vocab", 'v',  "specify mllm tokenizer model path", false, "path/to/qwen_vocab.mllm");
    cmdParser.add<string>("merge", 'e',  "specify mllm merge file path", false, "path/to/qwen_merges.txt");
    cmdParser.add<string>("qnn-model", 'm', "specify mllm model path", false, "path/to/qwen-1.5-1.8b-chat-int8.mllm");
    cmdParser.add<string>("decoding-model", '\0', "specify mllm model path", false, "path/to/qwen-1.5-1.8b-chat-q4k.mllm");
    ...
    auto tokenizer = QWenTokenizer(vocab_path, merge_path);
    QWenNPUConfig config(tokens_limit, "1.8B-rotated", RoPEType::HFHUBROPE);
    auto model = v2::QWenForCausalLM_NPU(config, 256);
    ...
}

```
Build the target with QNN backend.

```bash
cd ../scripts
./build_android_qnn.sh
```

Currently, there are two style of modeling, the Module API and the old implementation. The demo of the Module API is in `examples/demo_qwen_npu.cpp` which is in a **user friendly style**, and the old implementation is in `examples/main_qwen_npu.cpp` which supports **the chunk pipeline prefilling**.

Download the model from [here](https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm/blob/main/), or using the following instructions

```bash
mkdir ../models && cd ../models
# Download int8 model used by npu & q4k model used by cpu
wget https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm/resolve/main/qwen-1.5-1.8b-chat-int8.mllm?download=true  -O qwen-1.5-1.8b-chat-int8.mllm
wget https://huggingface.co/mllmTeam/qwen-1.5-1.8b-chat-mllm/resolve/main/qwen-1.5-1.8b-chat-q4k.mllm?download=true  -O qwen-1.5-1.8b-chat-q4k.mllm
```

Run on an android phone with at least 16GB of memory.

```bash
cd ../scripts
./run_qwen_qnn.sh
```
If you modify or re-export the model, make sure to delete the old cache file (qnn_context.bin) on your device before running the script again. The cache will be automatically regenerated.

Result are as followed:

```
> ./demo_qwen_npu
[Q] <|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Give me a short introduction to large language model.<|im_end|>
<|im_start|>assistant

[A] The large language model is a type of artificial intelligence that is designed to generate human-like text based on the input it receives It is typically trained on large datasets of text, such as books, articles, and web pages, and uses statistical models to learn patterns and relationships in the data The goal of a large language model is to generate text that is coherent
```

## Custom Op Package Development

In QNN, you can develop your own Op package to support custom operators. The Op package is a collection of QNN operators that can be used in the QNN backend.

If you want to develop your own QNN Op package, you can refer to the [QNN documentation](https://docs.qualcomm.com/bundle/publicresource/topics/80-63442-50/op_package_gen_example.html) for more details. The package name in this project is `LLaMAPackage`.

Generally, a QNN Op should implement an HVX version and a reference version. You can refer to 'Qualcomm Hexagon V73 HVX Programmer's Reference Manual' on Qualcomm's official website for more details about the HVX programming. 

To enable LSP for HVX, you can set clangd path to `$HEXAGON_SDK_ROOT/tools/HEXAGON_Tools/8.7.06/Tools/bin/hexagon-clangd` in your `.vscode/settings.json` file.

```json
{
  "clangd.path": "$HEXAGON_SDK_ROOT/tools/HEXAGON_Tools/8.7.06/Tools/bin/hexagon-clangd"
}
```

Then you need to generate the `compile_commands.json` file for the Op package, you can use the following command:

```bash
cd mllm/mllm/backends/qnn/LLaMAOpPackageHtp/LLaMAPackage/
compiledb make htp_v75 -C .
```
