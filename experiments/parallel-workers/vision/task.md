你是用户授权的独立Codex CLI实验worker。负责12-3视觉跨设备分工的真实编码/传输证据。先读 outlines/12-端边云协同.md 和 extensions 同章12-3，以及相关case-studies，核对原始输入、完整EC（含DeepStack等实际模型所需输出）、语言KV迁移的区别。calculations由另一个session独占，禁止执行/修改/复制其工作或联系作者；不要用计算模拟充实跑。

独占可写 experiments/ch12/12-03/ 及 experiments/parallel-workers/vision/status.md，远端对应/home/ubuntu/ai-infra-book-experiments/ch12/12-03/及私有venv。其他正文/总进展/inventory/research/references/实验只读。禁止git提交、再次派生agent或Codex。先写status，持续更新。

使用真实已有Qwen3-VL-8B-Instruct权重，远端HF缓存 /home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Instruct（4个权重分片合计17534339512bytes），不得重复下载。先精确固定snapshot和config。仅可用RTX主机CPU和Mac CPU，禁止GPU/MPS或停止已有服务：HiCache正在使用GPU。远端CPU最多4线程，内存<12GiB；本地数据<1GiB，无模型权重回传。可以从safetensors按key只读提取完整vision encoder实际参数，使用受支持的官方Transformers模型类，必须完整核验所有vision权重匹配（不能随机初始化代替缺失权重）。已有SG环境Transformers5.8.1/Torch2.11，不能修改共享环境；需要额外依赖用私有env，下载小依赖<300MB。

优先实际执行：固定几张程序生成PNG夹具（分辨率/内容版本不同）→官方processor→实际训练好的vision encoder→完整EC（所有下游所需张量）保存与真实socket传输→接收端形状/dtype/hash逐位一致，比较同一原图传输后重编码与EC直接传输的产物一致性；重复帧可检验正确复用/内容版本变化失效，不能只用尺寸当缓存key。使用独立发送/接收进程、真实日志/退出/字节、固定协议/输入。若 CPU 不支持所选模型路径，保存真正失败和官方源码依据，准备GPU交接，不patch出伪模型。避免完整语言模型加载超内存。

保存原始PNG、实际pixel_values/grid metadata、完整视觉输出、实际模型配置与选取权重manifest、版本/源码hash、原始计时/传输日志，独立run/analyze/README/必要图QA。计时含哪些processor/encoder/序列化/传输分别明确；CPU/同机socket不能当端设备、WAN或GPU性能。小夹具不是任务质量评测，完整模型答案/语言KV迁移/物理功耗若未执行必须保留未完成，不能宣称全12-3达成。只推进这个有界真实测量，不做跨session最终复核；正文候选简洁结果放自己README，主agent统一回填。
