你是用户授权的独立Codex CLI worker。完成V4全模型运行前的真实MXFP4专家/SM120数值兼容性预检。唯一可写 experiments/ch02/02-05/expert-preflight/、experiments/parallel-workers/v4expert/status.md，远端对应目录。其他文件只读；不改正文/inventory/PROGRESS/references/research/旧实验，calculations不执行不修改不复制、不联系其owner；不再派生agent/Codex、不git提交。

主agent正在核对完整V4的CPU offload。你负责独立有界数值实验，可与drafttrace共享GPU但显存上限3GiB、单GPU进程、CPU4线程/主存8GiB。本批不做性能排名。启动前nvidia-smi确认实际余量≥4GiB；不停止任何其他进程。禁止加载完整V4、禁止重新下载模型、禁止修改共享SG/Torch环境。已有环境 /home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python 实查Torch2.11cu130/SG0.5.13.post1；不要误用/home/ubuntu/sglang-venv。

缓存V4Flash路径 /home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/7872f01b1d1fe23eabc4c98b48bffcef5a386062。主agent已校验48文件header/index/offset（见runtime-preflight），没有全payload SHA。原权重key如 layers.0.ffn.experts.0.w1.weight/.scale、w3、w2，expert0在model-00002-of-00048.safetensors；按index查其他expert。读取layer0真实六个expert（建议0/1/7/42/128/255）并保存选取key/shape/dtype/raw SHA，不能随机权重替代。

已安装 mxfp4_marlin_moe.py 在SM120跳过Marlin repack，backend sm120_triton，实际调用 sglang.srt.layers.moe.fused_moe_triton.mxfp4_moe_sm120_triton.mxfp4_moe_forward_triton。先读完整该函数和stage kernel/scale处理/路由权重/激活clamp语义；固定源码/hash。用该未修改真实函数执行 M1/8、topk6、hidden4096/intermediate2048、固定随机小幅BF16输入及可复算路由权重，映射所选真实experts至0..5。真实全模型router/activation不在本预检范围，必须明确合成输入/路由。

执行前写PROTOCOL：独立CPU参考按FP4 E2M1显式16值表与E8M0标量解包，CPU FP64矩阵计算，按实际原内核存储边界round BF16；独立实现clamp/SwiGLU/加权reduce，不调用被测GPU函数作参考。预设可解释的逐元素门槛与relative-L2，保持不随失败放宽；保存所有误差/失败。增加单expert选择/置零权重等能识别routing/combine错误的必要控制，但不要制造海量测试。重点核对真实checkpoint尺度格式/排列，避免使用错layout后误判内核。小形状smoke后才完整实际专家形状。

输出完整真实input/packedweight/scales/output/reference、源hash、环境/peakGPU/运行和退出。若重排CPU权重用于原函数，记录实际张量布局/转换。允许一个独立torch profiler记录原函数实际kernel，性能只观测不排名。可进一步对该同一小层使用官方OffloaderV1验证CPU→GPU包装后相同输入输出（先认真读接口），但不要加载全V4；如不支持保留具体报错。不要patch共享框架或把自己实现reference当真实引擎。

原始数据本地≤500MiB（若全FP64reference大，输入输出必要文件优先，参考可从packed文件独立复算）；传输exit后再分析。standalone run/analyze/README、必要图QA与明示未完成全模型/检索质量/其他算子；只做这项有界预检，不做最终跨session审计。先写status并持续更新，完成后交主agent统一审核。
