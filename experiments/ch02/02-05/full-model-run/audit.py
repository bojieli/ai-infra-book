"""Read-only toolchain/source/cache audit; no compilation or GPU model."""
import argparse,base64,importlib.metadata,signal,sys
from common import *
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 out=a.out.resolve();assert out.is_relative_to(BASE) and out!=BASE;out.mkdir(parents=True,exist_ok=False)
 prepared=BASE/'prepared';assert (prepared/'completion.json').is_file()
 dist=importlib.metadata.distribution('sglang');records=[]
 for row in json.loads((prepared/'sources.json').read_text()):
  p=Path(row['path']);rel=str(p.relative_to(Path(dist.locate_file(''))));record=next((f.hash.value for f in dist.files if str(f)==rel and f.hash),None)
  records.append(dict(path=str(p),sha256=sha(p),matches_prepared=sha(p)==row['sha256'],matches_distribution_record=base64.urlsafe_b64encode(bytes.fromhex(sha(p))).decode().rstrip('=')==record if record else None))
 cccl=TOOLS/'sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl'
 seeds=[]
 for rel in ['jit-preflight/tvm-cache','jit-mhc-preflight/tilelang-cache']:
  for f in sorted((NATIVE/rel).rglob('*')):
   if f.is_file():seeds.append(dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f)))
 basis=[]
 for p in [NATIVE/'attempt-05/run.py',NATIVE/'attempt-05/launch.py',NATIVE/'attempt-05/results/config.json',NATIVE/'attempt-05/results/ready.json',NATIVE.parent/'runtime-preflight/resolved-config.json',NATIVE.parent/'full-model-readiness/results/observation.json']:
  if p.is_file():basis.append(dict(path=str(p),sha256=sha(p)))
 save(out/'toolchain-audit.json',dict(status='read_only_no_jit_no_model',time=time.time(),python=sys.executable,python_version=sys.version,cuda_home=str(TOOLS/'flashinfer-cuda130/nvidia/cu13'),nvcc_version=command([str(TOOLS/'flashinfer-cuda130/nvidia/cu13/bin/nvcc'),'--version']),cccl=str(cccl),cccl_nv_target_sha256=sha(cccl/'nv/target'),native_overlay_target=str((NATIVE/'include-overlay/cccl').resolve()),source_records=records,cache_seed_files=seeds,basis_files=basis,pidfd_open_available=hasattr(os,'pidfd_open'),pidfd_signal_available=hasattr(signal,'pidfd_send_signal')))
 save(out/'resources-current.json',snapshot())
if __name__=='__main__':main()
