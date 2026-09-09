# VL请求阶段账

`topics/vl_request.py`复用vision_encoding与公共GQA/SwiGLU算子，按官方Qwen3-VL-4B text配置显式生成语言阶段；现有vision-encoding.lock内固定modeling_qwen3_vl.py同时锁定语言实现，因此没有新增重复来源。

默认4张预处理后640×640图片，每张400语言图像位置，加400个已计数非图像位置（包括模板/边界/工具说明）得到2000-position prompt。输出128 token时，prefill最后logits产生第1个，随后127个decode forward，最终KV2127位置。

| 阶段 | 次数 | 矩阵FLOPs |
| --- | ---: | ---: |
| 视觉编码 | 4 | 5,241,202,278,400 |
| 语言prefill | 1 | 15,714,279,096,320 |
| 语言decode | 127 | 1,176,266,473,472 |
| 总量 | | 22,131,747,848,192 |

语言hidden2560、Q32×128=4096、KV8×128=1024、FFN9728、36层，词表151936，embedding/lm_head官方tie共享容量但输出头仍执行GEMM。全部语言参数4,022,468,096，BF16 8,044,936,192 bytes；与视觉权重830,695,424 bytes分阶段列出，不假设全部同时驻留一张卡。

BF16 KV每position147456 bytes，prefill294912000 bytes，最后313638912 bytes。图像cache全命中只将视觉编码工作降零，2000语言prompt、完整EC传输载荷和最终KV不变。没有默认语言prefix-cache命中。

DeepStack视觉5/11/17输出是在语言0/1/2层后注入；参考源码每次clone整个prompt并对视觉位置做加法，因此三次clone和12,288,000元素add单列。后续decode不运行这些注入或视觉编码。M-RoPE替换公共LLM的一维表，三轴频率与特殊函数按固定VL源码计；位置值生成/模板分词不假装执行过。

矩阵采用有效语言因果对（prefill2,001,000；decode合计262,128），视觉仍独立图内非因果attention。算子还提供norm/SiLU/softmax/RoPE/残差/embedding/输出头/KV追加载荷；语义字节不是HBM测量。图片产生embedding后仍需要语言层处理其位置，但这个工作只在统一prompt里计一次。CPU预处理、网络/排队、实际cache服务、采样与动作执行不在工作预算内。

3项测试验证独立参数及矩阵公式、7-output-token的逐步decode与等差和、全部encoder命中不减语言工作，以及context边界与KV精度切换。
