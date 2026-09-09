"""Reclaim only allowlisted, exited experiment creators' unmapped tmpfs pools."""
from pathlib import Path
import json,os,time,argparse
p=argparse.ArgumentParser();p.add_argument('--delete',action='store_true');a=p.parse_args();root=Path(__file__).absolute().parent;targets=json.loads((root/'targets.json').read_text());names={x['name'] for x in targets}
def available():return int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
before=available();references=[];errors=[];stats=[]
for x in targets:
 path=Path('/dev/shm')/x['name'];s=path.stat();assert not Path('/proc',str(x['creator_pid'])).exists();assert s.st_uid==1000 and s.st_nlink==1 and not path.is_symlink();stats.append(dict(name=x['name'],device=s.st_dev,inode=s.st_ino,size=s.st_size,allocated_bytes=s.st_blocks*512,mtime_ns=s.st_mtime_ns))
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  for line in (proc/'maps').read_text().splitlines():
   if any('/dev/shm/'+n in line for n in names):references.append(dict(pid=int(proc.name),kind='map',path=line.split()[-1]))
  for fd in (proc/'fd').iterdir():
   try:
    target=os.readlink(fd)
    if any('/dev/shm/'+n in target for n in names):references.append(dict(pid=int(proc.name),kind='fd',path=target))
   except FileNotFoundError:pass
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:errors.append(int(proc.name))
assert not references and not errors,(references,errors)
result=dict(mode='delete' if a.delete else 'inspect',time_unix=time.time(),targets=stats,references=references,unreadable_pids=errors,available_before_bytes=before)
if a.delete:
 for x,s in zip(targets,stats):
  path=Path('/dev/shm')/x['name'];now=path.stat();assert (now.st_dev,now.st_ino,now.st_size,now.st_mtime_ns)==(s['device'],s['inode'],s['size'],s['mtime_ns']);assert not Path('/proc',str(x['creator_pid'])).exists();path.unlink()
 result['all_target_paths_absent']=all(not (Path('/dev/shm')/x['name']).exists() for x in targets)
result['available_after_bytes']=available();result['target_allocated_bytes']=sum(x['allocated_bytes'] for x in stats)
(root/('deleted.json' if a.delete else 'inspection.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='targets'}))
