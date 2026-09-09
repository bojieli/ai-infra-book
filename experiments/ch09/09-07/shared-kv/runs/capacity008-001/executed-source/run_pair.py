"""Execute independently resident engines against one private MP cache daemon."""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import re
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from engine_process import run


def receive(connection, process, timeout=300):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if connection.poll(.2):
            value=connection.recv()
            if 'error' in value:raise RuntimeError(value['error'])
            return value
        if not process.is_alive():raise RuntimeError(f'engine exited {process.exitcode}')
    raise TimeoutError('engine response deadline')


def wait_store(root, request_id, expected_end):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        rows=[]
        for path in root.glob('adapter-*.jsonl'):
            for line in path.read_text().splitlines():
                try:rows.append(json.loads(line))
                except json.JSONDecodeError:continue  # writer may be appending last line
        matched={x['request_id'] for x in rows if re.fullmatch(re.escape(request_id)+r'(?:-[0-9a-f]{8})?',x['request_id'])}
        assert len(matched)<=1, 'ambiguous external/native request mapping'
        submits=[x for x in rows if x['kind']=='store_submit' and x['request_id'] in matched and x['submitted'] and x['end']>=expected_end]
        complete=[x for x in rows if x['kind']=='store_complete' and x['request_id'] in matched and x['success']]
        if submits and any(x['time_s']>=max(s['time_s'] for s in submits) for x in complete):return
        time.sleep(.1)
    raise TimeoutError(f'full prefix store ACK absent: {request_id}')


def main(args):
    root=args.out.absolute();root.mkdir(parents=True,exist_ok=False)
    prepared=json.loads(args.prepared.read_text());model=prepared['model']
    (root/'prepared.json').write_bytes(args.prepared.read_bytes())
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    (root/'executed-hashes.json').write_text(json.dumps(sources,indent=2)+'\n')
    ctx=mp.get_context('spawn');engines=[];daemon=None;daemonlog=None;records=[];metrics_url=None
    def start(name,port):
        parent,child=ctx.Pipe();process=ctx.Process(target=run,args=(child,str(root/name),model,port))
        process.start();child.close();engines.append((process,parent))
        ready=receive(parent,process)
        (root/f'{name}-ready.json').write_text(json.dumps(ready,indent=2)+'\n')
        if 'warmup_token_ids' in prepared:
            parent.send({'op':'generate','request':dict(id=name+'-warmup',
                         prompt_token_ids=prepared['warmup_token_ids'])})
            warmup=receive(parent,process)
            (root/f'{name}-warmup.json').write_text(json.dumps(warmup,indent=2)+'\n')
        return process,parent
    def generate(engine,case,label):
        process,pipe=engine;request=dict(case,id=case['id']+'-'+label)
        pipe.send({'op':'generate','request':request});result=receive(pipe,process)
        result.update(case_id=case['id'],path=label,expected=case['expected'],
                      quality_pass=result['finish_reason']=='stop' and result['text'].strip()==case['expected'])
        records.append(result)
        with (root/'requests.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
        if metrics_url is not None:
            with urllib.request.urlopen(metrics_url,timeout=5) as response:
                data=response.read()
            directory=root/'daemon-metrics';directory.mkdir(exist_ok=True)
            (directory/(result['id']+'.txt')).write_bytes(data)
        print(f'{result["id"]} {result["finish_reason"]} quality={result["quality_pass"]}',flush=True)
        return result
    def stop(engine):
        process,pipe=engine
        if process.is_alive():pipe.send({'op':'shutdown'})
        process.join(30)
        if process.is_alive():raise TimeoutError('engine shutdown')
        assert process.exitcode==0
    try:
        if args.baseline_from:
            old=args.baseline_from
            assert (old/'prepared.json').read_bytes()==args.prepared.read_bytes()
            prior=[json.loads(x) for x in (old/'requests.jsonl').read_text().splitlines()]
            prior=[x for x in prior if x['path']=='baseline']
            assert {x['case_id'] for x in prior}=={x['id'] for x in prepared['cases']}
            assert len(prior)==len(prepared['cases'])
            shutil.copytree(old/'baseline',root/'baseline')
            shutil.copyfile(old/'executed-hashes.json',root/'baseline-origin-hashes.json')
            (root/'baseline-origin.json').write_text(json.dumps({'from':str(old),'reused_without_inference':True})+'\n')
            records.extend(prior)
            (root/'requests.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in prior))
        else:
            baseline=start('baseline',None)
            for case in prepared['cases']:generate(baseline,case,'baseline')
            stop(baseline)
        ports=[]
        while len(ports)<3:
            with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
            if port not in ports:ports.append(port)
        command=[str(Path(sys.executable).absolute().parent/'lmcache'),'server',
                 '--host','127.0.0.1','--port',str(ports[0]),'--http-host','127.0.0.1',
                 '--http-port',str(ports[1]),'--prometheus-port',str(ports[2]),
                 '--chunk-size','256','--l1-size-gb',str(args.pool_gib),'--no-l1-use-lazy',
                 '--eviction-policy','LRU','--supported-transfer-mode','gpu','--max-workers','1',
                 '--lookup-hash-log-dir',str(root/'lookup-hashes')]
        (root/'daemon-command.json').write_text(json.dumps(command,indent=2)+'\n')
        daemonlog=(root/'daemon.log').open('wb');daemon=subprocess.Popen(command,stdout=daemonlog,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+120
        while True:
            if daemon.poll() is not None:raise RuntimeError('daemon exited')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{ports[1]}/healthcheck',timeout=2) as r:
                    if r.status==200:break
            except (urllib.error.URLError,TimeoutError):pass
            if time.monotonic()>deadline:raise TimeoutError('daemon health')
            time.sleep(.25)
        # The HTTP frontend disables the standalone Prometheus HTTP server.
        metrics_url=f'http://127.0.0.1:{ports[1]}/metrics'
        producer=start('producer',ports[0]);consumer=start('consumer',ports[0])
        for case in prepared['cases']:
            if case['kind']!='main':continue
            result=generate(producer,case,'producer')
            wait_store(root/'producer',result['id'],case['input_tokens']//256*256)
            generate(consumer,case,'retrieve')
            generate(consumer,case,'resident')
            miss=next(x for x in prepared['cases'] if x['id']==case['id'].replace('-main','-miss'))
            generate(consumer,miss,'miss')
        stop(consumer);stop(producer)
        (root/'completion.json').write_text(json.dumps(dict(status='requests_completed',requests=len(records),
          quality_pass=sum(r['quality_pass'] for r in records)),indent=2)+'\n')
    finally:
        for process,pipe in engines:
            if process.is_alive():process.terminate();process.join(15)
            if process.is_alive():process.kill();process.join(5)
            pipe.close()
        if daemon is not None:
            if daemon.poll() is None:daemon.terminate()
            try:daemon.wait(timeout=20)
            except subprocess.TimeoutExpired:daemon.kill();daemon.wait(timeout=5)
            (root/'daemon-exit.json').write_text(json.dumps({'returncode':daemon.returncode})+'\n')
        if daemonlog is not None:daemonlog.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--baseline-from',type=Path)
    parser.add_argument('--pool-gib',type=int,choices=[4,8],default=4)
    main(parser.parse_args())
