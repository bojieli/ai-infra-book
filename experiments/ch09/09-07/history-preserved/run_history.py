"""Alternate real frozen Agent requests between independent model engines."""
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from engine_process import run

ROOT=Path(__file__).resolve().parent


def receive(pipe,process,timeout=300):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if pipe.poll(.2):
            value=pipe.recv()
            if 'error' in value:raise RuntimeError(value['error'])
            return value
        if not process.is_alive():raise RuntimeError(f'worker exited: {process.exitcode}')
    raise TimeoutError('engine response')


def wait_store(root,rid,end):
    if end==0:return
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        records=[]
        for p in root.glob('adapter-*.jsonl'):
            for line in p.read_text().splitlines():
                try:x=json.loads(line)
                except json.JSONDecodeError:continue
                if re.fullmatch(re.escape(rid)+r'(?:-[0-9a-f]{8})?',x['request_id']):records.append(x)
        ids={x['request_id'] for x in records};assert len(ids)<=1
        starts=[x for x in records if x['kind']=='store_submit' and x['submitted'] and x['end']>=end]
        finished=[x for x in records if x['kind']=='store_complete' and x['success']]
        if starts and any(x['time_s']>=max(s['time_s'] for s in starts) for x in finished):return
        # If the entire prompt prefix was already in the shared pool, there may
        # be no new store. Keep that separate from a claimed new write ACK.
        if any(x['kind']=='lookup' and x['matched_tokens']>=end for x in records):return
        time.sleep(.05)
    raise TimeoutError('expected prompt-prefix publication not observed')


def execute(root,prepared,condition,rep):
    root.mkdir(parents=True,exist_ok=False);ctx=mp.get_context('spawn')
    engines=[];daemon=None;daemon_log=None;rows=[];metrics_url=None
    try:
        daemon_port=None
        if condition=='shared-apc':
            ports=[]
            while len(ports)<2:
                with socket.socket() as s:s.bind(('127.0.0.1',0));p=s.getsockname()[1]
                if p not in ports:ports.append(p)
            daemon_port,http_port=ports
            command=[str(Path(sys.executable).absolute().parent/'lmcache'),'server',
                '--host','127.0.0.1','--port',str(daemon_port),'--http-host','127.0.0.1',
                '--http-port',str(http_port),'--l1-size-gb','8','--no-l1-use-lazy',
                '--eviction-policy','LRU','--chunk-size','256','--max-workers','1',
                '--supported-transfer-mode','gpu','--lookup-hash-log-dir',str(root/'lookup-hashes')]
            (root/'daemon-command.json').write_text(json.dumps(command,indent=2)+'\n')
            daemon_log=(root/'daemon.log').open('wb');daemon=subprocess.Popen(command,stdout=daemon_log,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+120
            while True:
                if daemon.poll() is not None:raise RuntimeError('daemon exited before ready')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{http_port}/healthcheck',timeout=2) as response:
                        if response.status==200:break
                except (urllib.error.URLError,TimeoutError):pass
                if time.monotonic()>deadline:raise TimeoutError('daemon health')
                time.sleep(.2)
            metrics_url=f'http://127.0.0.1:{http_port}/metrics'
        for index in range(2):
            parent,child=ctx.Pipe();directory=root/f'engine{index}'
            process=ctx.Process(target=run,args=(child,str(directory),prepared['model'],daemon_port,condition!='recompute'))
            process.start();child.close();engines.append((process,parent))
            ready=receive(parent,process);(root/f'engine{index}-ready.json').write_text(json.dumps(ready,indent=2)+'\n')
            parent.send({'op':'generate','max_tokens':16,'request':{
                'id':f'warmup-engine{index}','prompt_token_ids':prepared['warmup_token_ids']}})
            warm=receive(parent,process);(root/f'engine{index}-warmup.json').write_text(json.dumps(warm,indent=2)+'\n')
        begin=time.monotonic()
        for turn,request in enumerate(prepared['requests']):
            index=turn%2;process,pipe=engines[index]
            rid=f'r{rep}-{condition}-{request["id"]}'
            pipe.send({'op':'generate','max_tokens':1200,'request':dict(request,id=rid)})
            result=receive(pipe,process)
            result.update(turn=turn,engine=index,condition=condition,rep=rep,
                          original_ids_equal=result['output_ids']==request['original_output_ids'])
            with (root/'requests.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
            rows.append(result)
            if metrics_url:
                publish_start=time.monotonic()
                wait_store(root/f'engine{index}',rid,len(request['prompt_token_ids'])//256*256)
                with (root/'publication.jsonl').open('a') as f:f.write(json.dumps(dict(id=rid,wait_start_s=publish_start,ready_s=time.monotonic()))+'\n')
                with urllib.request.urlopen(metrics_url,timeout=5) as response:data=response.read()
                directory=root/'metrics';directory.mkdir(exist_ok=True)
                (directory/f'turn-{turn}.txt').write_bytes(data)
            print(f'r{rep} {condition} turn={turn} engine={index} output={len(result["output_ids"])} {result["finish_reason"]}',flush=True)
        end=time.monotonic()
        for process,pipe in engines:
            pipe.send({'op':'shutdown'});process.join(30)
            if process.is_alive():raise TimeoutError('engine shutdown')
            assert process.exitcode==0
        result=dict(rep=rep,condition=condition,requests=len(rows),
                    replay_start_s=begin,replay_end_s=end,replay_wall_s=end-begin,
                    engine_exit_codes=[p.exitcode for p,_ in engines])
        (root/'completion.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:
        for process,pipe in engines:
            if process.is_alive():process.terminate();process.join(15)
            if process.is_alive():process.kill();process.join(5)
            pipe.close()
        if daemon is not None:
            if daemon.poll() is None:daemon.terminate()
            try:daemon.wait(timeout=20)
            except subprocess.TimeoutExpired:daemon.kill();daemon.wait(timeout=5)
            (root/'daemon-exit.json').write_text(json.dumps(dict(returncode=daemon.returncode))+'\n')
        if daemon_log is not None:daemon_log.close()


def main(args):
    root=args.out.absolute();root.mkdir(parents=True,exist_ok=False)
    prepared=json.loads(args.prepared.read_text());(root/'prepared.json').write_bytes(args.prepared.read_bytes())
    source=root/'executed-source';source.mkdir()
    hashes={}
    for p in ROOT.glob('*.py'):
        (source/p.name).write_bytes(p.read_bytes());hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (root/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    results=[]
    # Cyclic order balances which condition runs first without a hidden shuffle.
    for rep in range(prepared['repetitions']):
        conditions=prepared['conditions'][rep:]+prepared['conditions'][:rep]
        for condition in conditions:
            results.append(execute(root/f'r{rep}-{condition}',prepared,condition,rep))
    (root/'completion.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);main(parser.parse_args())
