"""Explicit chunk pipeline, jitter-buffer playback and a mute-only interruption.

All durations are scenario inputs. This does not model an acoustic network or
claim cancellation of GPU work when the audio device is muted.
"""
from collections import defaultdict
from ..units import positive_int, ceil_div


def calculate(frame_ns: int = 20_000_000, model_ns: list | None = None,
              network_delay_ns: list | None = None, send_ns: int = 1_000_000,
              jitter_buffer_ns: int = 40_000_000, sample_rate: int = 24000,
              channels: int = 1, sample_bytes: int = 2,
              interrupt_ns: int | None = None, control_delay_ns: int = 5_000_000,
              device_quantum_ns: int = 10_000_000) -> dict:
    for name, value in [('frame_ns',frame_ns),('sample_rate',sample_rate),('channels',channels),
                        ('sample_bytes',sample_bytes),('device_quantum_ns',device_quantum_ns)]:
        positive_int(value,name)
    for name,value in [('send_ns',send_ns),('jitter_buffer_ns',jitter_buffer_ns),('control_delay_ns',control_delay_ns)]:
        positive_int(value,name,allow_zero=True)
    if interrupt_ns is not None: positive_int(interrupt_ns,'interrupt_ns',allow_zero=True)
    durations = [12_000_000]*8 if model_ns is None else model_ns
    delays = [5_000_000,5_000_000,50_000_000,5_000_000,5_000_000,5_000_000,5_000_000,5_000_000] if network_delay_ns is None else network_delay_ns
    if not isinstance(durations,list) or not durations or not isinstance(delays,list) or len(delays)!=len(durations):
        raise ValueError('Model durations and network delays need equal nonempty lists')
    for value in durations: positive_int(value,'model duration')
    for value in delays: positive_int(value,'network delay',allow_zero=True)
    samples_numerator=sample_rate*frame_ns
    if samples_numerator % 1_000_000_000:
        raise ValueError('Audio chunk duration must contain an integral number of samples')
    chunk_bytes=(samples_numerator//1_000_000_000)*channels*sample_bytes
    model_free=link_free=0
    rows=[]
    for i,(duration,delay) in enumerate(zip(durations,delays)):
        capture=(i+1)*frame_ns
        start=max(capture,model_free)
        model_free=start+duration
        send_start=max(model_free,link_free)
        link_free=send_start+send_ns
        rows.append(dict(chunk=i,capture_ready_ns=capture,model_start_ns=start,model_end_ns=model_free,
                         send_start_ns=send_start,send_end_ns=link_free,arrival_ns=link_free+delay))
    first_play=rows[0]['arrival_ns']+jitter_buffer_ns
    play_free=first_play
    events=defaultdict(int)
    for i,row in enumerate(rows):
        deadline=first_play+i*frame_ns
        start=max(play_free,row['arrival_ns'])
        row.update(deadline_ns=deadline,deadline_miss=row['arrival_ns']>deadline,
                   playback_start_ns=start,playback_end_ns=start+frame_ns,
                   new_stall_ns=start-play_free,playback_lateness_ns=start-deadline)
        play_free=start+frame_ns
        # Reorder/ready queue only: remove when playback starts, not when it ends.
        if start>row['arrival_ns']:
            events[row['arrival_ns']]+=chunk_bytes
            events[start]-=chunk_bytes
    queued=peak=0
    for _,delta in sorted(events.items()):
        queued+=delta
        peak=max(peak,queued)
    cutoff=None if interrupt_ns is None else ceil_div(interrupt_ns+control_delay_ns,device_quantum_ns)*device_quantum_ns
    audible_after=None if cutoff is None else sum(max(0,min(r['playback_end_ns'],cutoff)-max(r['playback_start_ns'],interrupt_ns)) for r in rows)
    return dict(schema_version=1,calculation='audio-chunk-timing',model='',
                scenario=dict(frame_ns=frame_ns,model_ns=durations,network_delay_ns=delays,send_ns=send_ns,
                              jitter_buffer_ns=jitter_buffer_ns,sample_rate=sample_rate,channels=channels,
                              sample_bytes=sample_bytes,interrupt_ns=interrupt_ns,control_delay_ns=control_delay_ns,
                              device_quantum_ns=device_quantum_ns),sources=[],audio_chunks=rows,
                summary=dict(chunks=len(rows),frame_rate_per_second=1e9/frame_ns,pcm_chunk_bytes=chunk_bytes,
                             source_audio_duration_ns=len(rows)*frame_ns,
                             first_playback_from_time_zero_ns=first_play,
                             first_chunk_capture_to_playback_ns=first_play-frame_ns,
                             deadline_misses=sum(r['deadline_miss'] for r in rows),
                             total_playback_stall_ns=sum(r['new_stall_ns'] for r in rows),
                             maximum_playback_lateness_ns=max(r['playback_lateness_ns'] for r in rows),
                             baseline_playback_finish_ns=play_free,
                             baseline_ready_queue_peak_bytes=peak,
                             mute_effective_ns=cutoff,
                             interrupt_to_mute_ns=None if cutoff is None else cutoff-interrupt_ns,
                             audible_after_interrupt_ns=audible_after,
                             cancelled_gpu_work=None),
                assumptions=[
                    '全部时长是明确教学输入，未引用模型或设备峰值。每个输入帧采集完才就绪；单模型阶段和单发送链路各自串行，阶段间可重叠，传播延迟逐帧变化且允许乱序到达。',
                    '输入帧和输出音频块一一对应且等长，是本情景的简化；PCM 容量由显式采样率／声道／元素字节计算，不冒充压缩码率或声学 token 数。',
                    '首次播放在第 0 块到达后等待固定 jitter buffer。截止时刻固定为首次播放+i*块长；实际播放器按序等待，缺块时停顿而不丢弃，后续时间线整体后移。固定截止未到与新增播放停顿分列，不能重复相加。',
                    'ready queue 包含已到达但未开始播放的块，支持乱序缓存，同刻释放后复用；不包含正在播放块、传输中数据、模型状态、采集缓冲或完整设备内存。',
                    '可选打断只将基线播放投影为静音：在 interrupt+control_delay 后下一个绝对设备量子边界生效。统计到静音的响应时间与其中实际仍有声音的时长；间隔可能含原有播放停顿。',
                    '打断不重新调度模型／网络，也不宣称取消 GPU 工作或回收缓存。播放时序和队列峰值仍标为未打断基线；主动取消、输出 flush 的真实实现另需记录。',
                ])
