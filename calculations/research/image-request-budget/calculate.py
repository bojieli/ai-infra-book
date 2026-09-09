"""Declared complete-image request budget; no codec or network execution."""
from fractions import Fraction
from pathlib import Path
import json


def number(value, name, positive=False):
    if value is None or isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f'{name} requires an explicit finite integer/string, not unknown/float')
    try:
        result = Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError(f'Invalid {name}') from exc
    if result < 0 or (positive and result == 0):
        raise ValueError(f'Invalid {name}')
    return result


def size(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f'{name} must be positive integer bytes')
    return value


def calculate(input_bytes=30_000_000, output_bytes=5_000_000,
              upload_bits_per_second=20_000_000, download_bits_per_second=100_000_000,
              preparation_seconds='0', connection_seconds='0', request_rtt_seconds='1/10',
              queue_seconds='0', input_decode_seconds='0', model_seconds='3/10',
              output_encode_seconds='0', output_use_seconds='0', local_seconds=None,
              compression=None, quality_contract='same original information and same final-image requirement',
              metadata_kind='declared_teaching', input_format='RAW', output_format='JPEG'):
    inputs = locals().copy()
    if metadata_kind not in ('declared_teaching', 'supplied_file_metadata'):
        raise ValueError('Unrecognized metadata provenance')
    if not all(isinstance(x, str) and x.strip() for x in (quality_contract,input_format,output_format)):
        raise ValueError('Format labels and quality contract must be explicit')
    original = size(input_bytes, 'input_bytes'); size(output_bytes, 'output_bytes')
    up = number(upload_bits_per_second, 'upload rate', True)
    down = number(download_bits_per_second, 'download rate', True)
    timing = {key:number(inputs[key], key) for key in (
        'preparation_seconds','connection_seconds','request_rtt_seconds','queue_seconds',
        'input_decode_seconds','model_seconds','output_encode_seconds','output_use_seconds')}
    local = None if local_seconds is None else number(local_seconds, 'local_seconds')
    variants = [('original',original,Fraction(0),Fraction(0))]
    if compression is not None:
        if not isinstance(compression,dict) or set(compression) != {
            'transmitted_bytes','extra_encode_seconds','extra_decode_seconds','quality_contract','comparison_authorized'}:
            raise ValueError('Compression requires complete explicit metadata and quality assertion')
        if compression['comparison_authorized'] is not True or compression['quality_contract'] != quality_contract:
            raise ValueError('Compression comparison requires the same asserted quality contract')
        compressed = size(compression['transmitted_bytes'],'transmitted_bytes')
        if compressed > original:
            raise ValueError('This reduced-byte comparison requires transmitted_bytes <= original')
        variants.append(('compressed',compressed,
                         number(compression['extra_encode_seconds'],'extra encode'),
                         number(compression['extra_decode_seconds'],'extra decode')))
    rows=[]
    for name,payload,extra_encode,extra_decode in variants:
        stages=[('input_preparation',timing['preparation_seconds']),
                ('extra_input_compression',extra_encode),('connection',timing['connection_seconds']),
                ('request_round_trip',timing['request_rtt_seconds']),('upload',8*payload/up),
                ('queue',timing['queue_seconds']),('input_decode',timing['input_decode_seconds']),
                ('extra_input_decompression',extra_decode),('model',timing['model_seconds']),
                ('final_image_encode',timing['output_encode_seconds']),('download',8*output_bytes/down),
                ('output_use',timing['output_use_seconds'])]
        cursor=Fraction(0); events=[]
        for stage,seconds in stages:
            events.append(dict(stage=stage,start_seconds_exact=str(cursor),duration_seconds_exact=str(seconds),
                               end_seconds_exact=str(cursor+seconds)))
            cursor+=seconds
        fixed=cursor-8*payload/up
        available=None if local is None else local-fixed
        threshold=None if available is None or available<=0 else 8*payload/available
        rows.append(dict(variant=name,transmitted_input_bytes=payload,output_file_bytes=output_bytes,
            stages=events,complete_final_image_seconds_exact=str(cursor),preview_ready_seconds=None,
            reused_connection_final_seconds_exact=str(cursor-timing['connection_seconds']),
            connection_reuse_saving_seconds_exact=str(timing['connection_seconds']),
            local_comparison=dict(local_complete_seconds_exact=None if local is None else str(local),
                remote_strictly_faster=None if local is None else cursor<local,
                upload_equal_time_bits_per_second_exact=None if threshold is None else str(threshold),
                relation=('unknown_local_time' if local is None else
                    'no_finite_upload_rate_wins' if available<=0 else 'remote_faster_strictly_above_threshold'))))
    comparison=None
    if len(rows)==2:
        saved_bytes=original-variants[1][1]; overhead=variants[1][2]+variants[1][3]
        savings=8*saved_bytes/up-overhead
        comparison=dict(saved_input_bytes=saved_bytes,extra_codec_seconds_exact=str(overhead),
            complete_image_saving_seconds_exact=str(savings),compressed_strictly_faster=savings>0,
            upload_equal_time_bits_per_second_exact=str(8*saved_bytes/overhead) if overhead and saved_bytes else None,
            relation=('compressed_faster_strictly_below_threshold' if overhead and saved_bytes else
                      'compressed_faster_at_all_finite_positive_rates' if saved_bytes else
                      'tie_all_rates' if not overhead else 'compression_never_faster'))
    return dict(calculation='image-request-budget',scenario=inputs,variants=rows,compression_comparison=comparison,
        scope=[
            'File bytes are explicit metadata, not derived from pixels or a VAE tensor. No RAW/JPEG codec executes.',
            'Same-quality authorization is a caller assertion, not a measured quality guarantee; a JPEG label alone does not establish RAW equivalence.',
            'All stages are serial. Server waits for the entire input; download follows final-image encoding. No chunk or preview overlap is assumed.',
            'request_rtt_seconds is one declared residual request/response propagation/control budget, excluding serialization and connection establishment. It is charged once; no RTT is added per stage.',
            'Times exclude anything not included in explicit stage inputs. Default zero terms are teaching assumptions, not measurements. Supplied-file metadata does not make service times measured.',
            'Complete-final-image delivery is the comparison endpoint. Preview time remains unknown; earlier preview cannot substitute for full-image completion.',
            'Local time, when given, must cover the same original-input to usable-final-image boundary and quality requirement.',
            'Connection reuse removes only the explicit connection term; request RTT remains. Local thresholds are for each displayed original connection state.',
        ])


def build_results():
    compression=dict(transmitted_bytes=15_000_000,extra_encode_seconds='1/5',extra_decode_seconds='1/10',
        comparison_authorized=True,quality_contract='same original information and same final-image requirement')
    return dict(original=calculate(),faster_model=calculate(model_seconds='3/100'),
        connection=calculate(connection_seconds='1/5'),
        sweep=[calculate(upload_bits_per_second=rate,local_seconds='5',compression=compression)
               for rate in (10_000_000,20_000_000,100_000_000,400_000_000,800_000_000)])


if __name__=='__main__':
    Path(__file__).with_name('result.json').write_text(json.dumps(build_results(),indent=2,ensure_ascii=False)+'\n')
