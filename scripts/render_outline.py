#!/usr/bin/env python3
"""Sync chapter outlines into the existing skeleton and reference index."""
from pathlib import Path
import re,html,json,hashlib
from urllib.parse import quote
R=Path(__file__).resolve().parents[1];O=R/'outlines'
chapters=[]
for p in sorted(O.glob('[0-9]*.md')):
    s=p.read_text();s=re.sub(r'([^\n])\n(#{2,3} )',r'\1\n\n\2',s)
    s=s.replace('扩大型超节点规模','扩大超节点规模').replace('由 实验','由实验').replace('从 实验','从实验')
    p.write_text(s)
    n=int(p.name[:2]);secs=[]
    for m in re.finditer(r'^## (\d+\.\d+) ([^\n]+)\n(.*?)(?=^## |\Z)',s,re.M|re.S):
        body=m[3];subs=[dict(num=x[1],title=x[2],body=x[3].strip()) for x in re.finditer(r'^### (\d+\.\d+\.\d+) ([^\n]+)\n(.*?)(?=^### |\Z)',body,re.M|re.S)]
        secs.append(dict(num=m[1],title=m[2],intro=body.split('### ',1)[0].strip(),subs=subs))
    chapters.append(dict(n=n,path=p,title=s.splitlines()[0].split('章 ',1)[1],lead=s.split('\n\n',2)[2].split('\n## ',1)[0],sections=secs,subcount=sum(len(x['subs']) for x in secs),labs=len(re.findall(r'^> \*\*实验 ',s,re.M)),figs=len(re.findall(r'^> \*\*图 ',s,re.M))))
counts=dict(sections=sum(len(c['sections']) for c in chapters),subsections=sum(c['subcount'] for c in chapters),experiments=sum(c['labs'] for c in chapters),figures=sum(c['figs'] for c in chapters))
summary=f'十三章共 {counts["sections"]} 节、{counts["subsections"]} 个小节、{counts["experiments"]} 项实验与计算、{counts["figures"]} 项配图计划'
h=(R/'skeleton.html').read_text();panorama=re.search(r'<figure class="infra-map".*?</figure>',h,re.S)[0]
def inline(t):
    t=html.escape(t);t=re.sub(r'`([^`]+)`',r'<code>\1</code>',t)
    def link(m):
        u=html.unescape(m[2]);u=u[3:] if u.startswith('../') else 'outlines/'+u if not re.match(r'https?://|#',u) else u
        return '<a href="'+html.escape(u,quote=True)+'">'+m[1]+'</a>'
    t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,t)
    return re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',t)
def blocks(s):
    res=[]
    for part in re.split(r'\n\n+',s.strip()) if s.strip() else []:
        if part.startswith('> '):
            q=re.sub(r'^> ?','',part,flags=re.M).strip();kind='experiment' if q.startswith('**实验 ') else 'figure-plan'
            res.append('<aside class="outline-callout '+kind+'">'+''.join('<p>'+inline(x.replace('\n',' '))+'</p>' for x in q.split('\n\n'))+'</aside>')
        else:res.append('<p>'+inline(part.replace('\n',' '))+'</p>')
    return '\n'.join(res)
parts=['  <section id="chapter-details">\n<h2>章节安排</h2><p class="col">展开各节可查看小节说明，以及紧随内容的实验与配图计划。正式扩写以对应 Markdown 为基础。</p>']
for c in chapters:
    n=c['n'];parts.append(f'<article class="card" id="ch-{n}"><span class="tag">第 {n} 章</span><h3>{html.escape(c["title"])}</h3>'+blocks(c['lead']))
    for sec in c['sections']:
        opened=' open' if sec['num']=='1.1' else ''
        parts.append(f'<details class="outline-section" id="sec-{sec["num"].replace(".","-")}"{opened}><summary>{html.escape(sec["num"]+" "+sec["title"])}</summary><div class="outline-section-body">'+blocks(sec['intro']))
        for sub in sec['subs']:
            parts.append(f'<section class="outline-subsection" id="sec-{sub["num"].replace(".","-")}"><h4>{html.escape(sub["num"]+" "+sub["title"])}</h4>')
            if sub['num']=='1.1.2':parts.append(panorama)
            parts.append(blocks(sub['body'])+'</section>')
        parts.append('</div></details>')
    parts.append(f'<p class="chapter-end"><a href="outlines/{quote(c["path"].name)}">本章 Markdown 大纲</a> · {len(c["sections"])} 节／{c["subcount"]} 小节 · {c["labs"]} 项实验与计算 · {c["figs"]} 项配图计划</p></article>')
parts.append('</section>')
h=re.sub(r'  <section id="chapter-details">.*?(?=  <section id="shared-cases">)','\n'.join(parts)+'\n\n',h,flags=re.S)
h=h.replace('第一章提出 GPT-3 与 UB 的问题，第六章计算协作，第七章解释 NVLink、UB、网络状态与顺序，第十、十一章回到推理和训练。','第五章切分芯片内计算，第六章用真实模型推算 TP／PP／DP／EP，第七章继续计算跨超节点集合通信与网络；第十章研究 PD／AF、持久化与多级 KV，第十一章组织训练与 RL。')
h=h.replace('<li><a href="case-studies/model-operator-examples.md">Qwen3／V4-Flash 模型与算子核对</a></li>','<li><a href="case-studies/model-operator-examples.md">Qwen3／V4-Flash 模型与算子核对</a> · <a href="case-studies/model-parallelism.md">具体模型的并行推算</a></li>')
h=re.sub(r'十三章共 \d+ 节、\d+ 个小节、\d+ 项实验与计算、\d+ 项配图计划',summary,h)
(R/'skeleton.html').write_text(h)

topics={5: '沿真实算子推算复用、融合、编译调优与 Agent 性能反馈，再比较图执行和细粒度流水。', 12: '承接抽象边界上移，讨论调度、模型路由与通用工具环境中的多租户、虚拟化和任务成本。', 1: '从可编程性与系统抽象边界上移解释云到 AI 数据中心的变化，再建立全景与量化方法。', 2: '用 Qwen3 跟算，比较 DeepSeek-V4 与 Kimi K3 的 prefill／decode 计算、常驻容量和访问。', 3: '分推理与训练两块组织请求、阶段与计算预算，结合公开投入理解规模选择。', 4: '从负载和瓶颈解释计算、存储、搬运的架构取舍，将各家代际演进穿插其中。', 8: '用图片精修、ASR／TTS 和 Computer Use，推算传输、执行位置与逐轮交互的优化。', 9: '用 Qwen 贯穿请求调度、近期推测解码和本地量化，计算业务要求下的设备选择。', 10: '沿相同模型和请求推算 PD／AF、少量 GPU 的异构服务、持久化 KV 与共享池。', 11: '用具体训练任务推算资源与期限，以真实后端讨论通信重叠、RL 阶段配比和 Routing Replay。', 6: '用具体模型推算 TP、PP、DP、EP，比较容量、计算、访存与卡间通信。', 7: '沿既定切分计算跨超节点训练、集合通信和八卡服务器间的大模型推理。'}
for p in [R/'README.md',O/'README.md']:
    s=p.read_text()
    for n,t in topics.items():s=re.sub(rf'(^{n}\. .*?：)[^\n]+',lambda m:m[1]+t,s,flags=re.M)
    s=re.sub(r'十三章共 \d+ 节、\d+ 个小节、\d+ 项实验与计算、\d+ 项配图计划',summary,s)
    s=s.replace('第五章沿具体算子讲复用与融合，编译器由手工优化和融合组合的成本引出。第六章扩大到超节点，第七章从超节点边界和跨超节点协作继续展开，第八章再把链路延伸到端侧与用户。','第五章在芯片内切分计算，以分块、布局和融合减少数据搬移。第六章用 Qwen3-8B、235B Qwen／V4-Flash、V4-Pro／Kimi K3 推算 TP、PP、DP、EP；第七章沿同一模型计算跨超节点训练集合通信和八卡服务器之间的推理。第八章把同一模型的执行位置与传输继续延伸到端侧和用户。')
    s=s.replace('第九至十二章依次组织单实例推理、分布式推理、训练和 CPU 任务环境','第九章在既定实例资源上组织请求，第十章集中研究 PD／AF 分离、持久化与多级 KV 缓存，第十一、十二章分别组织训练与 CPU 任务环境')
    if p==R/'README.md':s=s.replace('- [Qwen3／V4-Flash 模型与算子核对](case-studies/model-operator-examples.md)。','- [Qwen3／V4-Flash 模型与算子核对](case-studies/model-operator-examples.md)、[具体模型的并行推算](case-studies/model-parallelism.md)。')
    else:s=s.replace('[模型与算子笔记](../case-studies/model-operator-examples.md)和[训练投入比较]','[模型与算子笔记](../case-studies/model-operator-examples.md)、[并行推算](../case-studies/model-parallelism.md)和[训练投入比较]')
    p.write_text(s)

# Keep all source rows, updating primary chapter use and appending the new fixed configuration.
p=O/'source-map.md';s=p.read_text();meta=json.loads((R/'references/outline-checks/2026-09-07/scaling-history/sources.json').read_text())+json.loads((R/'references/outline-checks/2026-09-07/systems-cases/sources.json').read_text())+json.loads((R/'references/outline-checks/2026-09-07/edge-media/sources.json').read_text())+json.loads((R/'references/outline-checks/2026-09-07/model-accounting/sources.json').read_text())+json.loads((R/'references/outline-checks/2026-09-07/platform-routing/sources.json').read_text())+json.loads((R/'references/outline-checks/2026-09-07/execution-feedback/sources.json').read_text())+json.loads((R/'references/outline-checks/2026-09-07/framework-evolution/sources.json').read_text())
meta += json.loads((R/'references/proceedings/selected-sources.json').read_text()) + json.loads((R/'references/framework-history/2026-09-07/lora/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-07/flashinfer/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-07/startup/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/attention/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/chunk-scheduling/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/overlap-placement/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/rl-consistency/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/collective-paths/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/checkpoint-loading/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/communication-tuning/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/workload-generation/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/speculative-execution/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/rollout-tail/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/offload-execution/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/multimodal-execution/sources.json').read_text())
meta += json.loads((R/'references/interviews/2026-09-08/fourth-pass/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/pcie-staging/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/kernel-orchestration/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/cache-routing/sources.json').read_text())
meta += json.loads((R/'references/framework-history/2026-09-08/structured-generation/sources.json').read_text())
meta += [x for x in json.loads((R/'references/framework-history/2026-09-08/ep-reconfiguration/sources.json').read_text()) if '-pr' not in x['id']]
meta += [x for x in json.loads((R/'references/framework-history/2026-09-08/cache-events/sources.json').read_text()) if x['id'] in ['vllm-current-kv-publisher','dynamo-native-offload-fixed','dynamo-event-recovery-fixed','dynamo-sglang-hicache','dynamo-router-design','dynamo-config-tuning','dynamo-local-indexer','dynamo-recovery-state']]
meta += [x for x in json.loads((R/'references/framework-history/2026-09-08/weight-handoff/sources.json').read_text()) if x['id'] in ['vllm-sleep-current','vllm-transfer-current','vllm-transfer-rdt','vllm-worker-current','vllm-sleep-2025','vllm-rdt-2026','sglang-rl-guide-fixed','verl-v1-async-fixed','verl-vllm-server','verl-sglang-server','sglang-memory-2025','vllm-native-rl-2026-fixed-url']]
meta += json.loads((R/'references/proceedings/ASPLOS/2024/selected-sources.json').read_text())
meta += [x for x in json.loads((R/'references/proceedings/ISCA/2024/selected-sources.json').read_text()) if x['id'] == 'isca24-public-011-author']
meta += [x for x in json.loads((R/'references/proceedings/ASPLOS/2025/selected-sources.json').read_text()) if x['id'] in ['asplos25-public-pdf-94','asplos25-iks-pdf','asplos25-faiss-faiss-indexes','asplos25-faiss-guidelines-to-choose-an-index']]
meta += json.loads((R/'references/outline-checks/2026-09-08/system-abstraction/sources.json').read_text())
for x in meta:
    if f'| `{x["id"]}` |' not in s:
        note='失败／空响应；不作正文证据' if x.get('reading_status','').startswith('failed') else '已归档；固定快照'
        s+=f'| `{x["id"]}` | [{x["title"]}](../{x["file"]}) | 补充 | 补充／版本参照 | {note} |\n'
lines=[]
for line in s.splitlines():
    if line.startswith('| `'):
        cells=[x.strip() for x in line.split('|')[1:-1]];links=re.findall(r'\]\((\.\./[^)]+)\)',cells[1]);cited=[str(c['n']) for c in chapters if any(u in c['path'].read_text() for u in links)]
        if cited:cells[3]=','.join(cited)
        elif re.match(r'^\d',cells[3]):cells[3]='补充／版本参照'
        line='| '+' | '.join(cells)+' |'
    lines.append(line)
p.write_text('\n'.join(lines)+'\n')
for x in meta:assert hashlib.sha256((R/x['file']).read_bytes()).hexdigest()==x['sha256']
print(summary)
