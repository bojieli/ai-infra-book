"""L2 organisation, cross-SM handoff and synchronisation scopes, from the RTX PRO 6000 measurements."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from figure_style import COL,STYLE,canvas,plot,text,box,arrow

SOURCE='calculations/sources/opentallas/blackwell-sync-latency.json'

def ladder_rows(m,english=False):
    L=lambda zh,en:en if english else zh
    b=m['boundaries_ns']
    return [(L('SM 内栅栏','Barrier within an SM'),b['syncthreads_one_block'],'green'),
            (L('线程块簇内同步','Within a thread\nblock cluster'),b['cluster_sync_8_blocks'],'purple'),
            (L('跨 SM 一对一交接','One-to-one\ncross-SM handoff'),sum(b['handoff_release_acquire'])/2,'blue'),
            (L('全部 SM 汇合','All-SM barrier'),b['all_sm_counter_barrier'][0],'blue'),
            (L('全部 SM 汇合\n并送达激活向量','All-SM barrier\n+ vector delivery'),b['all_sm_gather_with_vector_bf16_8kib'],'blue')]

def draw(out,root,english=False):
    L=lambda zh,en:en if english else zh
    m=json.loads((Path(root)/SOURCE).read_text())
    def save(f,n):out.save(f,'figure-4-'+n)
    with plt.rc_context(STYLE):
        # Where L2 sits: the only storage every SM reaches.
        f,a=canvas(5.0)
        for g,x0 in enumerate([.03,.52]):
            box(a,x0,.58,.45,.39,'','gray');text(a,x0+.015,.93,f'GPC {g}',11)
            for i in range(3):box(a,x0+.02+i*.145,.68,.125,.19,L('SM\n共享内存','SM\nshared\nmemory'),'blue',11)
        a.add_patch(plt.Rectangle((.04,.655),.285,.235,fill=False,ec=COL['ink'],lw=1.2,ls='--'))
        text(a,.1825,.62,L('线程块簇','Thread block cluster'),11,ha='center')
        box(a,.03,.38,.94,.12,L('片上交叉互连','On-chip crossbar'),'orange')
        for i in range(6):box(a,.03+i*.16,.17,.14,.11,L('L2 分片','L2 slice'),'green',11)
        text(a,.5,.12,L(f"L2 共 {m['device']['l2_mib']} MiB，每个分片负责一部分地址",f"{m['device']['l2_mib']} MiB of L2; each slice owns part of the addresses"),11,ha='center')
        box(a,.03,.02,.94,.07,L('显存控制器与显存','Memory controllers and GPU memory'),'gray',11)
        arrow(a,(.4125,.68),(.4125,.50));arrow(a,(.36,.38),(.40,.28))
        arrow(a,(.44,.28),(.74,.38));arrow(a,(.7475,.50),(.7475,.68))
        text(a,.425,.54,L('① 写入','① Write'),11);text(a,.76,.54,L('② 读取','② Read'),11)
        save(f,'l2-structure')

        # One cross-SM handoff, time downward.
        f,a=canvas(5.2)
        for x,label,c in [(.22,L('生产者 SM','Producer SM'),'blue'),(.56,L('L2 分片','L2 slice'),'green'),(.86,L('消费者 SM','Consumer SM'),'orange')]:
            box(a,x-.10,.88,.20,.09,label,c);a.plot([x,x],[.05,.88],color=COL['line'],lw=.8,ls=':')
        def msg(x0,y0,x1,y1,label,above=True):
            arrow(a,(x0,y0),(x1,y1));text(a,(x0+x1)/2,(y0+y1)/2+(.03 if above else -.03),label,11,ha='center')
        P,S,C=.22,.56,.86
        msg(P,.82,S,.75,L('写数据','Write data'));msg(S,.73,P,.66,L('确认','Ack'),False)
        a.plot([.18,.18],[.81,.67],color=COL['ink'],lw=2.2);text(a,.01,.74,L('fence：\n等待确认','Fence:\nwait\nfor ack'),11)
        msg(P,.52,S,.45,L('写标志','Write flag'))
        msg(C,.80,S,.73,L('读标志','Read flag'));msg(S,.71,C,.64,L('旧值','Old value'),False)
        msg(C,.46,S,.39,L('读标志','Read flag'));msg(S,.37,C,.30,L('新值','New value'),False)
        msg(C,.25,S,.18,L('读数据','Read data'));msg(S,.16,C,.09,L('数据','Data'),False)
        a.plot([.90,.90],[.80,.30],color=COL['ink'],lw=2.2);text(a,.92,.55,L('轮询','Poll'),11)
        save(f,'cross-sm-handoff')

        # Cost of each synchronisation scope, measured.
        rows=ladder_rows(m,english);f,a=plot(3.6,left=.30,bottom=.19)
        for i,(label,ns,c) in enumerate(rows):
            a.barh(i,ns,color=COL[c],edgecolor=COL['line'],height=.58)
            a.text(ns+20,i,f'{ns:,.0f} ns',va='center',fontsize=11)
        a.set(yticks=range(len(rows)),yticklabels=[r[0] for r in rows],xlim=(0,1250),xticks=range(0,1201,200),ylim=(len(rows)-.4,-.6),xlabel=L('一次同步的时间（ns）','Time per synchronization (ns)'))
        save(f,'sync-ladder')
    return {'source':SOURCE,'ladder':[{'scope':r[0],'ns':r[1]} for r in rows]}
