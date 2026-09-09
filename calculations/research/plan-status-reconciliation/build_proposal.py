"""Create guarded PLAN prose-only proposals; never edit PLAN itself."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];target=CALC/'PLAN.md';raw=target.read_bytes();text=raw.decode();changes=[]
def add(old,new,reason):
 assert text.count(old)==1,(old,text.count(old))
 changes.append(dict(old=old,new=new,line=text[:text.index(old)].count('\n')+1,reason=reason))
add('不冒称所有数值已公开，H05逐精度/clock映射与H07全局来源工作另行完成。','不冒称所有数值已公开；H05逐精度/clock映射与H07全局来源工作已有各自正式验收，见下方对应条目。','H01 boundary references now-completed H05/H07')
add('未声明实测性能或H05/H07全局完成。','未声明实测性能；H05/H07全局来源与语义验收另有独立证据，见对应已完成条目。','H02 local scope is not a denial of final global acceptance')
add('H05/H07另行验收。','H05/H07已另有正式验收记录，见对应条目。','H03 future tense stale')
add('这是计算契约完成，不代表H01–H05／H07的全部规格审查或C22的全部负载映射完成。','这是计算契约完成；H01–H05／H07已有各自独立规格审查验收，C22有限逐层资源界也已接入，但完整负载映射与运行时仍未由本条闭合。','H06 scope statement clarified without changing checked status')
add('coverage 保留运行时转换／分配、剩余复制／量化和 MTP／前缀执行缺项；','coverage 保留运行时转换／分配、剩余复制／量化和 MTP 缺项；合法逐token前缀续算已由[v4-prefix-continuation](src/infra_calc/topics/v4_prefix_continuation.py)接入6144+2048等场景，恢复成本、并行chunk与完整runtime继续待补；','C10 sequential prefix execution exists publicly')
add('低位多卡分组/完整通信图、实际工作区和结构变化仍待完成。','[Dense低位多卡](src/infra_calc/topics/dense_quantized_placement.py)与[Qwen235逐卡容量](src/infra_calc/topics/qwen235_placement.py)已补local-K分组/尾部、TP复制及最差rank门槛；[架构变体](src/infra_calc/topics/architecture_variants.py)已补声明的深宽/KV/FFN变化。完整通信、实际workspace/低位执行与MoE颗粒度、质量条件仍待。','C13 local-K and finite architecture variants already public')
add('原论文实验点、任务质量映射与图3-7待补，不标整项完成。','[real-scaling-fit](src/infra_calc/topics/real_scaling_fit.py)已接作者8个C4点、6fit/2预定holdout及四项敏感性；[real-scaling-lifecycle](src/infra_calc/topics/real_scaling_lifecycle.py)已接主law与敏感性的调用量交叉和外推边界，plot-real-scaling已生成真实点/生命周期双图。完整论文实验、同任务质量映射、实际硬件费用与统计不确定性仍未闭合，不标整项完成。','C19 real data, lifecycle and relevant figure already public')
add('真实生命周期曲线候选待公共接入，原完整实验/质量/费用范围不由单个fit勾完。','真实生命周期曲线已公共接入，见下一条；原完整实验/质量/费用范围不由单个fit勾完。','Duplicate old paragraph contradicts following lifecycle completion')
add('- [ ] C33 Qwen235B/V4/K3 专家 EP/TP/PP 组合、路由倾斜、组播去重及逐卡峰值（6.3）。','- [ ] C33 Qwen235B/V4/K3 专家 EP/TP/PP 组合、路由倾斜、组播去重及逐卡峰值（6.3）。现有公共qwen235-placement、moe-dedup、grouped-experts已分别覆盖容量/路由去重/局部矩阵；[同cohort联合执行候选](research/qwen235-execution/CONTRACT.md)已独立审查，尚待公共接入。其他模型完整所有权图、实际通信/运行时与多目标扫描继续待补。','No shared qwen235_execution.py yet at this snapshot; distinguish reviewed candidate from public delivery')
add('- [ ] C55 GPipe/1F1B 微批时序与峰值、pipeline bubble、不均衡与暴露通信，长序列／MoE（10.3）。','- [ ] C55 GPipe/1F1B 微批时序与峰值、pipeline bubble、不均衡与暴露通信，长序列／MoE（10.3）。[training-pipeline-schedule](src/infra_calc/topics/training_pipeline_schedule.py)已接Qwen8 PP4时序、有限缓冲、参数更新屏障和不均衡；[training-pipeline-gemm-state](src/infra_calc/topics/training_pipeline_gemm_state.py)已补253输入身份、325矩阵VJP依赖及保存/乘积重算合账。长序列/MoE扩展、实际BF16后端激活与完整运行峰值仍待，不勾选整项。','Public pipeline schedule and GEMM state missing from primary checkbox summary')
add('真实大模型、输入供给、争用归因与完整恢复仍待。','[训练输入供给候选](research/training-input-supply/CONTRACT.md)已补预token样本打包、21B线格式、R/P/H/C与snapshot/write及共享存储，独立审查通过但尚待公共接入。真实大模型输入/预处理校准、争用归因与完整恢复仍待。','C56 candidate reviewed but not public; keep original requirement open')
add('原始波形预处理与完整请求仍待。','[原始PCM前端候选](research/omni-audio-preprocess/CONTRACT.md)已锁固定Whisper/STFT/mel/mask和30s构造器边界并完成数值验证，尚待独立审查及公共接入；现有[omni-understanding](src/infra_calc/topics/omni_understanding.py)已连接预计算媒体与Thinker。文件解码/重采样、FFT内部实现与完整请求运行时继续待补。','C77 private PCM candidate must not be called public or fully reviewed')
result=text
for row in changes:result=result.replace(row['old'],row['new'])
import re
assert re.findall(r'^- \[[ x]\] [HCF]\d+',text,re.M)==re.findall(r'^- \[[ x]\] [HCF]\d+',result,re.M)
(HERE/'suggested.patch.json').write_text(json.dumps(dict(target='calculations/PLAN.md',expected_sha256=hashlib.sha256(raw).hexdigest(),scope='Prose only; preserve every checkbox; candidate progress clearly separate',replacements=changes),indent=2,ensure_ascii=False)+'\n')
print(len(changes),'guarded suggestions; all checkbox states preserved')
