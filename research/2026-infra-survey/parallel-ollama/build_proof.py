from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
selections={
 'blog-thinking.txt':[[1,66]],'blog-gguf.txt':[[1,54]],'docs-thinking.txt':[[1,60],[80,260],[420,448]],'docs-gpu.txt':[[290,408]],'qwen3-author.txt':[[110,121]],
 'current-envconfig.go':[[173,196],[230,236],[350,363]],'current-cmd.go':[[750,780],[1770,1855]],'current-types.go':[[1155,1265]],
 'current-discover-vulkan.go':[[1,144]],'current-discover-gpu.go':[[1,70]],
 'current-discover-llama_server.go':[[203,225],[365,395],[478,489]],'current-discover-llama_server_test.go':[[109,142],[388,439]],
 'current-discover-runner.go':[[85,135],[208,245],[382,440],[612,635]],'current-discover-runner_test.go':[[120,200]],
 'current-ml-device.go':[[175,229],[401,450]],'current-ml-device_test.go':[[112,184]],'current-llm-vulkan_windows.go':[[1,109]],
 '0126-discover-gpu.go':[[35,85],[128,160]],'090-routes.go':[[183,200],[258,293],[1510,1530]],
 'current-llm-llama_server.go':[[105,120],[1488,1518],[1990,2048],[2140,2220]],'current-llm-llama_server_test.go':[[3580,3642]],
 'current-routes.go':[[2370,2401],[2627,2678],[2970,3055]],'qwen3-report-p11.txt':None,
}
rows=[]
for name,rr in selections.items():
 p=D/name;b=p.read_bytes();ls=b.decode().splitlines();rr=rr or [[1,len(ls)]]
 rows.append(dict(file=name,bytes=len(b),sha256=sha(b),ranges=[dict(first=a,last=z,range_sha256=sha(('\n'.join(ls[a-1:z])+'\n').encode())) for a,z in rr],method='static text reading; no downloaded code executed'))
book=[]
for rel,rr in [('research/2026-infra-survey/framework-coverage.md',None),('case-studies/framework-evolution.md',[[52,70]]),('outlines/extensions/05-算子与运行时.md',[[303,317]]),('outlines/extensions/08-单实例推理.md',[[247,277]]),('outlines/extensions/11-资源调度与运行环境.md',[[243,283]])]:
 p=R/rel;b=p.read_bytes();dst=D/'book-snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
 book.append(dict(original=rel,file=str(dst.relative_to(D)),sha256=sha(b),bytes=len(b),mtime_ns=p.stat().st_mtime_ns,read_ranges=rr or [[1,len(b.decode().splitlines())]]))
refs={}
for t in ['v0.9.0','v0.12.6','v0.30.0']:
 x=json.loads((D/(t+'-ref.json')).read_text());refs[t]=x['object']['sha']
paper=D/'qwen3-report.pdf';view=D/'qwen3-report-p11.png'
proof=dict(completed_at=datetime.now(timezone.utc).isoformat(),scope='two Ollama evolution topics; not full release history',fixed_current_commit=json.loads((D/'current-commit.json').read_text())['sha'],historical_refs=refs,selections=rows,book_snapshots=book,paper=dict(file=paper.name,sha256=sha(paper.read_bytes()),bytes=paper.stat().st_size,source_kind='copied existing repository archive; no new HTTP retrieval claim',original='references/files/papers/qwen3.pdf',document_id='arXiv:2505.09388v1',physical_pages_read=[11],viewed_image=dict(file=view.name,sha256=sha(view.read_bytes()),bytes=view.stat().st_size,actually_viewed=True)),metadata_read=['current-commit.json','current-tree.json','release-0126.json','release-0300.json','release-090.json',*[t+'-ref.json' for t in refs]],source_probe_failures=[dict(file='current-renderers-qwen3.go',status=404,adopted=False)],execution=dict(downloaded_code=False,framework_tests=False,model_download=False,gpu=False,self_written_archival_verifier=True),authorization=dict(write_scope='research/2026-infra-survey/parallel-ollama/',shared_outlines_modified=False,git_actions=False),limitations=['Only selected code paths inspected; no universal absence or model support claims','Vulkan discovery/selection tests are not hardware compatibility/performance results','Thinking template controls are not exact threshold-budget controller','Ollama native upstream token accounting and cloud billing not fully audited'])
(D/'reading-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
