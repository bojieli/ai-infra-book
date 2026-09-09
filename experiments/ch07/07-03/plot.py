from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent
rows=list(csv.DictReader((P/'rows.csv').open()))
fig,axes=plt.subplots(1,2,figsize=(12,4.8))
for rid,label,color in [('hgx2','2 hosts / 16 ranks','#0072B2'),('hgx4','4 hosts / 32 ranks; custom topology','#D55E00')]:
 a=[r for r in rows if r['run']==rid and r['mode']=='out_of_place'];x=[int(r['size_bytes']) for r in a]
 for key,style,suffix in [('algbw_GB_s','-','algbw'),('busbw_GB_s','--','busbw')]:axes[0].plot(x,[float(r[key]) for r in a],style,color=color,label=label+' / '+suffix)
axes[0].set_xscale('log',base=2);axes[0].set_xticks([8,2**10,2**20,2**30,2**34],['8 B','1 KiB','1 MiB','1 GiB','16 GiB']);axes[0].set_ylabel('Reported bandwidth (decimal GB/s)');axes[0].set_title('Published HGX AllReduce sweeps')
for rid,label,color in [('plugin_swap_0','24.06 container: original plugin','#D55E00'),('plugin_swap_1','24.06: plugin replaced from 23.12','#0072B2')]:
 a=[r for r in rows if r['run']==rid and r['mode']=='out_of_place'];axes[1].plot([int(r['size_bytes'])/2**30 for r in a],[float(r['time_us'])/1000 for r in a],'o-',label=label,color=color)
axes[1].set_yscale('log');axes[1].set_xticks([2,4,8,16]);axes[1].set_xlabel('AllReduce message (GiB)');axes[1].set_ylabel('Reported operation time (ms; log scale)');axes[1].set_title('Author plugin replacement; all rows correct')
for ax in axes:ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=8)
fig.text(.5,.015,'Out-of-place values only. Public reporter measurements; no new GPU run. Different hosts/topology are not a controlled placement experiment.',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(P/'public-records.png',dpi=160);fig.savefig(P/'public-records.svg')
