# 实验9-7：历史序列化与连续前缀

复用原始失败Agent的12轮消息，在固定Qwen3-8B tokenizer上实际序列化，不执行模型或工具。

| 方式 | 完整已消费前缀保留 | 12轮输入token合计 |
| --- | ---: | ---: |
| 原模板 | 0/11 | 19556 |
| assistant显式空reasoning_content | 0/11 | 19556 |
| 每个历史assistant保留空thinking文本 | 11/11 | 19820 |
| 保留旧token并追加原输出及反馈 | 11/11 | 19820 |

两种保留方式逐token相同。默认模板每次在旧prompt末尾4个token之前分叉；显式空字段并不能修复。保留方式每个旧assistant增加4token，总输入增加264token。消费前缀排除最后生成的EOS，因为该token尚未作为下一次decode输入；下一轮输入仍包含EOS。

这是针对本轨迹string system/user/assistant消息的受限序列化器，不支持一般tool_calls、多模态或非空推理历史；不建议无条件替换通用模板。源Agent任务失败，保留其输出仅用于固定历史；未证明修正后答案质量、GPU KV实际复用、耗时改善或跨主机收益。随后实际生成若偏离固定输出，也会重新打断前缀。后续GPU对照必须单独检验。

## 复现与证据

```sh
python -m pip install transformers==5.12.1
python -B run.py --out new-results
```

本目录保存实际tokenizer.json/config、原始轨迹、全部48组输入token与44次前缀比较。`results/analysis.json`与用本目录自带tokenizer执行的`replay-check/analysis.json`逐字一致；环境在各自environment.json。未下载权重、未调用模型。`run.py`直接检验12组默认输入等于原记录、历史追加消息、输出decode、EOS与保留文本，不据token数量计算成本。源轨迹SHA在analysis中，所有文件由manifest封存。
