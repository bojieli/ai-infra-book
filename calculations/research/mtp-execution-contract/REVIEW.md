# MTP三方层数与下一单层执行契约

固定原件已足以闭合本次“三方分别说清”的有限证据任务，但不支持声称已核真实部署MTP调用数。mapping.json保留逐模型字段、源码/报告SHA、下一算子图及去重界。未修改公共文件，也没有新下载权重。

| 模型 | 报告训练MTP | 发布配置与checkpoint | 固定入口行为 | 实际服务启用 |
|---|---|---|---|---|
| V4-Flash | depth1；报告文本1384–1385 | config num_nextn_predict_layers=1；mtp.0共1575索引键 | Transformer.forward不调用mtp；构造器建立1个模块；__main__用随机h单独演示两次调用 | unknown |
| V4-Pro | depth1；报告文本1405 | config同为1；mtp.0共2343键 | 同一参考路径；独立MTP演示不证明服务启用 | unknown |
| Kimi K3 | 表中1层；文本933–956说明将该层微调为EAGLE3草稿，训练unroll7步 | text_config num_nextn_predict_layers=0；497220个索引键无mtp/nextn/draft/eagle名称，语言层恰0..92共93层，与主干配置一致 | 固定wrapper调用language_model，其构造/forward仅93主干层，无草稿分支 | unknown |

“固定函数中调用0次”与“实际服务启用未知”是不同字段。V4演示的输入h是torch.randn，并未从Transformer.forward取回真实目标隐藏状态；不能将它记为真实draft服务轨迹。K3报告的7步是草稿训练展开次数，不是7个MTP层，也不是每轮必然接受7token。报告一层与本次发布配置零层应原样保留，不修配置来制造一致。

## 最有界的可执行下一计算

优先Flash单个显式MTPBlock。固定inference config的base_layers=43，compress_ratios长度44，MTP索引43的ratio=0；Pro对应61/62/ratio0。n_mtp_layers未显式写入inference JSON，但ModelArgs默认1，发布HF配置也为1。无需把主干ratio4/128压缩器错误附到此层。

按官方model.py:738–766依次展开：

1. 共享embedding读取input_ids到[B,T,H]，own enorm做weighted RMS。
2. 输入target_hidden是[B,T,4,H]；own hnorm对每一路H分别归一化，不是对4H一次归一化。
3. e_proj在BT行上执行H×H；h_proj在4BT行上执行同一H×H矩阵。两者新增有效矩阵工作合计`2BT(1+4)H²`，h_proj参数只有一份。
4. e_proj输出unsqueeze是视图，加到四路h_proj输出执行4BTH次加法。
5. 调用继承Block：两套mHC前后汇合、attention/FFN norm、ratio0独立注意力、评分路由MoE。MTP层号已在hash前三层之后，不能套hash路由。状态属于MTP Attention实例，不能别名主干最后层KV。
6. own hc_head_fn/base/scale将所有T位置的四路合并，own norm仍处理所有T。共享ParallelHead.get_logits明确只取x[:,−1]，词表矩阵工作是`2BHV`，不能乘T。多卡all_gather属于另一个显式world_size路径。

契约先限定world_size1；fresh start0可T≥1，positive start先仅T1并要求调用者提供正确MTP初态。不要从主干缓存存在推MTP缓存已经恢复。target hidden与input_ids的真实next-token对齐、草稿特征截取和验证/拒绝回滚必须由caller证据另给。对齐未证时，只称单个模块的条件执行账。

## 复用与防重复

- 已有v4_attention/arithmetic/projection、mHC、expert子账可抽取一层公式，不能再加一次完整v4_forward总数。
- 新e_proj/h_proj、三个MTP norm和MTP专属HC-head是必须补的外层；其余own Block权重/缓存亦需计入该额外层。
- v4_checkpoint已按base/mtp分开真实packed字节；若用户容量初始已包含全checkpoint，新增调用不重复增加同一MTP权重。shared embed/head没有新的unique参数副本，但每次调用的查表/矩阵工作仍发生。
- v4_optimizer(include_mtp=True)只是更新分组和状态账，不是MTP forward实现。现有primitive/hc/attention/MoE反向也不能混入推理前向。
- 实际e_proj/h_proj含scale，不能因H×H公式而称BF16 checkpoint或假设FP32逐值执行；有效数学和固定FP8/量化路径tile/转换应分列。

## K3下一边界

报告可证的EAGLE3输入为第1、第4与最后AttnRes块输出，拼接后由无bias[3H,H]投影融合，初始化[0,0,I]；target冻结，只训练draft及fusion。它支持一个“报告数学融合”子账，但本次发布config/index/reference没有相应可执行草稿模块/权重与特征接口。不得简单复制主干最后一层并声称这就是发布MTP。下一有限来源需求是官方draft配置/权重命名与固定调用代码，或明确把[3H,H]融合标为报告层面的条件算例；不需要重下现有96个主干头。

因此T01可形成有据的训练/发布/入口差异表；T02仍待上述Flash单层计算及有调用证据的draft/verify调度连接。真实启用、接受长度、质量、服务时延继续unknown，不以这些unknown阻止先完成明确的单层预算。
