# Qwen3.5 F02 必要输入独立审查

**可接受当前F02必要固定config／实现／checkpoint metadata输入。未发现需要阻止合入的实际来源、分片范围或基础文本形状错误。** 这不构成完整forward计算、运行时加载或全部视觉/MTP执行覆盖的验收。

独立脚本 `audit.py` 仅读原件，不执行提供方脚本、不下载权重；结果及输入哈希见 `verification.json`。审阅同时核对了实际config、modeling构造器及fallback/router代码，不把脚本通过本身当作来源正确。

## 独立确认

- 204份拟合入原件的SHA和长度正确，共1127274 bytes；文件路径无重复，与公共锁无碰撞。独立config副本与现有共享config逐字节相同。
- 模型revision为8472618112abcbd45acbcdc58436aff4233c23f7；实现revision为cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55。9份实现／测试／辅助文件不仅匹配自报SHA256，还匹配已归档固定Git tree中的Git blob SHA1。
- 94分片的8字节长度前缀与header真实长度一致，188条HTTP206记录范围严格一致。同一分片两次Content-Range总长度相同，且等于8字节前缀＋header长度＋所有tensor payload字节。比原审查增加了分片总文件大小的闭合检查。
- 所有JSON用拒绝重复键的解析器读取；2924张量无重复名称，index/shard归属、非负shape、dtype字节、连续offset、总字节以及tensor-inventory逐项一致。
- 独立构造1038个基础文本张量名称/形状，与全部基础文本header一一相符。实际源码确认线性层qkv与z分列、全注意力Q含gate、head_dim256不同于H/heads128、45线性/15full层、每层共享专家、512/top10专家和router FP32 softmax。

| 存储部分 | 张量数及dtype | 元素数 | payload字节 |
|---|---|---:|---:|
| 基础文本 | 948 BF16＋90 F32 | 396346350336 | 792692717952 |
| 视觉 | 333 BF16 | 456010480 | 912020960 |
| MTP | 1553 BF16 | 6595568128 | 13191136256 |

型号397B不能取代实际checkpoint分账。MTP分离后，基础文本＋视觉约396.802B元素；完整checkpoint约403.398B元素。90个FP32张量属于基础文本，因此也不能把全部文件按BF16二字节统算。

## 有限修正

1. **204条来源锁记录缺少downloaded_at。** 这不改变原件真实性，但丢失了已存在的获取时间。`source-timestamp.patch.json` 对原 `source-lock.patch.json` 提供204条完整记录test及204条时间字段add，时间逐项来自原HTTP日志。可先对独立来源提案应用，再合公共锁；不是针对公共锁索引的补丁。
2. **卷积与递推分支条件须分开写。** 递推核在已有state且seq_len=1时选择；单步causal_conv1d_update还要求 `record_past=False`。如果后续forward只按“cached单token”统一选择两条路径，会漏掉record_past卷积历史保留分支。现有报告并未声称完整路径实现，属于后续适配器必须保留的具体约束。
3. config中的transformers_version=4.57.0.dev0是保存时元数据，模型README要求latest Transformers；不能作为本次所选实现commit的版本兼容认证。双仓库revision已正确分开。1038形状相符确认基础文本张量契约，但不等于完成state_dict加载和数值输出验证。

## 非本次输入验收已完成项

锁定9份实现源不是可离线安装的Transformers依赖闭包：modeling还导入通用mask、activation、modeling、integration/kernel等；固定整个仓库commit使这些后续可精确补取，但当前未执行它们。动态hub kernel替换不能自动继承fallback逐算子账。

视觉与MTP的header存储账已完成，config→全部预期张量枚举和完整运行路径未完成。MTP在模型README有专门的vLLM speculative配置，并不证明当前选定Transformers基础类实现了MTP；不能把其6.596B参数混入基础60层forward。视觉还需单独核grid/THW、attention分块和merger路径。tokenizer_config不是完整tokenizer词表；实际字符串分词的端到端复算需要另锁tokenizer数据，而给定token数量的矩阵预算不依赖其下载。

F02必要输入可按上述边界验收；完整forward、runtime加载、实际分词、视觉/MTP执行及有效硬件测量另列，不能借此输入验收宣称全项目已支持完整Qwen3.5推理。
