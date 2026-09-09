QNN AOT Execution Flow
================================================================

.. note::
   Please refer to the `Environment Setup <setup_env.html>`_ documentation to configure the QNN and Hexagon SDK environments before proceeding.

This document aims to explain the main execution flow of QNN AOT (Ahead-of-Time). This implementation is designed to fully leverage the offline compilation capabilities of the Qualcomm QNN framework to achieve efficient inference of fully integer-quantized Large Language Models (LLMs) on mobile devices, which is the de facto workflow for LLM execution on the Hexagon NPU.

Specifically, our implementation employs a W4A16 quantization scheme. The Key-Value (KV) Cache is quantized to ``uint8``, and the linear weights are quantized using Low-Power Blockwise Quantization (LPBQ).

The implementation of this module was inspired by the `PyTorch ExecuTorch`_ project, especially its `Hybrid Execution Mode`_ designed for the Qualcomm backend, for which we are grateful.

.. _PyTorch ExecuTorch: https://pytorch.org/executorch/
.. _Hybrid Execution Mode: https://github.com/pytorch/executorch/blob/main/examples/qualcomm/oss_scripts/llama/README.md

Overall Flow
----------------------------------------------------------------

The QNN AOT execution flow is mainly divided into three stages:

1.  **Model Quantization and Export (Python)**: On the host machine, a Python script is used to quantize the pre-trained floating-point model and export it to ``.safetensor`` file. The ``.safetensor`` is then converted to ``.mllm`` file using mllm-convertor.
2.  **Offline Compilation (C++)**: On the host machine, a C++ compiler program loads the ``.mllm`` file, invokes the QNN toolchain for model compilation, graph optimization, and quantization parameter adjustment, and finally generates a QNN Context Binary.
3.  **On-Device Execution (C++)**: On the target device (e.g., a mobile phone), the AOT runner program loads the pre-compiled context binary and executes inference.


Detailed Steps
----------------------------------------------------------------

Taking ``qwen3_qnn_aot`` as an example, the detailed steps are as follows.

1. **Model Quantization and Export**

   First, we need to run a Python script on the host to quantize the model and export it as a ``.safetensors`` file.

   .. code-block:: shell

      cd ./pymllm/backends/qualcomm/transformers/qwen3
      python train.py --model_path "/your/qwen3/model/path/" --max_length 1024 --num_samples 128 --output_dir "/path/to/output"

   This step generates a key file:

   *   ``model.safetensors``: The quantized model file, saved in the specified output directory.

   Next, convert the exported ``.safetensors`` model to the MLLM format (``.mllm``) using the ``mllm-convertor`` script.

   .. note::
      Before using ``mllm-convertor``, you need to install the ``pymllm`` package. You can install it using one of the following methods:

      **Standard Installation:**

      .. code-block:: shell
         
         bash ./scripts/install_pymllm.sh

      **Editable Installation (for development):**

      .. code-block:: shell

         # In the mllm project root directory
         pip install -e .

         # link lib to pymllm's dir, so that tvm ffi can find the lib
         # 
         # NOTE:! build x86 qualcomm aot first !
         source <absolute path to where you install qnn>/bin/envsetup.sh
         python task.py tasks/build_x86_qnn_aot.yaml
         ln -s <absolute path to where you build mllm>/bin/ mllm/pymllm/lib


   .. note::
      1. The ``--pipeline`` option is not required for converting models in this document.
      2. The ``--verbose`` option is used to print verbose output. It is recommended to use it for debugging.

   .. code-block:: shell

      mllm-convertor --input_path /path/to/output/model.safetensors --output_path /path/to/output/qwen3_1.7b.mllm --verbose

   This will generate the ``qwen3_1.7b.mllm`` file, which will be used in the subsequent compilation step.

2. **Offline Compilation to Generate QNN Context**

   Next, we use a C++ compiler program (``compile.cpp``) on the host to generate the QNN context. This process invokes the QNN SDK to convert the MLLM IR into a QNN-supported format and performs optimizations.

   Compile and run the ``compile`` program:

   .. code-block:: shell

      # In the mllm-v2 project root directory
      source <absolute path to where you install qnn>/bin/envsetup.sh
      python task.py tasks/build_x86_qnn_aot.yaml

      # Run the compiler program
      ./build-qnn-aot/bin/mllm-qwen3-aot-sha-c \
      -m /path/to/output/qwen3_1.7b.mllm \
      -c ./examples/qwen3_qnn_aot/config_1.7B.json \
      --aot_config ./examples/qwen3_qnn_aot/qnn_aot_cfg_1.7B.json
      # Optional, default value is /opt/qcom/aistack/qairt/2.41.0.251128/lib/x86_64-linux-clang/
      # --qnn_env_path path/to/qnn_sdk.


   This program reads the ``.mllm`` model file and the quantization recipe, and finally generates a QNN context binary file named ``qwen3-1.7B-lpbq-sha.bin``. This file contains all the information needed to execute inference on the target device.

   .. note::
      The ``HtpSignedPd`` config in qnn_aot_cfg_1.7B.json will specify ``QNN_HTP_DEVICE_CONFIG_OPTION_SIGNEDPD`` during QNN initialization, which may cause an "Unsupported config option 2" error in older QNN versions. It is recommended to change the config in the json file to ``HtpUnsignedPd``.

3. **On-Device AOT Inference**

   Finally, we push the generated ``qwen3-1.7B-lpbq-sha.bin`` file and other resources like the tokenizer to the target device. The on-device AOT runner program (``aot_run.cpp``) will load this binary file and execute inference.

   Compile and run the ``aot_run`` program:

   .. code-block:: shell

      # Cross-compile the aot_run program for the target device (e.g., Android)
      python task.py tasks/build_android_qnn.yaml

      # Push compiled context file to the device
      adb push qwen3-1.7B-lpbq-sha.bin /data/local/tmp/
      
      # Push QNN libraries and Op Packages
      ANDR_LIB=$QNN_SDK_ROOT/lib/aarch64-android
      OP_PATH=mllm/backends/qnn/custom-op-package/LLaMAPackage/build

      adb push $ANDR_LIB/libQnnHtp.so /data/local/tmp
      adb push $ANDR_LIB/libQnnHtpV75Stub.so /data/local/tmp
      adb push $ANDR_LIB/libQnnHtpPrepare.so /data/local/tmp
      adb push $ANDR_LIB/libQnnHtpProfilingReader.so /data/local/tmp
      adb push $ANDR_LIB/libQnnHtpOptraceProfilingReader.so /data/local/tmp
      adb push $ANDR_LIB/libQnnHtpV75CalculatorStub.so /data/local/tmp
      adb push $QNN_SDK_ROOT/lib/hexagon-v75/unsigned/libQnnHtpV75Skel.so /data/local/tmp
      adb push $QNN_SDK_ROOT/lib/aarch64-android/libQnnSystem.so /data/local/tmp

      adb push $OP_PATH/aarch64-android/libQnnLLaMAPackage.so /data/local/tmp/libQnnLLaMAPackage_CPU.so
      adb push $OP_PATH/hexagon-v75/libQnnLLaMAPackage.so /data/local/tmp/libQnnLLaMAPackage_HTP.so

      # Push mllm runner and libs to device
      adb push build-android-arm64-v8a-qnn/bin/*.so /data/local/tmp
      adb push build-android-arm64-v8a-qnn/bin/mllm-qwen3-aot-runner /data/local/tmp

      # Execute on the device
      adb shell "cd /data/local/tmp && export LD_LIBRARY_PATH=. &&
      ./mllm-qwen3-aot-runner -m qwen3-1.7B-lpbq-sha.bin
      -t qwen3-tokenizer.json -c config_1.7B.json --ar_len 32"

   The AOT runner program loads the ``.bin`` file to initialize the QNN context, then receives input tokens, performs model inference, and outputs the next token, thus realizing the language model generation process.

Hybrid Mode Explanation
----------------------------------------------------------------

Our QNN AOT implementation adopts a Hybrid mode similar to `executorch` to optimize the efficiency of Prompt processing and Token generation.

*   **Prefill Phase**: When processing the user's input (Prompt) for the first time, the model calculates and caches the Key-Value (KV) states for all input tokens at once. This phase is computationally intensive but is performed only once.
*   **Decode Phase**: When generating subsequent tokens, the model takes only the previously generated token as input and uses the cached KV state for computation. This process is computationally light and fast, suitable for token-by-token generation.

In this way, we combine the advantages of batch processing and stream processing to improve overall throughput while ensuring low latency.
