"""Extract published operator tables, never run the external calculation work package."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT.parents[3]/'references/files/papers/cloudmatrix384-v2.pdf'
EXPECTED='9f64d10d41a426a7fe271fecaf25d7be6fa5b6d4fb11ef290b1cf485baf31e9e'
def extract(pdf):
    digest=hashlib.sha256(pdf.read_bytes()).hexdigest();assert digest==EXPECTED,'Unexpected paper version'
    text=subprocess.check_output(['pdftotext','-f','48','-l','49','-layout',str(pdf),'-'],text=True)
    table8=text.split('Table 8.')[1].split('Table 9.')[0]
    table9=text.split('Table 9.')[1].split('patterns.')[0]
    table10=text.split('Table 10.')[1].split('K=8192')[0]
    mla=[]
    for name,label in [('DeepSeek FlashMLA on H800','h800'),('CANN MLA on Ascend 910C die','ascend_910c_die')]:
        compute=re.search(re.escape(name)+r'\s+BF16/FP16\s+([\d.]+)',table8)
        bandwidth=re.search(re.escape(name)+r'\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)%',table9)
        assert compute and bandwidth
        achieved,peak=[int(x.replace(',','')) for x in bandwidth.group(1,2)]
        util=float(bandwidth.group(3));assert abs(100*achieved/peak-util)<.06
        mla.append(dict(device=label,precision_as_reported='BF16/FP16',compute_utilization_percent=float(compute.group(1)),
                        bandwidth_GB_s=achieved,peak_bandwidth_GB_s=peak,bandwidth_utilization_percent=util,
                        page=48,tables=[8,9],exact_shape=None,measurement_counter_definition=None))
    gemm=[]
    for match in re.finditer(r'^\s*(4|8)\s+(7168|2048)\s+(4096|7168)\s+(4096|8192)\s+(\d+)\s+([\d.]+)\s*$',table10,re.M):
        g,m,n,k,b,u=match.groups();gemm.append(dict(groups=int(g),m=int(m),n=int(n),k=int(k),bandwidth_GB_s=int(b),compute_utilization_percent=float(u)))
    assert len(gemm)==6 and len(mla)==2
    return dict(source=dict(url='https://arxiv.org/pdf/2506.12708v2',sha256=digest,version='v2, 2025-06-18',pages=[48,49],evidence_kind='paper author reported measurements; not local reproduction'),
                mla=mla,gemm=dict(device='one Ascend 910C die',input_dtype='INT8',output_dtype='BF16',tile=[128,152],table=10,page=49,rows=gemm),
                limitations=['MLA exact batch/head/sequence shapes not specified in Tables 8/9 or section 5.5.2.',
                             'No raw repetitions, dispersion or counter byte definition in these operator tables.',
                             'GEMM INT8 grouped large matrices differ from local FP32 small GEMM.',
                             'MLA differs from local standard causal attention; paper bandwidth differs from copy payload/time.',
                             'Published utilization is relative to each devices reported peak, not relative application speed.'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,default=DEFAULT);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=extract(a.pdf);dest=ROOT/'records.json'
    if a.verify:assert json.loads(dest.read_text())==result
    else:dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('PASS: PDF hash, 2 MLA entries, 6 GEMM rows, bandwidth percentage consistency')
