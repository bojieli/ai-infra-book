"""Qwen3-VL static-image features, language KV and an explicit E/PD pool.

Dimensions are AFTER image preprocessing. This module does not resize pixels,
run the image processor, tokenize a prompt or execute a vision/language model.
"""
from fractions import Fraction
import hashlib
import json

from ..paths import PROJECT
from ..sources import model_config, provenance
from ..units import positive_int
from .pd_pool import exact_rate


MODEL = 'qwen3-vl-4b'
DTYPE_BYTES = {'bf16': 2, 'fp16': 2, 'fp32': 4}


def read_auxiliary():
    """Verify the archived processor config and encoder-layout implementation."""
    lock = json.loads((PROJECT / 'configs/multimodal-cache.lock.json').read_text())
    files = {}
    for record in lock:
        data = (PROJECT / record['file']).read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Multimodal source checksum mismatch: ' + record['file'])
        files[record['file'].split('/')[-1]] = data
    if set(files) != {'qwen3-vl4-preprocessor.json', 'vllm-qwen3-vl.py'}:
        raise ValueError('The processor and encoder-layout sources are both required')
    return json.loads(files['qwen3-vl4-preprocessor.json']), lock


def calculate(preprocessed_height=640, preprocessed_width=640,
              images_per_request=4, text_tokens=400, dtype='bf16', kv_dtype='bf16',
              compressed_image_bytes=800000, uplink_bits_per_second=6400000,
              total_workers=4, encoder_images_per_second='12',
              pd_requests_per_second='4', encoder_cache_hit_fraction='0',
              network_bytes_per_second=300000000, arrival_requests_per_second='0'):
    """Account one repeated image shape and enumerate fixed integer pool splits.

    Cache hits occur at E. Both hit and miss paths send the full encoder tensor
    to PD. A positive E pool is retained even at a hit fraction of one; cache
    lookup/read capacity is unknown, not silently converted into infinite service.
    """
    inputs = locals().copy()
    for name in ('preprocessed_height', 'preprocessed_width', 'images_per_request',
                 'text_tokens', 'compressed_image_bytes', 'total_workers'):
        positive_int(inputs[name], name, allow_zero=name == 'text_tokens')
    if total_workers < 2 or total_workers > 1024:
        raise ValueError('Use 2 to 1024 workers for positive E and PD pools')
    if dtype not in DTYPE_BYTES or kv_dtype not in DTYPE_BYTES:
        raise ValueError('Cache and KV element formats must be bf16, fp16 or fp32')
    uplink = exact_rate(uplink_bits_per_second, 'uplink_bits_per_second') / 8
    encoder_rate = exact_rate(encoder_images_per_second, 'encoder_images_per_second')
    pd_rate = exact_rate(pd_requests_per_second, 'pd_requests_per_second')
    network = exact_rate(network_bytes_per_second, 'network_bytes_per_second')
    hit = exact_rate(encoder_cache_hit_fraction, 'encoder_cache_hit_fraction', True)
    arrival = exact_rate(arrival_requests_per_second, 'arrival_requests_per_second', True)
    if hit > 1:
        raise ValueError('Encoder image-cache hit fraction must be in [0,1]')

    config = model_config(MODEL)
    processor, auxiliary_sources = read_auxiliary()
    vision, text = config['vision_config'], config['text_config']
    if config['model_type'] != 'qwen3_vl':
        raise ValueError('Only the audited Qwen3-VL image geometry is supported')
    patch = vision['patch_size']
    merge = vision['spatial_merge_size']
    if (processor['patch_size'], processor['merge_size'], processor['temporal_patch_size']) != (
            patch, merge, vision['temporal_patch_size']):
        raise ValueError('Model and processor patch geometry differ')
    width = text['hidden_size']
    if vision['out_hidden_size'] != width:
        raise ValueError('The audited encoder projection must match the text width')
    deepstack = vision['deepstack_visual_indexes']
    if len(set(deepstack)) != len(deepstack) or any(
            not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < vision['depth']
            for i in deepstack):
        raise ValueError('DeepStack layer indices must be distinct vision blocks')
    factor = patch * merge
    if preprocessed_height % factor or preprocessed_width % factor:
        raise ValueError('Preprocessed image dimensions must align to patch × spatial merge')
    pixels = preprocessed_height * preprocessed_width
    limits = processor['size']
    if not limits['shortest_edge'] <= pixels <= limits['longest_edge']:
        raise ValueError('Preprocessed image pixel count is outside the locked default budget')

    # One static image is padded to one temporal patch, hence grid_t = 1.
    grid = [1, preprocessed_height // patch, preprocessed_width // patch]
    patches = grid[1] * grid[2]
    positions = patches // (merge * merge)
    visual_positions = positions * images_per_request
    input_positions = visual_positions + text_tokens
    if input_positions > text['max_position_embeddings']:
        raise ValueError('Declared input positions exceed the official text context limit')
    element_bytes = DTYPE_BYTES[dtype]
    component_bytes = positions * width * element_bytes
    encoder_width = width * (1 + len(deepstack))
    image_ec = positions * encoder_width * element_bytes
    request_ec = images_per_request * image_ec
    kv_per_position = (2 * text['num_hidden_layers'] * text['num_key_value_heads']
                       * text['head_dim'] * DTYPE_BYTES[kv_dtype])
    components = [dict(name='final_embedding', vision_block=None,
                       shape=[positions, width], bytes=component_bytes)]
    components.extend(dict(name='deepstack_' + str(i), vision_block=i,
                           shape=[positions, width], bytes=component_bytes) for i in deepstack)

    network_capacity = network / request_ec
    assignments = []
    for encoders in range(1, total_workers):
        pd_workers = total_workers - encoders
        encode_capacity = (encoder_rate * encoders / (images_per_request * (1 - hit))
                           if hit < 1 else None)
        constraints = dict(pd=pd_rate * pd_workers, network=network_capacity)
        if encode_capacity is not None:
            constraints['uncached_encode'] = encode_capacity
        bound = min(constraints.values())
        assignments.append(dict(
            encoder_workers=encoders, pd_workers=pd_workers,
            uncached_encode_requests_per_second_exact=(str(encode_capacity)
                                                       if encode_capacity is not None else None),
            pd_requests_per_second_exact=str(pd_rate * pd_workers),
            network_requests_per_second_exact=str(network_capacity),
            bound_requests_per_second_exact=str(bound),
            bottlenecks=[name for name, value in constraints.items() if value == bound],
            arrival_strictly_below_all_known_bounds=arrival < bound,
            transmitted_bytes_per_second_at_bound_exact=str(bound * request_ec),
        ))
    best_rate = max(Fraction(row['bound_requests_per_second_exact']) for row in assignments)
    best_splits = [dict(encoder_workers=row['encoder_workers'], pd_workers=row['pd_workers'])
                   for row in assignments if Fraction(row['bound_requests_per_second_exact']) == best_rate]

    return dict(
        schema_version=1, calculation='multimodal-cache', model=MODEL, scenario=inputs,
        sources=provenance(MODEL) + auxiliary_sources,
        multimodal_encoder_components=components, multimodal_pool_assignments=assignments,
        summary=dict(
            preprocessed_grid_thw=grid, pre_merge_patch_count=patches,
            image_visual_positions=positions, deepstack_visual_blocks=deepstack,
            final_embedding_shape=[positions, width], complete_encoder_shape=[positions, encoder_width],
            final_embedding_bytes_per_image=component_bytes,
            deepstack_bytes_per_image=image_ec - component_bytes,
            complete_encoder_bytes_per_image=image_ec,
            complete_encoder_bytes_per_request=request_ec,
            visual_positions_per_request=visual_positions, declared_input_positions=input_positions,
            kv_bytes_per_position=kv_per_position,
            visual_kv_bytes_per_image=positions * kv_per_position,
            visual_kv_bytes_per_request=visual_positions * kv_per_position,
            text_kv_bytes_per_request=text_tokens * kv_per_position,
            declared_input_kv_bytes=input_positions * kv_per_position,
            compressed_image_uplink_exact_seconds=str(Fraction(compressed_image_bytes) / uplink),
            complete_encoder_uplink_exact_seconds=str(Fraction(image_ec) / uplink),
            encoder_to_compressed_bytes_ratio_exact=str(Fraction(image_ec, compressed_image_bytes)),
            one_image_ec_network_exact_seconds=str(Fraction(image_ec) / network),
            one_request_ec_network_exact_seconds=str(Fraction(request_ec) / network),
            ec_transfer_bytes_per_request=request_ec,
            uncached_images_per_request_exact=str(images_per_request * (1 - hit)),
            best_known_bound_requests_per_second_exact=str(best_rate), best_pool_splits=best_splits,
            arrival_strictly_below_best_known_bound=arrival < best_rate,
            encoder_cache_service_capacity_known=False,
        ),
        assumptions=[
            '锁定官方Qwen3-VL-4B配置与预处理配置、固定vLLM输出布局；这里只接受预处理后的单一静态图片尺寸，重复images_per_request次。每边须为patch×merge整数倍且面积在默认预算内；未运行resize、像素归一化、tokenizer、视频采样或视觉剪枝，不能把任意原图尺寸直接代入。',
            '静态图片只形成一个temporal grid；temporal_patch_size=2不使位置数翻倍。完整EC沿特征维拼接最终embedding及每个DeepStack输出，消费者再拆分，不把DeepStack维度扩展误算成更多语言token。',
            'text_tokens是调用者已经计数的其余输入位置，应包含实际模板/特殊token；默认400是教学题设。不自动增加图片边界token，也不冒称完整文本tokenizer输出。KV仅为声明输入位置的完整层逻辑K/V，不含生成增长、页碎片、并行复制、工作区或HBM流量。',
            'EC和KV精度各自仅决定元素字节；没有量化metadata、误差或转换计时。完整EC不是图片原件、RAW精修输入或语言KV的等价替代，跨问题EC复用与顺序相关KV复用须分别验证身份。',
            '压缩图片字节、上行与E/PD/网络能力均为教学输入；时间只算单向payload/BW，不计本地编码、RTT、排队、D2H/H2D、序列化或接收就绪，不是完整请求时间或官方硬件性能。',
            'E卡12 images/s和PD卡4 requests/s须按给定相同图像/请求形状校准。改变图数、分辨率或dtype而保留速率只是敏感性假设。worker假定能容纳相应模型与状态，未核设备内存、并行组或资源混用。',
            'cache命中位于E侧；所有图像不论命中仍发送完整EC，命中只减少未缓存编码工作。查询、cache读取/写回与服务槽能力未定价，至少保留一个E worker；h=1的编码约束null表示该工作为零，不表示缓存服务无限快。',
            '固定整数E/PD分配穷举所有正池组合，独立已知资源取min，所有并列最优均保留；网络是共享有效单向字节率，不把收发两端相加。到达率严格低于这些上界仍不证明真实稳定性或SLO，缺失缓存服务约束、突发与尾部需另核。',
        ],
    )
