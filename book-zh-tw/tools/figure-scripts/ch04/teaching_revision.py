"""Physical resources and finite buffers at final book dimensions."""
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from figure_style import COL,STYLE,canvas,plot,text,box,arrow,Exporter

def draw(here,data,teaching):
    out=Exporter(here)
    def save(f,n):out.save(f,'figure-4-'+n)
    with plt.rc_context(STYLE):
        f,a=canvas(4.7)
        for row,m in enumerate([1,256]):
            y=.58-row*.44;text(a,.04,y+.30,f'{m} 行共用 32 MiB 權重',14)
            box(a,.34,y+.04,.32,.20,"權重 W",'orange')
            for j in range(1 if m==1 else 4):
                yy=y+.12+(j-1.5)*.06 if m>1 else y+.12
                box(a,.04,yy,.17,.045,'','blue');box(a,.80,yy,.16,.045,'','green');arrow(a,(.21,yy+.023),(.34,y+.14));arrow(a,(.66,y+.14),(.80,yy+.023))
            text(a,.50,y-.07,"每行分攤："+('32 MiB' if m==1 else '128 KiB'),12,ha='center')
        save(f,'1-reuse')
        f,a=canvas(4.9);box(a,.04,.79,.36,.14,"主機 CPU",'gray');box(a,.60,.79,.36,.14,"片外視訊記憶體",'blue')
        box(a,.03,.06,.94,.60,'','gray');text(a,.06,.62,"加速器晶片內部",14)
        box(a,.10,.41,.80,.12,"共享快取與資料搬移",'blue');arrow(a,(.78,.79),(.68,.53));arrow(a,(.22,.79),(.24,.53),'control')
        box(a,.10,.16,.24,.14,"區域性緩衝",'green');box(a,.41,.16,.24,.14,"矩陣單元",'orange');box(a,.72,.16,.19,.14,"累加儲存",'purple',11)
        arrow(a,(.25,.41),(.22,.30));arrow(a,(.34,.23),(.41,.23));arrow(a,(.65,.23),(.72,.23));save(f,'2-components')
        f,a=canvas(3.9);text(a,.04,.94,"小陣列反覆複用輸入與權重",14)
        for i in range(3):
            text(a,.12,.67-i*.18,f'A{i}',12,ha='center')
            for j in range(3):
                x=.30+j*.22;y=.59-i*.18;box(a,x,y,.16,.14,"乘加",'green',11)
                arrow(a,(.18 if j==0 else x-.06,y+.07),(x,y+.07))
                if i==0:text(a,x+.08,.84,f'W{j}',12,ha='center')
                arrow(a,(x+.08,.79 if i==0 else y+.18),(x+.08,y+.14))
        text(a,.5,.08,"每個乘加單元保留部分和，繼續累加下一對輸入",11,ha='center');save(f,'matrix-array')
        f,a=canvas(4.0);text(a,.04,.94,"每塊固定 16 行，灰色行也參與執行",14)
        for x,count,label in [(.08,2,"每專家 2 行"),(.57,16,"每專家 64 行\n由四塊組成")]:
            for i in range(16):a.add_patch(Rectangle((x,.74-i*.034),.30,.029,facecolor=COL['green'] if i<count else COL['gray'],edgecolor=COL['line'],lw=.3))
            text(a,x+.15,.10,label,12,ha='center')
        save(f,'3-expert-rows')
        f,a=plot(3.2,left=.28)
        a.barh([0,1],[512,512],color=COL['green'],label="有效行");a.barh([0,1],[3584,0],left=[512,512],color=COL['gray'],edgecolor=COL['line'],label="補零行")
        a.set(yticks=[0,1],yticklabels=["256 個專家","8 個專家"],xlim=(0,4500),ylim=(-.7,1.7),xlabel="執行的矩陣行數（含補零）");a.invert_yaxis();a.legend(frameon=False);save(f,'expert-padding-total')
        vals=np.array(data['4-4']['service_cycles'])
        f,a=plot(4.0,left=.27)
        for i,(label,c) in enumerate([("矩陣",'orange'),("共享記憶體",'blue'),("指數",'green')]):a.barh(np.arange(4)+(i-1)*.22,vals[:,i],height=.20,color=COL[c],edgecolor=COL['line'],label=label)
        a.set(yticks=range(4),yticklabels=["原設定","矩陣 ×2","矩陣、指數均 ×2","三項 ×2"],xlabel="單計算組耗時（週期）",xlim=(0,1150),ylim=(-1.1,3.6));a.invert_yaxis();a.legend(ncol=3,loc='upper center',frameon=False,fontsize=11);save(f,'4-attention')
        f,a=canvas(4.3)
        for y,title,stages in [(.58,"先展開為高精度",[("壓縮 8.5 MiB",'blue'),("展開 32 MiB",'orange'),("BF16 計算",'green')]),(.12,"在低精度路徑中計算",[("壓縮 8.5 MiB",'blue'),("低精度計算",'orange'),("縮放與合併",'green')])]:
            text(a,.04,y+.29,title,14)
            for i,(label,c) in enumerate(stages):
                x=.03+i*.335;box(a,x,y,.27,.20,label,c,11)
                if i<2:arrow(a,(x+.27,y+.10),(x+.335,y+.10))
        save(f,'5-precision')
        d=data['4-6'];f,a=plot(3.8,left=.28,bottom=.25)
        for y,row in enumerate(d['cases']):
            left=0
            for n,c,label in [(d['weight_bytes'],'blue',"權重"),(d['workspace_bytes'],'orange',"工作區"),(row['requests']*row['context_multiplier']*d['kv_bytes_per_request'],'green','KV')]:
                a.barh(y,n/1e9,left=left,height=.5,color=COL[c],edgecolor=COL['line'],label=label if y==0 else None);left+=n/1e9
        a.axvline(24,ls='--',color='#555555');a.set(yticks=range(3),yticklabels=["8K token × 4 請求","8K token × 5 請求","16K token × 2 請求"],xlim=(0,27),xlabel="RTX 4090 視訊記憶體佔用（GB）");a.invert_yaxis();a.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.22),frameon=False);save(f,'6-capacity')
        f,a=canvas(3.3);text(a,.04,.92,"同時等待回傳的存取佔用請求槽",14)
        for i in range(4):box(a,.05+i*.235,.49,.20,.18,f'請求 {i+1}','blue',11)
        text(a,.5,.31,"每請求 128 bytes，發出後 500 ns 回傳",12,ha='center')
        text(a,.5,.12,"持續頻寬還取決於能同時處理多少請求",12,ha='center');save(f,'memory-inflight')
        d=data['4-7'];f,a=plot(3.7)
        for b,ys,c in zip(['RTX 4090：1008 GB/s','RTX 5090：1792 GB/s'],d['bandwidth_upper_bytes_per_second'],['#267398','#388768']):a.plot(d['requests'],np.array(ys)/1e12,label=b,color=c)
        a.set(xlim=(0,10000),ylim=(0,2.4),xlabel="同時未完成請求數",ylabel="頻寬上界（TB/s）");a.legend(frameon=False);save(f,'7-memory')
        f,a=plot(3.4,left=.21)
        for i in range(4):a.barh(i,8192,color=COL['gray'],edgecolor=COL['line'],height=.5);a.barh(i,256,color=COL['blue'],height=.5)
        a.set(yticks=range(4),yticklabels=["第 0 行","第 1 行","第 2 行","第 127 行"],xlim=(0,8500),xlabel="相對每行起點的位元組偏移",xticks=[0,4096,8192]);a.invert_yaxis();a.annotate("實際讀取 256 bytes",(128,0),xytext=(2000,.65),arrowprops={'arrowstyle':'->'},fontsize=12);save(f,'8-layout')
        f,a=plot(3.1,left=.16);a.barh(0,320,left=0,color=COL['gray'],height=.62,label="槽位佔用");a.barh(0,64,left=0,color=COL['blue'],height=.4);a.barh(0,128,left=192,color=COL['green'],height=.4);a.axvline(192,color='#a56c28',lw=1)
        a.set(xlim=(0,350),ylim=(-.7,.7),yticks=[],xticks=[0,64,192,320],xlabel="時間（tick）")
        for x,label in [(32,"傳輸"),(128,"等待回傳"),(256,"計算")]:a.text(x,.4,label,fontsize=11,ha='center')
        a.text(175,-.4,"320 tick 後用完，輸入槽才能再次寫入",fontsize=11,ha='center');save(f,'slot-lifetime')
        for slots,name in [(1,'9-pipeline'),(2,'pipeline-two'),(3,'pipeline-three')]:
            r=teaching['baseline'][slots-1];f,a=plot(3.5,left=.17)
            for t in r['chunks']:
                y=t['chunk'];a.barh(y,t['slot_released']-t['issue_start'],left=t['issue_start'],height=.62,color=COL['gray']);a.barh(y,t['transfer_end']-t['issue_start'],left=t['issue_start'],height=.40,color=COL['blue']);a.barh(y,t['compute_end']-t['compute_start'],left=t['compute_start'],height=.40,color=COL['green']);a.plot(t['data_ready'],y,'|',color='#a56c28',markersize=12)
            a.set(yticks=range(4),yticklabels=[f'塊 {i}' for i in range(4)],xlim=(0,1320),xticks=[0,320,640,960,1280],xlabel="時間（tick）");a.invert_yaxis();save(f,name)
        f,a=canvas(4.0);text(a,.04,.93,"傳遞完整行，兩組交替使用緩衝區",14)
        box(a,.04,.61,.26,.17,"矩陣單元\n計算 QK",'orange');box(a,.70,.61,.26,.17,"向量單元\n計算 Softmax",'green')
        box(a,.38,.66,.23,.11,"槽 A",'blue');box(a,.38,.42,.23,.11,"槽 B",'purple')
        arrow(a,(.30,.695),(.38,.715));arrow(a,(.61,.715),(.70,.695));arrow(a,(.17,.61),(.38,.475))
        box(a,.28,.09,.44,.16,"矩陣單元計算 PV\n用完後釋放緩衝區",'orange');arrow(a,(.83,.61),(.72,.17));save(f,'matrix-vector-handoff')
        cases=teaching['die_locality']['cases']
        for move,name in [(False,'10-locality'),(True,'locality-compute')]:
            f,a=canvas(4.8);text(a,.03,.96,"計算都放在 die 0" if not move else "計算放到權重所在的 die",14)
            for row,c in enumerate(cases):
                y=.56-row*.46;text(a,.03,y+.31,'HGX B200' if row==0 else "昇騰 910C",13)
                box(a,.03,y,.27,.25,"die 0\n32 GiB 權重\n計算",'blue',11)
                box(a,.70,y,.27,.25,"die 1\n32 GiB 權重"+("\n計算" if move else ''),'orange',11)
                if move:
                    arrow(a,(.30,y+.17),(.70,y+.17));arrow(a,(.70,y+.08),(.30,y+.08))
                    text(a,.50,y+.215,f"輸入與結果 64 MiB：{c['activation_us']:.1f} μs" if c['activation_us']<100 else f"輸入與結果 64 MiB：{c['activation_us']/1000:.2f} ms",11,ha='center')
                    text(a,.50,y-.045,f"兩側各讀本地權重：{c['split_ms']:.1f} ms",12,ha='center')
                else:
                    arrow(a,(.70,y+.125),(.30,y+.125))
                    limit="受 die 1 的 HBM 限制" if c['link_to_hbm_ratio']>=1 else "受 die 間鏈路限制"
                    text(a,.50,y+.20,f"跨 die 讀 32 GiB：{c['remote_ms']:.1f} ms",11,ha='center')
                    text(a,.50,y+.05,limit,11,ha='center')
                    text(a,.50,y-.045,f"階段讀取時間：{c['overlapped_ms']:.1f} ms",12,ha='center')
            save(f,name)
        d=data['4-11']
        for i,name in enumerate(['11-interconnect','large-message']):
            f,a=plot(3.2);vals=np.array(d['total_us'][i]);alpha=d['alpha_seconds']*1e6;a.bar([0,1],[alpha,alpha],color=COL['orange'],edgecolor=COL['line'],label="啟動");a.bar([0,1],vals-alpha,bottom=alpha,color=COL['blue'],edgecolor=COL['line'],label="傳輸")
            a.set(xticks=[0,1],xticklabels=['A100 NVLink\n300 GB/s','H100 NVLink\n450 GB/s'],ylabel="傳輸時間（μs）",ylim=(0,max(vals)*1.45));a.legend(ncol=2,frameon=False)
            for j,v in enumerate(vals):a.text(j,v+max(vals)*.035,f'{v:.3f}',ha='center',fontsize=12)
            save(f,name)
        d=data['4-12'];f,a=plot(3.5)
        a.axhline(d['active_weight_bytes']/1e9,color='#267398',label="每批權重");a.plot(d['batch'],np.array(d['kv_read_bytes'])/1e9,color='#388768',label="各請求 KV");a.axvline(13,ls=':',color='#777777')
        a.set(xlim=(1,32),ylim=(0,45),xlabel="批內請求數",ylabel="每步讀取（GB）");a.legend(frameon=False);save(f,'12-specialization')
        d=data['4-13'];f,a=plot(3.6)
        for key,label,c in [('compute_us',"矩陣計算",'#a56c28'),('memory_us',"片外讀取",'#267398')]:a.plot(d['rows'],d[key],label=label,color=c)
        a.axvline(179,ls=':',color='#777777');a.set(xlim=(1,256),ylim=(0,65),xlabel="本次 token 數 M",ylabel="資源時間（μs）");a.legend(frameon=False);save(f,'13-roofline')
        d=data['4-14']
        for key,name,label in [('wall_us','14-performance',"每次呼叫總耗時（μs）"),('dram_read_mib','performance-traffic',"DRAM 讀取（MiB）")]:
            f,a=plot(3.5)
            vals=d[key];a.bar(range(4),vals,color=[COL['blue'],COL['green']]*2,edgecolor=COL['line']);a.set(xticks=range(4),xticklabels=["1 行\n複用","1 行\n輪換","256 行\n複用","256 行\n輪換"],ylabel=label,ylim=(0,max(vals)*1.3))
            for i,v in enumerate(vals):a.text(i,v+max(vals)*.025,'256 B' if v<.001 else f'{v:.1f}',ha='center',fontsize=11)
            save(f,name)
    from sync_figures import draw as draw_sync
    data['4-sync']=draw_sync(out,Path(here).resolve().parents[1])
    from core_principles_figures import draw as draw_principles
    draw_principles(4, out)
    from energy_physics import draw as draw_energy
    data['4-energy']=draw_energy(out)
    return out.finish()
