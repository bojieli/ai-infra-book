import json, os, resource, sys, time
from pathlib import Path
import tools
kind, directory = sys.argv[1:]
buffer=bytearray(16*1024**2)
print(json.dumps(dict(event='ready',pid=os.getpid(),t_ns=time.perf_counter_ns(),kind=kind,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
for line in sys.stdin:
    msg=json.loads(line)
    if msg.get('stop'): break
    start=time.perf_counter_ns()
    try: reply=tools.execute(msg['action'],Path(directory))
    except Exception as e:reply={'error':type(e).__name__+': '+str(e)}
    print(json.dumps(dict(event='reply',start_ns=start,end_ns=time.perf_counter_ns(),reply=reply,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
