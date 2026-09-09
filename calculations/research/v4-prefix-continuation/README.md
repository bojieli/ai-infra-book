# V4 已知后缀的顺序完整基础前向

独立候选入口 `src/infra_calc/topics/v4_prefix_continuation.py:calculate`。公共代码只读，复用现有已锁基础前向、动态 attention 算术和 sparse kernel 账。三个场景与源码摘录在本目录。该工作补上可由固定源码支持的**顺序已知 token 调度**，并不声称实现了 cached parallel chunk prefill。

## 固定源码支持的范围

`source-proof.json` 绑定 Flash/Pro 官方原件 SHA 与正文行。Compressor 的 `start_pos==0` 分支处理完整序列；`start_pos>0` 分支按 `(start_pos+1)%ratio` 判断完成，`kv.squeeze(1)` 写入一个 `[B,width]` 槽（316–377行）。Attention 对增量路径也把 `kv.squeeze(1)` 写到 `start_pos%window` 单槽（518–533行）。因此对 `[B,2048,width]`，squeeze 不会删掉时间维，不能据源码证明一次调用支持6144+2048。公共 attention 入口的显式拒绝符合该限制。

合法的有限调度是：完整前缀状态已正确恢复，逐个传入后缀已知 token；调用 start_pos 依次为6144…8191，每次 seqlen=1。Transformer.forward 每次执行 embedding、全部基础层、hc_head/final norm/词表头（801–809行）；中间2047次logits虽不用也有实际源工作。最终logits可提供后续首个生成token，这里没有追加生成调用。不能省略中间词表头后仍称原封不动源路径。

前缀状态包含环形window布局、压缩历史、index历史、FP32 kv_state/score_state及ratio4重叠carry。仅有prefix长度或主cache无法恢复这些内容。查找、传输、恢复和前缀原计算不在本次后缀账，保持unknown。

源 `ModelArgs` 默认 max_seq_len=4096、max_batch_size=4。候选显式声明覆盖本请求的分配输入，book默认8192/1，并拒绝不足值；不是声称默认4096配置可直接运行8192位置。预分配cache/compressor bytes与请求有效状态独立列出，不含freq表、权重和其它临时，设备是否容得下仍需另验。

## 6144+2048 默认 Flash 结果

| 项目 | 结果 |
|---|---:|
| 顺序基础forward调用 | 2048 |
| 有效attention口径全部基础矩阵 FLOPs | 60,270,873,411,584 |
| 替换已知sparse/expert tile后的矩阵 FLOPs | 884,744,027,897,856 |
| 已计普通scalar FLOPs | 1,351,190,939,136 |
| 2048次词表头矩阵 FLOPs | 2,168,958,484,480 |
| prefix有效状态 bytes | 60,112,896 |
| final有效状态 bytes | 74,203,136 |
| 状态增长 bytes | 14,090,240 |
| ratio4完成数 | 512 |
| ratio128完成数 | 16 |

ratio4在结束位置6148、6152、…、8192完成；ratio128在6272、6400、…、8192完成；结束位置对应 `input_position+1`。后者也是ratio4边界。所有2048行保留完成标记、单步矩阵/scalar/special、接口bytes与末状态，可直接画边界更新峰值。状态增长与写入不是同一数：window持续覆盖、compressor每步写FP32槽，ratio4完成时还读写重叠carry。

special按名字累加，不把exp、topk候选、bit round、encode/decode和整数lookup当Tensor FLOPs。接口分列sparse gather/query/output/index/sink、index扫描、window/压缩新记录、FP32槽和重叠复制，以及静态子阶段权重比较载荷。专家的BF16比较权重与实际packed+scale是替代口径，不能相加。未包含完整norm/数据转换访存；完整HBM、runtime驻留peak、完整scalar和延迟均为null。

## 静态复用与验收

完整基础forward只调用一次，因此checkpoint索引和全部分片头只核一遍。其专家/mHC/外部norm/head工作按同一明确路由直方图每步复用；动态 attention 只接已加载config，逐步更新选中历史、index扫描、compressor和sparse tile。不是把静态模块每步执行成本省掉。所选路由是固定工作负载假设，不宣称真实后缀tokens每步恰好有相同专家分布；尤其hash输入与评分路由需实测每步直方图才能进一步收紧。

7项回归验证Flash/Pro跨128边界每步与完整公共forward一致（矩阵、tile、scalar、special、state），首步恰好完成块，book全部压缩位置及独立缓存增长式，checkpoint仅一次，合计守恒、分配拒绝/FP32更新，以及公共并行chunk拒绝。没有运行完整V4 checkpoint，也没有以计数一致替代数值输出一致或质量证明。

```sh
python -m unittest discover -s calculations/research/v4-prefix-continuation/tests -v
PYTHONPATH=calculations/src python calculations/research/v4-prefix-continuation/freeze.py
```

公共接入可新增独立 `v4-prefix-continuation` topic和三个book场景；输出应保留 `parallel_cached_chunk=False`、每调用head、分配输入及unknown，避免沿用“并行命中prefill”标签。当前基础forward已经列明的量化转换、部分primitive与运行时访存缺口没有因本调度而消失。
