"""Make a valid fixed-length WAV from the last complete streaming response."""
import hashlib,json,struct,wave
from pathlib import Path
B=Path(__file__).absolute().parent
source=B/'runs/3-stream-true/response.wav';raw=source.read_bytes();pcm=raw[44:]
assert raw[:4]==b'RIFF' and raw[8:12]==b'WAVE' and raw[40:44]==b'\xff'*4
out=B/'replay';out.mkdir(exist_ok=True)
with wave.open(str(out/'audio.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100);w.writeframes(pcm)
with wave.open(str(out/'audio.wav'),'rb') as w:assert w.readframes(w.getnframes())==pcm
(out/'source.json').write_text(json.dumps(dict(source=str(source.relative_to(B)),source_sha256=hashlib.sha256(raw).hexdigest(),
 pcm_sha256=hashlib.sha256(pcm).hexdigest(),wav_sha256=hashlib.sha256((out/'audio.wav').read_bytes()).hexdigest(),
 pcm_bytes=len(pcm),sample_rate=44100,channels=1,bits=16,transformation='Only replace RIFF/data placeholder lengths with exact PCM length; samples unchanged.'),indent=2)+'\n')
