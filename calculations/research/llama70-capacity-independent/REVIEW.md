# 70B capacity frozen candidate independent review

结论：可按声明的单设备、教学低位存储、固定工作区预算范围合入。未发现计算阻塞。未改变共享源码或作者候选。绑定候选SHA `5830d853fe3475c51d5e38d097753d7513a7e6c069fa74e4bc4debcfe2f29a36`。

## 独立核算

独立从固定配置尺寸构造723个真实权重名称，集合与官方checkpoint index逐名一致。索引仅证明名称存在，形状来自官方config与已审核Llama定义；不误称索引本身提供tensor shape。

每层7个可量化矩阵：Q8192×8192、K/V各1024×8192、O8192×8192、gate/up各28672×8192、down8192×28672。80层合计560矩阵、68,451,041,280元素。两份未共享词表与161个norm保持BF16，共2,102,665,216元素。总70,553,706,496参数；无Q/K norm误加。默认BF16/8bit/4bit总权重分别141,107,412,992、73,725,919,232、39,500,398,592字节。

独立逐真实名称枚举验证group1/3/128/1000/32768，三个bits分支payload与scale均一致。scale按每行ceil(K/group)计算；group大于K仍每行至少一组。新增反例(3,5)矩阵4bit逐行需9B，不能全局15nibble压成8B；group4/scale2另需12B。该反例检查公共packing helper的行边界，真实70B矩阵恰好偶数K并不会触发此差异。

KV独立公式80×8×128×2(K,V)×2(BF16)×8192=2,684,354,560B；使用KV heads而非64个query heads，权重低位不压缩KV。长度增长和最大context由候选验证。

容量反例：4bit+2GiB workspace下，48 decimal GB为2个8K请求，48GiB为3个；单位混淆会改变整数结果。逐byte检查base−1/base/base+KV−1/base+KV/base+3KV−1/base+3KV，最大请求数分别0/0/0/1/2/3，fit标志把权重/工作区不fit与仅KV不足区分。负available时resident_at_maximum可能大于预算是允许的，并非0请求就成功部署。

## 公共兼容

动态注入候选后实际调用现有CLI `capacity-scan --model deepseek-r1-distill-llama-70b --format md`，现有report成功渲染并包含真实4bit字节值，输出见cli-report.md。现有Qwen8/30/235三种模型完整JSON逐值精确相同。候选8测试全部通过。CLI模型参数不限制枚举，新calculation标识不会阻止通用capacity表。

唯一可顺手更新的非阻塞文案：CLI help仍写Actual Qwen shapes，应包含Llama70。候选不是TP/PP放置实现；capacity list是各独立单设备预算，不得加和为多卡总显存。scale_bytes是正整数教学metadata大小，不声明真实硬件dtype/格式。workspace固定值非真实allocator峰值，缺失反量化临时区和batch相关scratch已声明，不阻塞本有限计算契约，也不能据此标C13全部完成。

## 重跑

`PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/llama70-capacity-independent/check.py`

check.py动态加载冻结候选，在内存替换公共模块以执行CLI；磁盘共享树保持只读。results.json绑定候选/测试/依赖及官方config/index SHA。独立算术验证和SHA身份验证分别记录，SHA不是语义审核替代品。
