"""Build this bounded local packet; never writes a shared index."""
from pathlib import Path
import hashlib,json,datetime,subprocess
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent
ROOT=P.parents[4]
def h(b):return hashlib.sha256(b).hexdigest()
def proof(f):
 f=Path(f);b=f.read_bytes();return {'file':str(f.relative_to(ROOT)),'bytes':len(b),'sha256':h(b)}
def dump(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def get_text(s,sel):return s.select_one(sel).get_text(' ',strip=True)
manifest=json.loads((ROOT/'references/proceedings/ASPLOS/2025/manifest.json').read_text())
M={r['program_order']:r for r in manifest['papers']}
sources=[]
for f in sorted(P.glob('sources-*.json.results.json')):
 for r in json.loads(f.read_text()):
  r['file']=str(Path(r['file']).relative_to(ROOT));sources.append(r)
records=[]
for order,pdfname,arxiv,version,pages in [(145,'145-author-paper','2411.08300',4,[]),(175,'175-arxiv-v3-paper','2407.21255',3,[4,8,9,11])]:
 formal=M[order];html=P/f'{order:03}-arxiv-landing.html';s=BeautifulSoup(html.read_bytes(),'html.parser')
 a=s.select_one('blockquote.abstract');a.select_one('.descriptor').decompose();abstract=a.get_text(' ',strip=True)
 af=P/f'{order:03}-abstract.txt';af.write_text(abstract+'\n')
 pdf=P/(pdfname+'.pdf')
 layout=pdf.with_suffix('.layout.txt')
 if not layout.exists():subprocess.run(['pdftotext','-layout',str(pdf),str(layout)],check=True)
 authornames=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in formal['author_metadata']]
 fullpages=int(subprocess.check_output(['pdfinfo',str(pdf)],text=True).split('Pages:')[1].splitlines()[0])
 record={'program_order':order,'doi':formal['doi'],'title':formal['title'],'authors':authornames,
 'source_file':str(html.relative_to(ROOT)),'source_sha256':h(html.read_bytes()),
 'extraction':'HTML blockquote.abstract; remove .descriptor; BeautifulSoup get_text(" ", strip=True). No search snippet or PDF-cleaned substitute.',
 'source_url':f'https://arxiv.org/abs/{arxiv}','version_url':f'https://arxiv.org/abs/{arxiv}v{version}',
 'version':f'arXiv:{arxiv}v{version}','history':get_text(s,'.submission-history'),
 'abstract':abstract,'abstract_sha256':h(abstract.encode()),'abstract_text_file':proof(af),
 'reading_status':'full_abstract_and_selected_sections_read' if pages else 'full_abstract_read',
 'read_date':datetime.date.today().isoformat(),'identity':{'official_program_doi':formal['doi'],
 'publisher_title':formal['publisher_title'],'publisher_author_names':authornames,'pdf_title_doi_visually_verified':True,
 'html_title':get_text(s,'h1.title'),'html_authors':get_text(s,'.authors'),
 'normalization':'Aqua PDF small-caps font extracts as Aqa; normalize only for identity comparison, preserve raw PDF/text.' if order==175 else 'Whitespace/title-line joins only.',
 'secondary_doi_bridge':'arXiv .metatable Related DOI' if order==145 else '175-author-home.html author publication link and PDF p1 ACM reference'},
 'representative_pdf':{**proof(pdf),'pages':fullpages,'text':proof(pdf.with_suffix('.txt')),'layout_text':proof(layout),'first_page_text':proof(pdf.with_suffix('.first.txt'))},
 'selected_reading':{'physical_pdf_pages':pages,'scope':'Complete text of physical PDF pages 4,8,9,11 read, including figures; p1 separately for abstract/identity and noted KV error. Other pages keyword-location only; not full-paper reading.' if pages else 'Complete HTML abstract and PDF title/abstract/identity on p1 only. No later body reading.',
 'page_text':{str(n):proof(P/f'{pdfname}.p{n:02}.txt') for n in pages},
 'viewed_page_images':{'1':{**proof(P/f'{pdfname}.p1.png'),'actually_viewed':True},**{str(n):{**proof(P/f'{pdfname}.p{n:02}.png'),'actually_viewed':True} for n in pages}}},
 'version_notes':(['Purdue author-hosted 18-page publication-layout PDF carries official DOI. HTML is arXiv v4 dated 2025-02-13; no assertion of byte equality with author PDF.','Only abstract claims read; FPGA unloaded fabric latency and larger-scale simulation evidence kept separate.'] if order==145 else ['Explicit arXiv v3 dated 2025-02-21; formal DOI and all authors verified on PDF p1. Earlier title/abstract versions not included or counted.','Paper implementation uses vLLM v0.5.3 plus author changes; no present upstream availability claim, source checkout, execution or benchmark reproduction.','H100 end-to-end platform and A100 microbenchmark platform are distinct.','PDF p1 KV-cache quadratic-capacity statement is retained in raw source but rejected for ordinary fixed-shape uncompressed KV; independent linear capacity arithmetic in calculations.json.']),
 'editorial_decision':('候选：用内存池短请求说明带宽充足仍需拆分固定延迟；未读正文，不作部署或端到端延迟结论。' if order==145 else '候选：用邻卡显存卸载贯通容量、分页大小、公平调度与共置干扰；保留旧版框架改造及具体评测边界，不增加大纲。'),
 'editorial_notes':str((P/'READINGS.md').relative_to(ROOT))}
 records.append(record)
formal=M[23]
gap={'program_order':23,'doi':formal['doi'],'title':formal['title'],'authors':[' '.join([a.get('given',''),a.get('family','')]).strip() for a in formal['author_metadata']],
 'abstract_read':False,'representative_pdf':None,'selected_reading':None,'reading_status':'primary_identity_only_abstract_gap',
 'candidate_reason':'训练对象存储与 DPU 数据通路有关；仅凭题名选入定位，未继承第三方性能数字。',
 'gap_reason':'Author publication entry has DOI/title/all authors but no complete abstract or public PDF; publisher Crossref message.abstract absent; ACM landing and PDF returned HTTP 403. Third-party summaries rejected as primary abstract evidence.',
 'identity_sources':[proof(P/'023-author-publications.html'),proof(P/'023-crossref.html')],
 'failed_sources':[proof(P/'023-acm-landing.html'),proof(P/'023-acm-pdf.html')],
 'unresolved':'Find author public full text or publisher original complete abstract; do not increase read counts.'}
calcs={'scope':'Independent arithmetic under explicit teaching assumptions; not paper benchmark reproduction. MB/GB decimal for transfer budget; GiB binary for KV capacity.',
 'assumptions':{'payload_bytes':64,'hypothetical_link_bits_per_second':100_000_000_000,'small_copy_bytes':4_000_000,'small_copy_bytes_per_second':50_000_000_000,'coalesced_copy_bytes':64_000_000,'coalesced_copy_bytes_per_second':200_000_000_000,'layers':32,'kv_heads':8,'head_dim':128,'bytes_per_element':2,'tokens':[8192,16384]},
 'results':{'serialization_ns':5.12,'small_copy_count':16,'individual_copies_ms':1.28,'coalesced_copy_ms':0.32,'remaining_gather_scatter_budget_ms':0.96,'kv_bytes_per_token':131072,'kv_8192_bytes':1073741824,'kv_16384_bytes':2147483648,'kv_length_doubling_capacity_ratio':2},
 'provenance':'Aqua p8 reports 4 MB/50 GB/s and 64 MB/200 GB/s; decimal interpretation is explicit. 100 Gb/s,64 B and KV geometry are illustrative assumptions, not asserted experimental/model configurations.'}
dump('calculations.json',calcs)
x={'scope':'Three bounded missing-abstract candidates 23/145/175; only parallel-next files; no shared index/outline/Git edits.',
 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':proof(P/'selection-snapshot.json'),'sources':sources,
 'records':records,'gaps':[gap],'software_sources':[],
 'new_full_abstracts':2,'representative_pdfs':2,'representative_pdf_pages':33,'selected_body_reading_records':1,'selected_body_physical_pages':4,'abstract_identity_pages_read_separately':2,'actual_rendered_pages_viewed':6,'body_reading_is_full_paper':False,
 'calculations':proof(P/'calculations.json'),'notes':proof(P/'READINGS.md'),'handoff':proof(P/'HANDOFF.md'),
 'unresolved':['OS2G full primary abstract/PDF unavailable in bounded search.','EDM body not read; no practical framework or whole-system latency conclusion.','Aqua other body pages not read; source code/current upstream adoption unverified; no full paper or benchmark reproduction claim.']}
dump('reading-records.json',x)
print('Built',len(records),'abstract records; gap',gap['doi'])
