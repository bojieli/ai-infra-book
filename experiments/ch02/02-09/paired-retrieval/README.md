# 实验2-9：同消息模型检索质量对照

**Qwen3-8B与V4 Flash在同一八道短语检索题均8/8正常停止并精确答对，未区分出质量优劣。** V4复用2-5已封存的八份原响应，Qwen只新增这组消息的八次推理，没有重跑V4或重复计算。

| 原消息档位 | Qwen实际输入token | V4实际输入token | Qwen / V4严格通过 |
| --- | ---: | ---: | ---: |
| 短文，两个答案×前/后位置 | 523或524 | 501 | 4/4 / 4/4 |
| 长文，两个答案×前/后位置 | 2121或2122 | 2036 | 4/4 / 4/4 |

这里的“长文”只相对本题短文，不是长上下文能力验证。两者system/user内容逐字相同，但分词器和聊天模板不同；不强行凑成相同token数。期望短语由原文独立提取，要求`text.strip()`精确匹配且自然stop。保留完整文本、输入/输出token、结束信息及每对消息SHA。

## 如何影响模型选择

这八题只证明两种已测部署都通过此窄任务。不能从同为8/8推断一般能力相同，也不能从历史运行耗时判定性价比。Qwen BF16权重/KV、vLLM0.23、Triton attention；V4原MXFP4专家fallback、FP8 KV、SGLang0.5.13、110GiB CPUoffload以及私有bias引用适配。两者部署、模板、精度和运行时间不同，原V4专家严格数值门槛仍未放行；本次不是纯架构因果对照。

V4 Pro和Kimi K3没有纳入本实验的同消息原始响应，报告为null，不继承Flash或Qwen分数。资源、FLOPs、Roofline及链路核算由C14另一个任务负责，本目录不重算或据缺失数据选出成本赢家。2-9整体仍partial。

## 已固定的最小后续实验（未执行）

`next-experiment.json`固定四道原8-8长文多键检索题、完整消息和Qwen既有原响应。Qwen BF16串行repeat0已知为3/4，故只需新增四次V4推理，不重跑Qwen。要求自然stop、精确三个六位数字字符串的JSON、拒绝重复/额外键及解释；输出上限128。

若V4达到4/4，便为“这四道多键任务需要更大模型”提供有限证据；否则保留各题差异或并列，不用综合总分掩盖错误身份。Qwen结果在提案前已知，所以这是针对已有失败的增补，不是盲选留出集。原V4最大上下文4096，不能直接运行Qwen7239token的这组文档；必须先用V4分词器核实长度并验证真实可用池和资源。此项尚未执行，不把提案当成质量结果。

## 原始证据与复现

`cases.json`、`reference/v4-requests.json`及原评分、token核验、配置证据由旧成功实验逐字复制；来源和SHA在origin.json。新Qwen结果在`runs/paired-002/`，启动前prepared.json保存实际模板token，environment.json记录部署和执行脚本SHA。正文只引用结果，完整数据可独立重新评分：

```sh
python3 -B analyze.py
python3 -B analyze.py --run runs/paired-002 --out another-analysis.json
```

实际新运行需要固定Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`和Torch2.11cu130/vLLM0.23/Transformers5.12.1环境：

```sh
/path/to/runtime-python -B resource_guard.py --out runs/new-guard -- \
  /path/to/runtime-python -B run.py --model /path/to/fixed-Qwen3-8B --out runs/new
```

greedy、top_p1、top_k1、最多32输出、允许EOS；单请求、chunk256、2GiB KV、APC/graph/异步调度关闭，没有同题预热。首请求可能含首次编译，不做性能比较。Qwen全部输入ID与实际引擎输入、输出decode和EOS均在运行时核验。51离线检查重新评分原V4和新Qwen；正式运行48610 exit0、14.071s、guard无原因/无残留。

只有paired-002成功运行及其监督记录。成功后清理被替代的6个启动调试文件，没有模型回答被删除，见cleanup.json。有效失败结果和不同正式条件不按启动失败清理。未修改calculations，也未开始全书最后的跨session论文审计。
