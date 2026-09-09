Qwen3.5冻结续补差异复核

本次只核初始snapshot到作者冻结版本的差异；原snapshot及其36个独立数值案例保持不变。冻结主模块、helper、新mask原件均独立保存，SHA见final-results.json。未修改shared或作者目录。

**结论：两处record_past接口错误均已修复；此次复核没有剩余已发现的核心数学错误。** 可按已声明的reference矩阵/标量/primitive与逻辑接口边界集成，不能升级成实测HBM、完整分配峰值或backend全指令账。

复核过程中发现并推动修复：

1. 原snapshot对cold record_past=True错误计last4 copy，已改为alias赋值，保留实际T长度。
2. 第一次冻结版虽去掉last4 copy，但cold record_past=True且T<4时仍在`cache_concat_or_initial_pad`伪计一次输入复制。已通知作者再次修复，条件现为`not S and (T>=4 or record_past)`时该接口读写皆零。源码确实不pad也不cat；lazy initialization先建4槽zero仍是真实语句，因此保留。

第二次冻结后10个独立场景均通过：cold recorded T1/T2/T8，普通cold T1/T2/T8，cached recurrent、cached多token chunk、T65尾块，以及已有recorded history未知长度场景。具体可重跑验证在check_final.py/final-results.json。

已核完整的具体部分：

- 原36例DeltaNet chunk/recurrent数学对照与4个核心矩阵/solve/MoE/状态守恒不受此次改动影响。核心GEMM与三角求解计算未被本轮修改。
- Full attention：valid QK/PV加显式masked slots，等于每15层完整B*Q*T*(S+T)矩形的矩阵工作。softmax补齐masked位置的exp/普通算术，并为每score加一次mask，合计每层5*Q*B*T*(S+T)-Q*B*T普通算术。没有重复再加SDPA参考账。
- Conv：普通fallback输入L，dense输出L+3，先裁到L再SiLU，最后裁T；cached update输入4+T，conv无padding输出L-3，先裁T再SiLU。valid subtotal加额外槽恰好等于全部dense conv乘加槽；SiLU范围与实际裁切顺序一致。
- Cold record_past：无last4 copy、无pad/cat copy；保留4槽初始化zero；最终retained conv为45*B*12288*T*2字节。该retained量可别名输入，不等于新增分配字节。已有记录长未知时保留null，未凭history强猜长度。
- Mask原件：新增masking_utils.py与模型相同固定commit `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`，SHA/bytes均一致。选定纯文本、无外部padding、DynamicCache、eager causal路径；eager_mask显式禁止is_causal_skip。先生成T*(S+T)布尔因果平面再批展开，最后写B*1*T*(S+T) BF16 where结果；没有把expand视图伪算成先复制B遍比较。
- 新norm/gate与router接口按逐语句读写核对：offset RMS的weight.float()+1、gated RMS的先回输入dtype乘weight、再乘FP32 SiLU(z)、末cast顺序正确；router softmax/topk/selected renorm/index_add各接口分列，未再重复添加已有数学FLOPs。

仍为已声明primitive或运行时边界，而非本轮可声称精确的内容：

- torch三角solve、softmax/topk/nonzero/where/reduction的实际kernel内部算法、工作区与指令排程；其数学工作或primitive接口可计，不能声称实测实现。
- hub替代FLA/causal-conv实现、导出inverse构建分支、外部padding/custom packed mask及实际生成kernel并非本次选择路径。
- 同一source语句接口与原operator边界存在重叠；不得相加作为HBM总流量。alias、allocator lifetime、peak live memory和硬件缓存效果也没有得到运行验证。
- 已有record_past记录的真实长度未作为输入提供，相关conv重算与额外记录保留量继续unknown。
- 常数建立、Python调度、kernel launch等运行时开销不由所列普通算术与特殊primitive数量证明；模块保持full_forward_exact=False是必要边界，不应改成True。

复现命令：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=calculations/src python3 calculations/research/qwen35-independent-math/check_math.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=calculations/src python3 calculations/research/qwen35-independent-math/check_final.py
```

本次实际运行第二条10例通过；第一条在前轮已实际运行36例通过，核心代码无改动无需重复宣称新测试。作者20测试/8场景为作者验证，未混入独立案例数。
