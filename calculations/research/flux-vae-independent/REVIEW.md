# FLUX2 Klein VAE decoder independent review

当前冻结快照见flux_vae_decode.snapshot.py，最终SHA在layout-delta-results.json；results.json保留此前16例数学审计绑定。独立16场景通过；候选可支持声明的decoder参数/算术及条件张量边界预算，不是完整GPU运行时峰值。最终布局分支改为正常接受大输入、复制字节unknown及条件预算null；增量重绑通过，可按声明范围集成。

## 固定操作图与参数

官方config与已锁Diffusers源码确定：post_quant32→32的1×1conv、decoder输入32→512的3×3conv；mid两个512残差块夹一个单头512维attention；up通道512/512/256/128，每级3个residual，前三次nearest2×及3×3conv；末端GN+SiLU+128→3conv。总14个residual、40个conv/linear、30个GN、29个SiLU、15次残差加法和除1、3次nearest。

每个conv包含输出通道bias；两个变通道残差shortcut为1×1+偏置。attention四个512²投影均有bias，GN有gamma和beta。独立从通道图建立维度列表得到49,620,259参数，与候选一致。此结果不声称checkpoint header验证，也不把encoder或VAE latent batchnorm的参数混进decoder。

矩阵为dense same-padding FMA2槽预算，另枚举非padding值。最小8²输出的latent1×1检验3×3卷积只有中心tap有效；不能把padding槽说成有效输入乘法。GN的7E+G普通标量与G次rsqrt对应声明two-pass biased variance+affine；不代表实际CUDA归约算法。SiLU乘法和sigmoid分列，nearest没有浮点插值乘加但有输出复制。SDPA数学attention与eager共享QK/PV工作，不给opaque SDPA猜造N²score张量。

## 生命周期实质修正

固定attention_processor.py第694行显式del baddbmm_input：原候选将beta0临时scratch保留至probability返回，有误。作者已修producer=last_use=QK步骤；独立验证scratch不再出现在softmax事件中。

第700行亦显式del attention_scores：BF16 upcast后的FP32 score于softmax结束释放，prob.to阶段不应继续保留。我曾在未看完整函数时提出延长score32，完整读取后立即撤回；当前候选释放点正确。独立测试同时检查两条显式删除，避免相反方向误差相抵。

其他对象持有按源码frame检查：residual根输入由调用者保留至返回，main/shortcut局部在加法及除1期间仍存活；attention root/normalized encoder alias/Q/K/V、eager probability保留至processor返回；Decoder的sample在mid/up调用期间仍指旧输入；_decode的postquant z保持至decoder返回。latent外部调用者保留，返回后只计latent与RGB。独立interval枚举与所有事件张量集合/字节相符；这验证声明对象图的一致性，不证明allocator或backend内部峰值。

## 范围收紧建议

PyTorch>=2.1 BF16 nearest不执行旧版FP32 roundtrip，因此该路径当前dtype字节合理。但官方Upsample2D另有batch>=64或input.numel()*scale_factor>2^31触发contiguous。候选未模拟layout，故要求作者限制这两类输入或返回显式未核布局状态，不能默认为0复制。默认1024 B1及16独立例不触发。

外部输入必须已unpatchify/BN反标准化；此模块不重算DiT或image_stages完整VAE矩阵。集成宜替换已有decoder分项并保留其余BN/packing阶段，不能把新matrix总量再加一次。workspace只有显式输入时才给weights+boundary+workspace，actual_runtime_peak必须null。no tiling/slicing/offload/autograd明确保留。

## 可重跑证据

check.py不调用作者测试或image_stages作oracle。独立维度图与矩阵公式覆盖16场景：8² B1、16×24 B2、64×128 B1、1024² B1，分别BF16/FP32×eager/SDPA。检查权重、dense/nonpadding、GN、nearest、明确删除事件、张量区间集合、conditional workspace12345及actual_runtime_peak=null。六份官方原件SHA及bytes独立验证，锁保存sources.lock.json。

运行：`PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/flux-vae-independent/check.py`。shared及作者目录未改。

最终范围修正已核：batch64与8192²被明确拒绝；batch63的小图允许，4096²恰好numel×2=2^31仍允许，匹配官方严格大于条件。新增config provenance列入候选sources；16场景复核再次通过，最终SHA见results.json。


## 最终替代结论：接受大输入，布局复制未知

上文拒绝batch64/8192²的旧验收已作废，仅作为审查历史。最终候选正常接受大batch/大尺寸，每个upsample阶段返回input_elements/input_bytes/triggered/materialized_copy_bytes。触发时复制量null，summary.layout_copy_bytes_unknown=true，显式workspace也不能产生conditional_weights_boundary_workspace_bytes；named-boundary peak保留但明确排除未知布局复制。

只审该diff并执行check_layout_delta.py的8项检查（4种形状×2种dtype），未重复完整数学审计。batch64三个阶段均触发；8192²第一阶段未触发、后两阶段触发；4096²最后阶段恰2^31不触发，batch63小图亦不触发。每阶段输入元素/字节独立核算、true/null传播与无触发条件预算均通过。actual_runtime_peak仍null。新快照与layout-delta-results.json绑定最终源，原快照另存flux_vae_decode.pre-layout-update.py。
