#!/usr/bin/env python3
"""Analyze saved arrival records; never infer physical playback or cancellation."""
import hashlib
import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent

def stats(values):
    return {'count': len(values), 'min': min(values), 'median': median(values),
            'max': max(values)} if values else {'count': 0}

def main():
    metadata = json.loads((ROOT / 'source-metadata.json').read_text())
    results = []
    for entry in metadata['files']:
        path = ROOT / 'sources' / Path(entry['relative_path']).name
        raw = path.read_bytes()
        assert len(raw) == entry['bytes']
        assert hashlib.sha256(raw).hexdigest() == entry['sha256']
        source = json.loads(raw)
        moments = source['moments']
        times = [m['at_ms'] for m in moments]
        assert all(math.isfinite(t) and t >= 0 for t in times)
        assert times == sorted(times), 'do not silently sort a malformed timeline'
        audio = [m for m in moments if m['kind'] == 'agent_audio']
        assert all(math.isfinite(m['audio_ms']) and m['audio_ms'] > 0 for m in audio)
        starts = [m['at_ms'] for m in moments if m['kind'] == 'user_speech_started']
        stops = [m['at_ms'] for m in moments if m['kind'] == 'user_speech_stopped']
        assert len(starts) == len(stops) == 2
        assert starts[0] < stops[0] < starts[1] < stops[1]
        initial = [m for m in audio if stops[0] <= m['at_ms'] < starts[1]]
        gaps = [b['at_ms']-a['at_ms'] for a,b in zip(initial,initial[1:])]
        # Receiver arrival spacing minus previous chunk's declared duration.
        # This is not device underrun: no device queue or playback clock exists here.
        residuals = [b['at_ms']-a['at_ms']-a['audio_ms'] for a,b in zip(initial,initial[1:])]
        overlap = [m for m in audio if starts[1] <= m['at_ms'] < stops[1]]
        results.append({
            'record': path.name, 'sha256': entry['sha256'],
            'all_audio_chunks': len(audio),
            'initial_window_start_ms': stops[0], 'initial_window_end_exclusive_ms': starts[1],
            'first_audio_arrival_ms': initial[0]['at_ms'],
            'first_audio_after_first_user_stop_ms': initial[0]['at_ms']-stops[0],
            'initial_window_audio_chunks': len(initial),
            'initial_window_interarrival_ms': stats(gaps),
            'initial_window_arrival_minus_previous_duration_ms': stats(residuals),
            'second_user_speech_window_audio_chunks': len(overlap),
            'second_user_speech_window_ms': [starts[1], stops[1]],
            'actual_first_playback_ms': None, 'cancel_ack_ms': None,
            'physical_silence_latency_ms': None, 'compute_exit_ms': None,
            'execution_evidence_error': source.get('execution_evidence_error'),
            'runtime_identity': source.get('runtime'),
        })
    output = {'scope': 'Historical receiver-arrival records; not a controlled model/network/buffer comparison',
              'records': results}
    (ROOT/'summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
