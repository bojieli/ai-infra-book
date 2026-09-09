"""Bounded little-endian GGUF v3 header reader; never interprets tensor data."""
import struct


class TruncatedHeader(ValueError):
    pass


def parse(data):
    pos=0
    def take(size):
        nonlocal pos
        if size<0 or pos+size>len(data):raise TruncatedHeader('Incomplete GGUF header')
        result=data[pos:pos+size];pos+=size;return result
    def scalar(code):return struct.unpack('<'+code,take(struct.calcsize('<'+code)))[0]
    def string():
        size=scalar('Q')
        if size>16*1024**2:raise ValueError('GGUF string exceeds header-reader bound')
        return take(size).decode('utf-8')
    formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
    def value(kind,depth=0):
        if kind in formats:return scalar(formats[kind])
        if kind==8:return string()
        if kind==9:
            if depth:raise ValueError('Nested metadata arrays unsupported')
            subtype=scalar('I');count=scalar('Q')
            if count>1000000:raise ValueError('GGUF metadata array exceeds bound')
            # Consume tokenizer arrays but avoid materializing them in results.
            for _ in range(count):value(subtype,depth+1)
            return dict(array_type=subtype,array_count=count)
        raise ValueError(f'Unknown metadata type {kind}')
    if take(4)!=b'GGUF' or scalar('I')!=3:raise ValueError('Expected little-endian GGUF v3')
    count=scalar('Q');metadata_count=scalar('Q')
    if count>100000 or metadata_count>10000:raise ValueError('Header count exceeds bound')
    metadata={}
    for _ in range(metadata_count):
        key=string()
        if key in metadata:raise ValueError('Duplicate metadata key')
        metadata[key]=value(scalar('I'))
    tensors=[];names=set()
    for _ in range(count):
        name=string();rank=scalar('I')
        if name in names or not 1<=rank<=4:raise ValueError('Invalid tensor name/rank')
        names.add(name);shape=[scalar('Q') for _ in range(rank)]
        if any(d==0 for d in shape):raise ValueError('Empty tensor')
        tensors.append(dict(name=name,shape=shape,type_id=scalar('I'),offset=scalar('Q')))
    alignment=metadata.get('general.alignment',32)
    if not isinstance(alignment,int) or alignment<1 or alignment&(alignment-1):raise ValueError('Invalid alignment')
    return dict(version=3,tensor_count=count,metadata=metadata,tensors=tensors,
                header_bytes=pos,data_start_bytes=(pos+alignment-1)//alignment*alignment,alignment=alignment)
