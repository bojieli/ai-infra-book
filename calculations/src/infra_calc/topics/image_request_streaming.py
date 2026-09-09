"""Explicit declared block dependencies; no inference of codec/model independence."""
from fractions import Fraction as F
import json


def rational(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int,str)):
        raise ValueError(label+' requires integer or rational string')
    try:value=F(value)
    except (ValueError,ZeroDivisionError) as exc:raise ValueError(label) from exc
    if value<0 or (positive and value==0):raise ValueError(label)
    return value


def byte_count(value):
    if type(value) is not int or value<=0:raise ValueError('Positive integer file bytes required')
    return value


def default_chunks():
    return [dict(input_bytes=10_000_000,output_bytes=out,process_seconds='1/10',encode_seconds='0',required_inputs=[i])
            for i,out in enumerate((1_000_000,2_000_000,2_000_000))]


def calculate(chunks=None,mode='whole_image',independent_blocks_authorized=False,
              quality_contract='same original information and usable final-image quality',
              upload_bits_per_second=20_000_000,download_bits_per_second=100_000_000,
              forward_propagation_seconds='1/20',reverse_propagation_seconds='1/20',
              preparation_seconds='0',connection_seconds='0',final_assembly_seconds='0',preview=None):
    chunks=default_chunks() if chunks is None else chunks
    if mode not in ('whole_image','independent_blocks'):raise ValueError('Unknown mode')
    if mode=='independent_blocks' and independent_blocks_authorized is not True:
        raise ValueError('Independent model, encoding, and output-block dependencies require explicit authorization')
    if not isinstance(quality_contract,str) or not quality_contract.strip():raise ValueError('Explicit same-quality contract required')
    if not isinstance(chunks,list) or not chunks:raise ValueError('Nonempty chunk metadata required')
    up=rational(upload_bits_per_second,'upload',True);down=rational(download_bits_per_second,'download',True)
    forward=rational(forward_propagation_seconds,'forward propagation');reverse=rational(reverse_propagation_seconds,'reverse propagation')
    prep=rational(preparation_seconds,'preparation');connection=rational(connection_seconds,'connection')
    assembly=rational(final_assembly_seconds,'assembly')
    inputs=[]
    for i,c in enumerate(chunks):
        if not isinstance(c,dict) or set(c)!={'input_bytes','output_bytes','process_seconds','encode_seconds','required_inputs'}:
            raise ValueError('Complete per-block metadata required')
        dependencies=c['required_inputs']
        if not isinstance(dependencies,list) or not dependencies or any(type(x) is not int or not 0<=x<len(chunks) for x in dependencies) or len(set(dependencies))!=len(dependencies):
            raise ValueError('Invalid input dependencies')
        if mode=='independent_blocks' and dependencies!=[i]:raise ValueError('Independent mode requires block i to depend only on input i; no implicit halo/global attention')
        inputs.append(dict(input_bytes=byte_count(c['input_bytes']),output_bytes=byte_count(c['output_bytes']),
                           process=rational(c['process_seconds'],'process'),encode=rational(c['encode_seconds'],'encode'),deps=dependencies))
    if preview is not None:
        if not isinstance(preview,dict) or set(preview)!={'after_processed_chunk','bytes','encode_seconds','quality_contract'}:
            raise ValueError('Preview needs scheduling boundary, additional bytes, encoding cost and separate quality requirement')
        if type(preview['after_processed_chunk']) is not int or not 0<=preview['after_processed_chunk']<len(inputs):raise ValueError('Invalid preview boundary')
        byte_count(preview['bytes']);rational(preview['encode_seconds'],'preview encode')
        if not isinstance(preview['quality_contract'],str) or not preview['quality_contract'].strip():raise ValueError('Preview quality required')
    events=[]
    def event(name,resource,start,duration,dependencies,**extra):
        finish=start+duration
        events.append(dict(id=name,resource=resource,start_seconds_exact=str(start),duration_seconds_exact=str(duration),end_seconds_exact=str(finish),dependencies=dependencies,**extra))
        return finish
    ready=event('prepare','client',F(0),prep,[])
    ready=event('connect','client',ready,connection,['prepare'])
    arrivals=[];uplink=ready
    for i,c in enumerate(inputs):
        uplink=event(f'upload.{i}','uplink',uplink,F(8*c['input_bytes'],up),['connect'] if i==0 else [f'upload.{i-1}'],bytes=c['input_bytes'])
        arrivals.append(event(f'input_arrival.{i}',None,uplink,forward,[f'upload.{i}']))
    server=ready;outputs=[];preview_ready=None
    for i,c in enumerate(inputs):
        required=list(range(len(inputs))) if mode=='whole_image' else c['deps']
        release=max(arrivals[j] for j in required)
        deps=[f'input_arrival.{j}' for j in required]
        if i:deps.append(f'preview_encode' if preview is not None and preview['after_processed_chunk']==i-1 else f'encode.{i-1}')
        server=event(f'process.{i}','server',max(server,release),c['process'],deps)
        server=event(f'encode.{i}','server',server,c['encode'],[f'process.{i}'])
        outputs.append(server)
        if preview is not None and preview['after_processed_chunk']==i:
            # Preview explicitly consumes processed prefix0..i, not future chunks.
            server=event('preview_encode','server',server,rational(preview['encode_seconds'],'preview encode'),[f'process.{j}' for j in range(i+1)]+[f'encode.{i}'])
            preview_ready=server
    jobs=[]
    for i,c in enumerate(inputs):
        release=max(outputs) if mode=='whole_image' else outputs[i]
        deps=[f'encode.{j}' for j in range(len(inputs))] if mode=='whole_image' else [f'encode.{i}']
        jobs.append((release,1,i,f'final.{i}',c['output_bytes'],deps))
    if preview is not None:jobs.append((preview_ready,0,0,'preview',preview['bytes'],['preview_encode']))
    # One non-preemptive FIFO downlink; preview wins only equal-ready-time ties.
    jobs.sort();link=F(0);delivered={}
    for release,_,__,name,count,deps in jobs:
        if delivered:deps=deps+[last_download]
        last_download='download.'+name
        link=event(last_download,'downlink',max(link,release),F(8*count,down),deps,bytes=count)
        delivered[name]=event('arrival.'+name,None,link,reverse,[last_download])
    complete=event('final_usable','client',max(delivered[f'final.{i}'] for i in range(len(inputs))),assembly,[f'arrival.final.{i}' for i in range(len(inputs))])
    return dict(calculation='image-request-streaming',scenario=dict(chunks=chunks,mode=mode,
        independent_blocks_authorized=independent_blocks_authorized,quality_contract=quality_contract,
        upload_bits_per_second=upload_bits_per_second,download_bits_per_second=download_bits_per_second,
        forward_propagation_seconds=forward_propagation_seconds,reverse_propagation_seconds=reverse_propagation_seconds,
        preparation_seconds=preparation_seconds,connection_seconds=connection_seconds,final_assembly_seconds=final_assembly_seconds,preview=preview),
        events=events,summary=dict(input_file_bytes=sum(c['input_bytes'] for c in inputs),
        final_file_bytes=sum(c['output_bytes'] for c in inputs),additional_preview_bytes=0 if preview is None else preview['bytes'],
        total_downlink_bytes=sum(c['output_bytes'] for c in inputs)+(0 if preview is None else preview['bytes']),
        complete_final_image_seconds_exact=str(complete),preview_ready_seconds_exact=None if preview is None else str(delivered['preview']),
        preview_is_complete_final_image=False,measured_seconds=None),
        scope=[
            'Given file-block bytes, not inferred RAW/JPEG sizes. No codec, model or network executes.',
            'Independent mode requires caller authorization that input, model and encoded output blocks preserve the same final quality without cross-block dependencies; this is not asserted for real RAW/JPEG editing.',
            'One serial uplink, one shared server for processing/encoding including preview, one serial downlink; these three resources may overlap. Fixed block order and non-preemptive FIFO downlink; no optimal scheduling claim.',
            'Forward/reverse propagation applies after each serialization and consumes no link capacity; packets can be in flight together. It is not repeatedly added to serialization resource occupancy. No separate RTT term exists.',
            'Whole-image mode adds all-input and all-final-encoding barriers while preserving identical per-block work/bytes. It is an explicitly declared barrier comparison, not a claim about actual monolithic runtime.',
            'Optional preview consumes processed prefix0..after_processed_chunk, extra encoding work and additional downlink bytes. Its quality requirement differs from final; preview never substitutes for complete final delivery.',
            'Final assembly starts only after every final block arrives. Times omit undeclared queueing, loss recovery, handshake RTTs, protocol overhead, flow control and codec global work. Connection cost must be supplied separately.',
        ])



def markdown(result):
    summary=result['summary']
    lines=['# 图片分块依赖与独立交付点', '',
           f"模式：{result['scenario']['mode']}；完整成片 {summary['complete_final_image_seconds_exact']} 秒；预览 {summary['preview_ready_seconds_exact']} 秒（None表示未声明）。",
           f"原图 {summary['input_file_bytes']} bytes；成片 {summary['final_file_bytes']} bytes；额外预览 {summary['additional_preview_bytes']} bytes。", '',
           '| 事件 | 资源 | 开始 s | 结束 s | 前置事件 |', '| --- | --- | ---: | ---: | --- |']
    for e in result['events']:
        lines.append(f"| {e['id']} | {e['resource']} | {e['start_seconds_exact']} | {e['end_seconds_exact']} | {', '.join(e['dependencies'])} |")
    lines += ['', *['- '+x for x in result['scope']], '', '```json', json.dumps(result,ensure_ascii=False,indent=2), '```', '']
    return '\n'.join(lines)
