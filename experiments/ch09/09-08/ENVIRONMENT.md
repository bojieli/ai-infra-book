# 独立运行环境与最终配置

实验专用 Python 3.10 venv：`/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv`。固定 `sglang==0.5.13.post1` 完整安装，声明依赖包含 Torch 2.11.0+cu130、sglang-kernel 0.4.3、TileLang 0.1.8；精确列表见 environment-freeze.txt。另安装 `nvidia-cuda-cccl==13.2.86` 提供 nv/target 头文件。pip check 和导入检查通过，不等于模型实验通过。

pip CUDA 13.2 工具包布局与 tvm_ffi JIT 链接器期待不同。工具包原来只有 lib/libcudart.so.13，链接器使用 CUDA_HOME/lib64 下的 -lcudart，曾实际链接系统 libcudart.so.11.0。只在专用 venv 内补两个链接：

```sh
cd /home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13
ln -s lib lib64
cd lib
ln -s libcudart.so.13 libcudart.so
```

launch.sh 固定此 CUDA_HOME、nvcc 路径与全新 TVM_FFI_CACHE_DIR，避免复用此前混合版本产物。不修改系统 CUDA、驱动或其他环境。check_runtime.py 用原 SGLang 融合 QK norm 校验 BF16 随机张量；runtime-check-v7.log 两组最大绝对误差均为零，runtime-linkage.txt 记录新链接依赖。这不是模型质量或 HiCache 正确性结论。

正式 producer-v6 与 consumer-v6 使用固定 config.json，各完成3次模型请求，summary.json 的 status 为 passed。

最终 runtime-check-v7.log 两组误差均为零。专用 CUDA 环境补齐上述两个链接并重新编译；正式启动不使用预加载或 runtime 转发库，producer-v6 使用原 config.json。

独立 ldd 的 runtime-linkage.txt 显示依赖已为 libcudart.so.13；在不加载 Python/Torch 的 shell 中该库和 libtvm_ffi 显示 not found，运行进程由 Torch/tvm_ffi 预先加载它们。数值检查与随后六次模型请求均实际成功，不把 shell ldd 当成功执行证据。
