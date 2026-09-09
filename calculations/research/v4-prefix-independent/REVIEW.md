# V4 cached prefix continuation independent review

结论：冻结候选通过独立复核，可按“已完整恢复prefix状态、已知suffix逐token调用”的有限范围集成。它不实现并行cached chunk prefill，不闭合基础forward原有缺项。未修改作者/shared。

## 官方分支与前提

已锁官方inference/model.py中Compressor.forward的start_pos>0分支把kv.squeeze(1)写入单槽；Attention.forward也按start_pos%window写单槽，因此不能把2048个已知suffix token作为一次已有prefix的调用。候选使用输入位置6144..8191、每次tokens1，符合该单token语义。

ratio4有overlap：kv_state和score_state各[B,8,2D]FP32，在每第4个结束位置汇聚后复制后4槽到前4槽；index compressor也具有相同结构、宽度为index_head_dim。ratio128不重叠，每完成128个token汇聚；非边界仍执行投影、槽写及其固定工作。6144已有完整压缩行数1536/48，最终8192为2048/64；新增512/16行。第一新增ratio4边界6148、ratio128边界6272，末次同时为8192。

prefix长度本身不足以重建状态，必须预先存在正确window环排列、全部compressed/index缓存、FP32 kv/score状态及overlap carry。候选未把这些状态的恢复/搬运成本当已算，也未宣称可以仅凭长度运行真实模型。

## 完整基础forward累积

独立对Flash/Pro各3步（prefix126、batch2，跨128结束边界）直接调用公共v4_forward逐步比较有效矩阵、参考tile矩阵、已计scalar及特殊函数，全部相等。静态分区复用的是“每次执行工作”，每步均加回专家/mHC/外norm/head；静态模型参数与checkpoint仅保留一份base账，不把参数容量乘2048。

2048步大例另用独立floor求和闭式：Σfloor(e/r)，CSA为Σmin(topk,floor(e/4))，window恒定。qk/pv按实际selected项、index扫描按全compressed项，加2048倍固定投影与静态基础矩阵，等于候选matrix总量。该验证不依赖重复调用候选attention_step来充当oracle。

每次Transformer.forward都执行head，所以2048个输入调用包含2048份 `2×dim×vocab` GEMM，2047份中间logits无用途但不能省略；最后head可供首个未来输出，不代表本算例另计2048次输出生成。路由直方图每步相同是明确fixture，真实token相关hash/专家不假装不变。

## 预分配与边界

独立从register_buffer尺寸重建max_seq_len129/max_batch4、8192/1、8193/4三种分配：每层main cache为Bmax×[window+floor(maxseq/r)]×head_dim×2；ratio0仍完整window；CSA另index cache；每个compressor两份FP32槽。全部等于候选source_cache_allocation。129小于window时不能以有效长度替代预分配window，候选补足正确。

分配max_seq小于续接终点、max_batch小于运行batch拒绝。ModelArgs默认4096/4被明确覆写为适合本例的8192/1，不声称默认源码分配可容纳8192。预分配预算不包括freq tables、权重和临时区；完整runtime驻留保持null。

状态增长仅新压缩行，window覆盖写与FP32槽覆盖写不增长容量。语义读写总量与resident差不是同一物理量。Uniform BF16和actual packed专家列是替代格式，不能相加当HBM；候选边界已说明。

## 验证产物

check.py：6次独立公共完整forward调用、2048步闭式及3种源buffer分配公式通过。results.json绑定最终候选SHA和结果，源码快照保留。原作者7测试另行重跑。公共接入仍需主线CLI/report/reproduce验证，不把研究测试冒充公共产物通过。

`PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/v4-prefix-independent/check.py`
