# 实验10-8：正式小模型闭环协议

## 边界与冻结版本

目标是两个真实verl更新步骤、参数/梯度/optimizer证据、受支持的权重交接与再次rollout。主任务的退化本身必须保留；独立控制检验非零学习，不作模型质量结论。V4训练、论文跨session最终审计、恢复/抢占/异步/长尾/归一化变体不在本批。

verl固定 `d040717b21af2e23e8e789a3e354cff2394ae2de`，官方main_ppo → use_v1=false的main_ppo_v0 → RayPPOTrainer → FSDPEngine。该commit的v0入口有deprecated警告，但核心advantage/loss/backward/optimizer均使用真实官方实现。私有观测patch只保存batch/metrics/代表张量，并将权重IPC路径移入私有目录；完整diff及原SHA随交付。

Python3.12.13、Torch2.11.0+cu130、vLLM0.24.0、Transformers5.9.0、Ray2.55.1；按官方uv.lock安装，再显式覆盖NumPy为2.3.5以满足mistral-common的<2.4声明。原锁不改，numpy-override.json固定官方wheel URL/SHA，完整实际freeze及依赖检查另存。共享vLLM0.23/SG环境保持原样。

真实公开模型 `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775`，全文件SHA固定，模型仅留远端。RTX PRO6000 SM120，CUDA13私有工具链；FSDP world_size1自动NO_SHARD，不宣称分片性能。官方SDPA配置、use_remove_padding=false；不以自写CPU scheduler代替CUDA流程。

## 主任务与独立控制

四题固定顺序：1+1→2、7+8→15、12-5→7、3*4→12。用户提示模板：`Compute {expression}. Reply with only the integer answer.`，模型原始chat template，无system prompt。训练集为四题重复两遍，每步四prompt，每prompt两次采样，共每步8回答、2步；不洗牌、不筛样。seed42、temperature1、top_p1、top_k-1、prompt≤128、response≤16、保留EOS。

主任务用GRPO；只对去首尾空白的完整回答等于标准整数字符串给1，其余0。不删除错误回答、全同reward、零advantage或零梯度。两步结果不作为质量提升证据。

独立控制的固定定义在首次完成主任务rollout和观察其奖励之前已登记。按相同四题为非空回答分别给[+1,-1,+1,-1]，空回答0，符号不依赖正确率或生成内容。控制从相同原始预训练模型重新开始，使用官方reinforce_plus_plus；由verl计算、归一化advantage并训练，不手填advantage、不自写optimizer。相同采样、batch和学习率。若主任务退化，在独立控制中检验非零梯度/参数变化；即使控制退化也保留全量结果，不修改符号制造成功。控制奖励和算术正确率分开分析，官方日志将reward叫acc不表示它是正确率。

## 训练与同步

FP32 master参数/bf16混精、FSDP、use_orig_params=true、gradient checkpointing；mini_batch4、micro_batch_per_gpu1、ppo_epochs1、lr1e-5、KL和entropy系数0，不启动critic/reference。完整生效Hydra overrides随每次运行保存。

vLLM TP1、eager、safetensors真实加载、free_cache_engine=true、gpu_memory_utilization0.035、max_model_len144、max_num_batched_tokens144、max_num_seqs8、权重bucket32MiB。超bucket张量使用官方CUDA IPC direct-send；不假设同设置可用于SHM fallback。

每步保存实际tokens、rollout与重算logprobs、mask、reward、advantage，以及optimizer前后完整embedding摘要和代表参数/梯度/optimizer切片。发送端对同步张量转换BF16后计算SHA；接收端在真正model.load_weights后读取实际embedding计算SHA。需按时间/版本匹配0/1/2，不能仅凭RPC返回证明身份，也不能把代表张量验证扩大为全模型逐参数验证。

第二次更新后运行固定四题验证集，n1、相同温度，保存原始tokens/logprobs/奖励。训练批次与验证批次分别记录，控制和主任务分别封存。

## 资源、时间与封存

自身全部GPU进程采样合计≤16GiB；自身全进程树RSS≤24GiB，含supervisor；CPU12–15、库线程4。每批启动GPUfree≥10GiB、MemAvailable≥16GiB，持续监控MemAvailable下限。每批≤1200秒，私有新增磁盘≤25GiB（24GiB预留停止线），本地交付≤150MiB。watchdog按唯一环境token和PID出生时间追踪/清理自己的所有进程，不global ray stop、不碰其他服务/OpenROAD。

私有Ray GCS6398、worker16400–16499，temp/session与IPC在tools/verl-private；启动时拒绝已有端口，不能连入他人集群。固定RayParams/Node启动adapter只处理私有会话。采样不是硬隔离，任何越限如实记录；不能声称采样峰值等于瞬时峰值。

使用共享GPU与已准备的私有JIT缓存，不reset共享缓存。初始化、实际框架阶段计时、观测hash/落盘开销分开记录；不可声称冷启动、隔离性能或V4/H20/H100/B200训练。作业和传输退出后才做离线结果分析与图QA。

成功门槛：主任务真实完成2次官方更新调用及最终rollout；主任务或独立控制至少2次可复核非零参数变化、梯度/optimizer状态，版本1/2真实接收和再次rollout。全部科学负结果保留。成功后清理被替代的启动/依赖排障attempt及日志，最终仅保留最后正式主任务/控制与必要源码、版本、协议，不把诊断失败历史放入最终交付。
