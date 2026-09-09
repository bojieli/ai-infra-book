import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
checks=[('session.go','AtMS remains its arrival time','Audio moment AtMS denotes receipt, not physical speaker output.'),('session.go','if moment.Kind == MomentAgentAudio && moment.AtMS >= fromMS','FirstAudioAfter selects an arrival moment.'),('session.go','PlayoutAtMS: playout','Captured playout coordinate comes from software audio recorder.'),('session_audio.go','if atMS < recorder.agentPlayoutMS','Recorder serializes chunks against its previous logical end.'),('session_audio.go','recorder.agentPlayoutMS = atMS + float64(len(copyOfSamples))*1000/24_000','Logical end advances by sample duration at 24kHz; this assignment is not a device callback.'),('session.go','PlaybackMS is how long the input recording was.','PlaybackMS is input recording duration, not response first-play latency.')]
rows=[]
for file,needle,interpretation in checks:
 p=R/'sources'/file;lines=p.read_text().splitlines();matches=[i+1 for i,x in enumerate(lines) if needle in x];assert len(matches)==1,(file,needle,matches)
 rows.append(dict(file=file,line=matches[0],source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),literal=needle,interpretation=interpretation))
(R/'review.json').write_text(json.dumps(dict(kind='source_contract_review_not_runtime',checks=rows,missing_measurements=['actual speaker/device first output','actual flush/mute event','model cancellation acknowledgement and worker release'],scope='Only two saved bench source files; no claim about all project paths.'),indent=2)+'\n');print('Located six source contracts; no runtime timings asserted')
