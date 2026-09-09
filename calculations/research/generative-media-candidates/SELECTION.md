# 开放视频与图像模型：入书选型简报

核对日期2026-09-09。建议正文仅设一小节、四个代表：视频的MiniMax H3与Wan2.2-TI2V-5B，图像的Qwen-Image-2512与FLUX.2 [klein] 4B。这些是有官方配置可审计、结构有教学差异的开放代表，不是未经统一测试的“当前全球SOTA”名单。这里只下载小型原件，没有下载权重。

## 名称和开放边界

- **MiniMax H3名称准确，是视频/音视频生成模型。** [官方发布](https://www.minimax.io/blog/minimax-h3)日期2026-07-31；当时写的是即将开放权重。现在[官方HF仓库](https://huggingface.co/MiniMaxAI/MiniMax-H3)已提供权重、配置和推理代码，固定revision见manifest。应写“开放权重，自定义社区许可”。下载的LICENSE日期为2026-08-02，I.3–5定义适用地域为全球但排除欧盟、英国、韩国、美国；II节说明排除地域可申请另行许可；III.1对商业产品/服务年收入超过2000万美元要求额外书面授权。QA标题与正文表达存在歧义，勿只读标题。其Qwen3-VL-32B编码器单独属于Apache 2.0。Context-IR是托管理解/编排系统，不将其等同已开放基础生成器。
- **Wan2.2-TI2V-5B**：[模型卡](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B)标Apache 2.0，官方[代码仓库](https://github.com/Wan-Video/Wan2.2)的LICENSE.txt已封存。选5B dense联合文生/图生视频版本，而不是混用A14B MoE配置。
- **Qwen-Image-2512**：[模型卡](https://huggingface.co/Qwen/Qwen-Image-2512)标Apache 2.0，官方[代码仓库](https://github.com/QwenLM/Qwen-Image)许可证原件已封存。它是有可下载配置和权重的开放图像代表。
- **FLUX.2 [klein] 4B**：[官方模型卡](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)和LICENSE.md为Apache 2.0；官方[代码仓库](https://github.com/black-forest-labs/flux2)提供参考实现。精确选择4B distilled，不能把9B的非商业许可或base的采样步数套过来。

以上许可证为来源事实摘要，不将“开放代码/权重”扩大为训练数据和全部训练过程也已公开。

## Qwen-Image-2.0未作为可下载权重输入

[官方项目README](https://github.com/QwenLM/Qwen-Image)已公告2026-02-10发布2.0，并链接官方博客与Qwen Chat；[2.0论文](https://arxiv.org/abs/2605.10730)也已存在。这证明模型发布，不证明权重发布。2026-09-09查询官方HF组织Qwen的Qwen-Image相关仓库，得到Image、2512、Edit系列、Layered和Bench，未返回2.0权重仓库（API原始结果封存为`Qwen-Image-official-api-search.json`）。本轮未找到官方可固定revision的2.0权重/config，因此不声明其永不开放，也不把2512写成2.0。待出现官方权重地址再升级定量输入。

## 可量化架构与配置位置

| 模型 | 已封存官方输入 | 可直接读取的结构 | 计算重点 |
| --- | --- | --- | --- |
| MiniMax H3 | `transformer/config.json`、`vae/config.json`、`audio_vae/config.json`、`text_encoder/config.json`、README | 50层，hidden5376，56 heads ×128，FFN14336，2 refiner层；视频24 latent channels，VAE空间16倍/时间4倍，patch1×2×2；音频各声道40 latent/s | hidden5376与attention宽7168不同；音视频与文本联合长度；768p生成＋2K regeneration两阶段；文本编码器与VAE另计 |
| Wan2.2-TI2V-5B | HF `config.json`；官方代码`wan/configs/wan_ti2v_5B.py`、`wan/modules/model.py` | 30层，hidden3072，24heads，FFN14336，48 latent channels；VAE stride(4,16,16)，patch(1,2,2) | 视频token随帧数和分辨率增长；全注意力平方项、每步矩阵工作与采样步数 |
| Qwen-Image-2512 | `transformer/config.json`、`vae/config.json`、`text_encoder/config.json` | 60层，24heads×128=3072，joint text dim3584，in64/out16，patch2 | 双流joint attention、文本+图像长度、CFG分支数与denoise步骤；FFN和packing应再绑定具体实现 |
| FLUX.2-klein-4B | `transformer/config.json`、`vae/config.json`、`text_encoder/config.json`、README | 5双流层＋20单流层，24heads×128，MLP ratio3，in128，joint dim7680，patch1；模型卡示例4步 | 区分双流/单流块和外部latent packing；4步distilled案例体现NFE，不混base版本 |

所有下载URL都固定到完整revision，并在manifest给出sha256与bytes。H3的33B与约13B AdaLN来自作者近似说明，不是配置精确求和。其AdaLN可预计算缓存不等于33B权重文件自动只有20B，也不能忽略预计算阶段。模型卡说明首发实现仅full attention；训练有sparse attention不证明本地公开推理已支持，也不等于GPU 2:4结构化稀疏。

## 建议入书文字

“图像和视频生成把LLM的一次前向扩展为多轮去噪；token还来自空间、时间和音频。以Qwen-Image-2512与FLUX.2-klein-4B对照图像双流/单流结构和采样次数，以Wan2.2-TI2V-5B与MiniMax H3对照视频压缩、联合音视频长度和分阶段生成。全部量化固定官方配置版本，分别列矩阵工作、逻辑读写、权重驻留及NFE，不把公式下界当实际生成速度。H3采用自定义开放权重许可，另三项所选版本为Apache 2.0。”

## SOTA与证据界限

Qwen-Image-2512作者在发布材料中称其AI Arena超过1万轮盲测结果领先开放模型。这是作者在该评测和当时模型集合上的结论，不能写成2026-09-09全球榜首。Wan和FLUX官方材料的先进质量/速度说明也没有在本轮形成同分辨率、帧数、音频、提示集、采样预算和硬件的共同对照。H3的原生音频、多参考、2K regeneration与Wan5B单生成管线任务不同，不能直接用宣传秒数或参数量排SOTA。本文选型依据是可审计和结构覆盖，性能优劣留给有明确协议的实测。
