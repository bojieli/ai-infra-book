"""Extract terminal usage evidence, without copying command/debug histories."""
import argparse, collections, datetime, hashlib, json
from pathlib import Path

def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    index=[]
    for number,p in enumerate(sorted(a.source_root.glob('*/*events.jsonl'))):
        raw=p.read_bytes();lines=raw.splitlines(keepends=True);events=[];offset=0
        for i,line in enumerate(lines):
            j=json.loads(line)
            events.append((i+1,offset,line,j));offset+=len(line)
        types=collections.Counter(e[3]['type'] for e in events)
        # Keep exact protocol lines and the final answer; no intermediate failures copied.
        final=[e for e in events if e[3].get('type')=='item.completed' and e[3].get('item',{}).get('type')=='agent_message']
        final_line=final[-1][0] if final else None
        selected=[e for e in events if e[3]['type'] in ['thread.started','turn.started','turn.completed'] or e[0]==final_line]
        name=f'{number:02d}-{p.parent.name}-{p.stem}.jsonl'
        data=b''.join(e[2] for e in selected);(a.out/name).write_bytes(data)
        task=p.parent/'task.md'
        index.append(dict(source=str(p.relative_to(a.source_root)),source_bytes=len(raw),source_sha256=sha(raw),
                          excerpt=name,excerpt_sha256=sha(data),event_counts=dict(types),
                          selected_lines=[dict(line=e[0],byte_offset=e[1],bytes=len(e[2]),sha256=sha(e[2])) for e in selected],
                          task_file=str(task.relative_to(a.source_root)) if task.exists() else None,
                          task_sha256=sha(task.read_bytes()) if task.exists() else None,
                          quality_accepted=None,invoice_amount=None,subscription_quota=None,monthly_coverage=None))
    (a.out/'index.json').write_text(json.dumps(dict(captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          source_root=str(a.source_root.absolute()),selection='all immediate child *events.jsonl present at capture; not a monthly or random sample',sources=index),indent=2)+'\n')
    print(json.dumps({'source_logs':len(index),'excerpt_bytes':sum((a.out/r['excerpt']).stat().st_size for r in index)}))

if __name__=='__main__':main()
