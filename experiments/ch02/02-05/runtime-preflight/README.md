# V4-Flash 真实检索实验的运行预检

尚未运行模型或检索评测，不算2-5完成。此目录只保存已缓存权重可访问性与当前执行源码，供下一阶段选择真实运行路径；不重复calculations的状态/FLOPs/带宽预算。

RTX主机已有 DeepSeek-V4-Flash-0731 snapshot `7872f01b1d1fe23eabc4c98b48bffcef5a386062`。实际读取48个safetensors文件的header，核验72317个索引张量与各文件key一一对应、数据offset连续且文件长度精确匹配末offset；未重新下载。`results/observation.json`保存实际路径、文件长度、header SHA和原始GPU/内存快照。只验证header/offset/长度，不代表重新计算全部166GB权重载荷的SHA，也不能仅凭通过证明推理正确。

实际已安装SG0.5.13.post1源码包含V4模型、SM120 attention专用分支、CPU OffloaderV1：`cpu_offload_gb`选择逐参数主机存储，forward时把state_dict送回原device并调用functional_call。V4参数默认KV为fp8_e4m3、page_size256，所选配置不支持以统一BF16 KV作为运行参数。源码原件及SHA保存在results/sources和observation中。

这不证明V4的FP4专家、量化加载后处理、attention kernel、CPU卸载和单卡组合已通过兼容性验证。下一步仍须检查实际MoE后端与SM120、完整加载的主机/显存峰值以及受支持的卸载包装，先固定检索任务/质量门槛，再启动模型；不能用dummy/random权重替代实测。当前没有停止任何既有服务或启动V4 GPU进程。Kimi K3及同条件检索/前缀状态对照仍未完成。

执行预检会话56442 exit0，传输23777 exit0。独立运行于具有这些缓存和安装路径的远端：

```sh
python3 probe.py --out new-results
```

输出必须新建，不覆盖原结果。只读checkpoint及安装目录；仅向给定输出目录保存证据，不修改引擎、缓存或calculations。此为运行条件检查，无性能图或推理性能结论。

实际参数解析补充：`resolve_config.py`在指定私有SG环境只构造ServerArgs，未构造Engine。`resolved-config.json`记录Torch2.11.0+cu130、SG0.5.13.post1；自动选择marlin、dsv4、fp8_e4m3 KV/page256，SM120自动禁用FP8 WO-A与若干特化路径。110GiB CPU offload、context2048、token pool4096、chunk256只是解析过的候选参数，不是已验证可运行配置。五份安装源码逐一匹配pip distribution RECORD SHA；保存在config-sources。参数进程6097和传输17759均exit0。独立六专家预检见[结果](../expert-preflight/README.md)，其预设逐元素门槛有失败，不能据参数解析成功宣称完整模型兼容。

后续实际结果：原生[四层加载/卸载/前向探测](../native-layer-probe/README.md)第五次配置已完成两次短请求并exit0，修复所需缓存参数与私有CCCL头路径、前四次失败均保留。该截断模型不是完整V4，六专家既定数值门槛也未改为通过，完整检索仍待。
