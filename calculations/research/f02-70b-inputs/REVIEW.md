# F02 公开70B代表输入准备

按原计划“70B代表”选用DeepSeek原发布者的DeepSeek-R1-Distill-Llama-70B，保留原Llama-3.1-70B请求401记录，不将蒸馏模型改称Llama原模型。官方config、同revision index及README已下载；架构实现与configuration固定在项目既有Transformers提交。来源、URL、revision、时间及SHA/字节数见manifest.json。未下载权重。

config包含80层、hidden8192、64个Q头/8个KV头、head_dim128、FFN28672、词表128256。配置推导9项每层权重加embedding/final norm/head，共723个权重名，与官方index完全一致。详细形状和参数总数见input-review.json。index名称一致并不证明实际每张量shape/dtype；BF16字节是config声明的逻辑值。

这是一份待公共输入集成的官方来源交付。该模型使用Llama3 scaled RoPE且没有Qwen3的Q/K norm，不能直接套现Qwen3 adapter；完整逐算子脚本、公共CLI/场景与正文集成尚待完成。
