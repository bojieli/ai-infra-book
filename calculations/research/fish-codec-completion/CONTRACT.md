# C78 Fish codec completion: selected remaining wrapper stage

审计结论：现有omni_audio.omni_codec_operators(codec_kind='fish')已经逐项算RVQ semantic1/residual9索引clamp、lookup、10个out_proj、post Transformer、ConvNeXt四倍恢复、DAC卷积/ConvTranspose/Snake/residual/tanh与weight_norm。codec每frame输出2048 samples@44100Hz，不能再实现一份重复主图。

本候选仅补固定text2semantic CLI的实际code chunk收集→单次codec→CPU waveform/export输入。接口`calculate(chunk_frames=[21,22],waveform_dtype='bf16',code_element_bytes=8)`。显式输入官方无条件切片y[1:,prompt_length:-1]之后实际返回的每个sample代码帧数（returned_y_length−prompt_length−1），被删除末步不保证为terminal；不把文本chunk_length=300/512猜成音频帧，不猜prompt dtype，code可声明int32或int64。选择GPU路径、codec已加载、output打开、num_samples1。

官方source证据：
- text2semantic/inference.py 440–444：decode_to_audio调用codec.from_indices(codes[None])，切出mono waveform。
- 708–723：`y[1:,prompt_length:-1].clone()`；非负assert；conversation接受codes.cpu()；sample yield仍返回原device codes。
- 925–955：sample仅append；next才cat所有chunks；merged_codes.cpu().numpy()先给NPY，再一次decode_to_audio；wave导出为audio.cpu().float().numpy()。
- dac/inference.py 113–122：standalone是fake_audios[0,0].float().cpu().numpy()，BF16时先device转FP32再D2H，与上述CLI低位D2H后CPU转换顺序不同。

来源均复用已锁generative-audio-analysis sources.lock，calculate经omni_audio.evidence验证SHA+bytes。source-lock.json单独列此次直接路径及YAML，公共来源不修改。

产物wrapper_stages逐样本clone/非负比较+归约/CPU conversation复制/保留代码、next cat、NPY输入CPU复制、单次codec、wave CPU转换。codec_operations是既有账复用；合入时作为现有Fish codec分项的外层接口，不重复加codec矩阵，也不重复AR阶段。host_array_alias不是NumPy额外copy。

一例21+22帧：43×2048=88064样本；int64码本10列，代码两次D2H共6880B；BF16 waveform D2H176128B，随后CPU FP32输出352256B。standalone dac路径wave D2H352256B。code list+merged暂时共同拥有6880B，但不是整个请求峰值，生成器挂起时y/encoded等仍可能保留。

CLI首波形必须在全部sample代码chunk和next之后，不是第一个sample到达即首音频。外部transport、文件编码、实际时长/TTFA/RTF均无实测故null。输入样本数精确不等于文件字节，soundfile subtype/容器与IO缓冲不推断。模型加载、tokenizer、真实生成时间、CPU解码/编码等在范围外。

4项测试验证合并codec只一次、精确样本时钟、两路径D2H/cast顺序、int32/64 payload与代码list持有、非法输入。`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=calculations/src python3 -m unittest discover -s calculations/research/fish-codec-completion -v`。shared未改。

独立review文字修正：max_new_tokens=1的源码decode_n_tokens可能cat空list失败，不作为成功零帧路径；本接口只接受实际成功返回的正帧数，不推断预算对应音频帧数。
