# 理解之外：Omni、语音、图像与视频生成

选型快照：2026-09-09。正文采用短例和一个对照，重点是执行路径与资源单位，不扩展成模型排行榜。开放权重、公开代码与许可条件分别记录；“领先”限于作者发布时列出的基准与设置，不保证所有任务、语言或后端均最优。官方配置与模型卡已下载，全文权重未下载，也未实跑这些模型。

## 先建工作量，再推资源需求

本书不以模型结构介绍为终点。把一次请求画成阶段依赖图，每个阶段记录矩阵尺寸M/K/N、出现次数、标量/特殊运算、读写接口、输入输出与状态的生命周期。阶段中的自回归时间步、码本内循环、去噪迭代和guidance分支分别展开，再按实际依赖汇总。FLOPs/匹配精度的有效算力与bytes/对应接口有效带宽给出阶段下界；只有明确依赖的串行部分才相加，能重叠的部分按调度计算。峰值容量来自同时存活的张量，不把各阶段容量简单求和；首输出和持续供给使用不同观察窗。

多模态理解尤其要分开“图像预处理→视觉编码→特征合并/投影→语言主干prefill→decode”。视觉embedding数量决定部分语言主干工作，却不包含产生embedding的视觉编码开销。patch、视觉QKV/QK/PV/O/MLP、merger/DeepStack逐步计量后，再计语言部分。Computer Use是包含截图、动作与环境等待的请求轨迹，不由VL标签自动证明能力。已接入[视觉编码逐矩阵报告](../calculations/results/vision-encoding-single.md)：640²单图patch为5,033,164,800 FLOPs、24视觉block为1,218,025,881,600、四merger为87,241,523,200，合计1,310,300,569,600矩阵FLOPs；标量/特殊函数及读写分列。运行`python3 calculations/calc.py vision-encoding --format md`。这是语言prefill前的独立视觉阶段，完整EC为8,192,000bytes；CPU解码/resize与后续语言计算仍要另计。

当前可运行矩阵账：[音频](../calculations/results/omni-audio-book.md)、[Fish](../calculations/results/fish-audio-book.md)、[图像](../calculations/results/image-generation-book.md)、[FLUX](../calculations/results/image-generation-flux.md)、[H3](../calculations/results/video-generation-book.md)、[Wan](../calculations/results/video-generation-wan.md)。运行`python3 calculations/calc.py omni-audio --format md`，或将子命令换为`image-generation`/`video-generation`。图像已包含文本编码、DiT和VAE矩阵/卷积；Omni已包含所列Transformer、桥接与非Transformer codec图。Fish 已补 codec 逐算子子账；视频前后编码/VAE、完整媒体输入与采样及实际运行时仍有缺项，各模块分别声明；不能将已计工作当成完整请求时延。

## Omni：Qwen3-Omni-30B-A3B-Instruct

采用[官方权重与模型卡](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct)作为可复算代表，固定revision `26291f793822fb6be9555850f06dfe95f2d7e695`。模型卡标明Apache-2.0；后续Qwen3.5-Omni报告与在线demo不能自动替代本例的公开权重。Omni接收文本、图像、音频和视频，输出文本与语音；“理解视频”不表示生成视频帧。

按[官方config](../calculations/configs/models/qwen3-omni-30b-a3b-instruct/config.json)分四段：音频／视觉编码，Thinker语义推理，Talker与code predictor，code2wav。Thinker文本部分48层、宽2048、128专家top8；Talker文本部分20层、宽1024、128专家top6；code predictor另有5层、16组code。不能把它视为一个30B文本模型执行一次，也不能把文本token率、codec帧率和PCM采样率混为一谈。分别计每阶段矩阵、KV、跨阶段hidden及首音频等待，模型支持与同机驻留需要另验。

## TTS：Fish Audio S2 Pro

当前核实可下载的Fish Speech系列代表为[Fish Audio S2 Pro](https://huggingface.co/fishaudio/s2-pro)，固定revision `1de9996b6be38b745688de084d87a5633f714e4e`。官方代码、权重开放，但采用[Fish Audio Research License](../calculations/sources/fish-audio-s2-pro/LICENSE.md)，研究／非商业授权与商业用途应按原条款区分，不能写为Apache许可。

[配置](../calculations/configs/models/fish-audio-s2-pro/config.json)包含沿时间轴的36层slow AR与4层audio decoder，两者宽2560；10个码本，音频decoder词表4096。官方说明由slow路径预测主要码本，再由fast路径生成其余9组，随后codec解码为声音。比较TTS时保留“每时间步的慢路径、每步内的快路径、波形解码”三个单位；码本数不是说话速度，生成音频秒数不能直接当语言token数。官方论文给出的RTF与首音频成绩只用于阅读其测试条件，不移植成另一GPU的预测。API出现更高版本名也不自动意味着有对应公开权重。

## 图像与视频：共享迭代去噪，但不共享一次请求的工作量

图像生成需分开文本／视觉条件编码、latent上的多轮Transformer与VAE解码；图像编辑还带参考图条件。视频增加时间latent、跨帧关系及可能的音轨，生成步数、分辨率、帧数和guidance分支都改变工作量。KV随文本逐token增长的计算规则不能直接套到反复更新同一latent序列的去噪过程。

视频主例采用[MiniMax-H3官方仓库](https://huggingface.co/MiniMaxAI/MiniMax-H3)，补[Wan2.2-TI2V-5B](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B)作较小规模对照。H3为音视频生成模型，50层、hidden5376，56个head且head_dim128，注意力投影宽7168，不能直接写成hidden平方；两阶段高分辨率生成应分别计latent尺寸与迭代次数。Wan5B的dim3072、30层、24heads、FFN14336提供更短的逐块核算例。H3采用自定义许可，Wan使用Apache-2.0；权重公开不等于相同的使用授权。

图像主例采用[Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512)，以[FLUX.2 klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)作较小、少步生成对照。前者Transformer为60层、24heads×128、patch2；后者5个双流层加20个单流层、24heads×128、patch1。两者都需联合VAE与packing代码解释in_channels，不能把配置中的64/128直接当原始图片通道数。少步蒸馏和完整步数生成保留各自质量条件，不能只按每步FLOPs排名。已下载的两份官方模型卡/许可证给出Apache-2.0。Qwen-Image-2.0的报告与API发布另作版本跟踪，未核到公开权重时不取代当前可下载主例。

上述是代表性公开模型的条件化选择，不声称跨所有基准均为第一。作者的发布结果要保留基准日期、提示、分辨率、采样步数、guidance及比较版本；后续版本可通过固定配置替换，不改变书中计算方法。

## 放入正文的方式

第2章用此处四类路径补齐架构视野；第3章比较文本token、codec步、去噪步和生成帧的工作单位；第5章以一个真实DiT投影说明hidden不一定等于heads乘head_dim；第8章比较分阶段驻留和streaming；第12章比较首音频、完整图片／视频交付与端云传输。每章只增加一段相关说明，不新增大型核心实验。完整算子与实测覆盖在计算清单中保留待办，不能由配置下载替代验收。

[VL请求账](../calculations/results/vl-request-book.md)现已把视觉阶段与语言计算连接。生成前后阶段方面，图像文本编码器虽只取hidden，固定入口仍算完整词表head；FLUX取9/18/27层特征仍跑完36层。Qwen图像VAE的静态首帧路径与完整3D核padding分别计量。Omni codec与逐帧DAG已接入，先执行完整Thinker/Talker再返回拼接音频的参考入口不当作外部流式首包。详见各CLI更新报告；这些都是源码工作预算，完整延迟仍需各阶段实测。

[视觉阶段图](../calculations/figures/vl-stages/figure.svg)比较同一请求的编码缓存未命中与全命中：省下的仅是视觉编码，图像位置仍参与语言prefill与KV。单图640²的编码矩阵工作为1,310,300,569,600 FLOPs，包括patch投影、24层视觉Transformer、final与三组DeepStack merger；JPEG解码和CPU缩放另计。VL理解能力也不能单独证明完整Computer Use动作闭环能力。

Fish codec现按源码逐步展开168个算子，12帧对应24,576 samples和81,173,200,896矩阵FLOPs；索引查表不做全码本搜索。图像生成的参考非矩阵账把普通算术与特殊函数分列，缓冲区事件图保留CFG跨分支预测和VAE缓存；图中的峰值只覆盖声明的边界张量。H3的30次forward对应31个scheduler网格点，条件化逐步噪声集合共有58个值；假设缓存预计算仍需1,513,840,312,320矩阵FLOPs，不能把这段工作当作免费。上述详细结果均由同名CLI报告与JSON给出。

多模态理解的输入编码进一步分开两个例子：[混合尺寸VL](../calculations/results/vl-request-mixed.md)逐图计视觉attention平方和，缓存命中仅跳过对应图像编码；[Omni输入音频encoder](../calculations/results/omni-audio-encoder-book.md)从有效mel帧起计卷积、分块双向attention及Thinker投影，1000帧得到130个语言输入位置。输出embedding的生成工作与其后语言处理是两段账；输入音频encoder没有自回归decode KV。实际mel提取、媒体传输和完整请求时延继续另计。

[Omni视觉编码](../calculations/results/omni-vision-book.md)现已独立核算图像/视频patch网格：640²静态图1737739468800矩阵FLOPs、400个视觉位置及6553600B完整特征。视频attention按时间块分别计空间平方；时间位置进入Thinker，不能把时间轴再并成一次全视觉attention。缓存命中省编码但仍交付四份特征，DeepStack注入单列。

Wan VAE补有固定源码非矩阵与复制primitive账：按首块/稳定块及增长输出拼接展开，以独立形状记录核对；张量接口读写和原矩阵接口可能重叠，不据其总和预测HBM。图像timestep helper临时存活也已插入原分支事件序列，默认并未抬高VAE主导的声明边界峰值，说明新增中间量不等于把各阶段峰值相加。

[Omni理解请求](../calculations/results/omni-understanding-book.md)已把各编码器连接到Thinker：默认658个prompt位置、32输出，计6327647059968矩阵FLOPs。缓存特征仍需进入语言prefill；音频miss重组可能改变编码分段，必须检查完整缓存身份。算子和声明接口已连接，原始媒体处理、实际路由/采样与服务时延未据此推断。
