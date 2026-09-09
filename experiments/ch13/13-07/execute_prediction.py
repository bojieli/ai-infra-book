"""Run the frozen, previously unseen K192 experiment only with --execute."""
import argparse,datetime,hashlib,importlib.util,json,time
from pathlib import Path
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
if not a.execute:raise SystemExit('Prediction only; no model run without --execute.')
forecast=json.loads((B/'prediction.json').read_text());assert hashlib.sha256((B/'prediction.json').read_bytes()).hexdigest()==(B/'prediction.sha256').read_text().strip()
for n,h in forecast['frozen_files_sha256'].items():assert hashlib.sha256((B/n).read_bytes()).hexdigest()==h,n
now=datetime.datetime.now(datetime.timezone.utc);assert now>datetime.datetime.fromisoformat(forecast['created_utc']);root=B/a.name;root.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('prediction_manager',B/'runner/launch.py');manager=importlib.util.module_from_spec(spec);spec.loader.exec_module(manager)
plan=json.loads((B/'future-plan.json').read_text());manager.dump(root/'plan.json',plan);manager.dump(root/'source-sha.json',forecast['frozen_files_sha256']);manager.dump(root/'provenance.json',dict(prediction_sha256=(B/'prediction.sha256').read_text().strip(),started_utc=now.isoformat(),scope='new K192 five-trial experiment, all frozen paths'))
start=time.monotonic()
for job in plan:manager.run_case(root/job['request_id'],job,start)
manager.dump(root/'completion.json',dict(done=True,paths=len(plan),wall_s=time.monotonic()-start,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
