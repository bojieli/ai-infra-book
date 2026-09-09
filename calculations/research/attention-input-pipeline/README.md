# Qwen注意力输入：有限槽位与异步供数候选

以官方Qwen3-8B的head_dim=128，把矩形QK分为K向累加块。默认Q[128,128]×K[128,128]，tile_k32；每块Q/K输入16KiB、1,048,576 FLOPs，4块串行累加到64KiB FP32结果。输入槽和累加器属于不同容量层级。

声明每时间单位输入256B、矩阵8192FLOPs、寄存器中转256B；额外请求完成延迟128时间单位。每个服务阶段单独向上取整。时间单位不是实际GPU时钟，速率不是厂商spec。

| 场景 | 1槽 | 2槽 | 4槽 | 8槽 | 匹配无槽位背压参考的最小枚举槽数 |
|---|---:|---:|---:|---:|---:|
| base | 1280 | 768 | 704 | 704（容量失败） | 4 |
| matrix-double | 1024 | 576 | 448 | 448（容量失败） | 4 |
| long-latency | 2816 | 1536 | 1088 | 1088（容量失败） | 4 |
| tile-k16 | 1792 | 960 | 672 | 672 | 4 |
| tile-k64 | 1024 | 768 | 768（容量失败） | 768（容量失败） | 2 |
| capacity-one-slot | 1280 | 768（容量失败） | 704（容量失败） | 704（容量失败） | 4 |

同步模式显式串行化搬运、寄存器写/读中转与计算；默认中转接口共131072B，异步直接到输入缓冲的声明路径省去该中转量，外部输入总量仍为65536B。地址/描述符/指令数量尚未建模，因此没有假定一条异步指令能替代任意数量的普通指令。

槽位从issue开始占用到消费矩阵结束。输入端口按load服务间隔发起请求，完成另加固定延迟，可以与后续请求重叠；消费者按K方向顺序累加。已准备不等于已消费，不能在data_ready时提前回收输入槽。输出逐块issue、ready、compute start/end、slot release、背压和计算空闲。

六场景包含矩阵速率翻倍、长延迟、K16/K64分块及一槽容量预算。容量只筛选输入SMEM；寄存器暂存和FP32累加器独立列出，仍不能保证完整内核可部署。结束点是QK累加器完成，不含Softmax/PV、输出写回、bank冲突、完整同步或实际指令开销。

复现：

```sh
python3 calculations/research/attention-input-pipeline/calculate.py --output calculations/research/attention-input-pipeline/result.json
python3 calculations/research/attention-input-pipeline/check.py
python3 -m unittest discover -s calculations/research/attention-input-pipeline -p 'test_*.py'
```

逐时刻独立模拟不导入候选，1144检查通过；4专项tests覆盖槽位消费结束释放、容量相差1B、有限槽饱和及非法输入。公共CLI、固定结果、正文接入与剩余地址/专用交接要求待办，C23不据此勾选。


公共接入已完成：`python3 calculations/calc.py attention-input-pipeline --inputs calculations/scenarios/attention-input-example.json --format md`。六组结果位于results/attention-input-*.json/md；12次实际CLI及12冻结产物全量数据与候选相同。全suite810项788通过22跳过，1807产物/22图和正文网页通过；证据见相邻attention-input-integration/acceptance.json。上文候选阶段说明保留历史，C23其余地址/指令/专用交接要求仍待。
