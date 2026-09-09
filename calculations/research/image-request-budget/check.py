"""Independent rational budget checks, not codec/quality verification."""
from fractions import Fraction as F
import calculate as candidate

checks=0
def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1

def total(**kw):
    return F(candidate.calculate(**kw)['variants'][0]['complete_final_image_seconds_exact'])

equal(total(),F(64,5))
equal(total()-total(model_seconds='3/100'),F(27,100))
equal(total(connection_seconds='1/5'),F(13))
for rate in (1,10_000_000,20_000_000,100_000_000,1_000_000_000):
    r=candidate.calculate(upload_bits_per_second=rate,local_seconds='5')
    row=r['variants'][0]
    equal(F(row['complete_final_image_seconds_exact']),F(240_000_000,rate)+F(4,5))
    threshold=F(row['local_comparison']['upload_equal_time_bits_per_second_exact'])
    equal(threshold,F(400_000_000,7))
    for relative in (F(1,2),F(1),F(2)):
        x=candidate.calculate(upload_bits_per_second=str(threshold*relative),local_seconds='5')['variants'][0]
        equal(x['local_comparison']['remote_strictly_faster'],relative>1)
for local in ('0','4/5'):
    equal(candidate.calculate(local_seconds=local)['variants'][0]['local_comparison']['relation'],
          'no_finite_upload_rate_wins')
c=dict(transmitted_bytes=15_000_000,extra_encode_seconds='1/5',extra_decode_seconds='1/10',
       comparison_authorized=True,quality_contract='same original information and same final-image requirement')
for rate in (200_000_000,400_000_000,800_000_000):
    result=candidate.calculate(upload_bits_per_second=rate,compression=c)
    comp=result['compression_comparison']
    equal(F(comp['complete_image_saving_seconds_exact']),F(120_000_000,rate)-F(3,10))
    equal(comp['compressed_strictly_faster'],rate<400_000_000)
    equal(F(comp['upload_equal_time_bits_per_second_exact']),F(400_000_000))
    for row in result['variants']:
        cursor=F(0)
        for event in row['stages']:
            equal(F(event['start_seconds_exact']),cursor)
            cursor+=F(event['duration_seconds_exact'])
            equal(F(event['end_seconds_exact']),cursor)
        equal(cursor,F(row['complete_final_image_seconds_exact']))
        equal(row['preview_ready_seconds'],None)
for overrides,relation in ((dict(transmitted_bytes=30_000_000),'compression_never_faster'),
    (dict(extra_encode_seconds='0',extra_decode_seconds='0'),'compressed_faster_at_all_finite_positive_rates'),
    (dict(transmitted_bytes=30_000_000,extra_encode_seconds='0',extra_decode_seconds='0'),'tie_all_rates')):
    equal(candidate.calculate(compression={**c,**overrides})['compression_comparison']['relation'],relation)
for kw in (dict(input_bytes=0),dict(upload_bits_per_second=None),dict(model_seconds=-1),
           dict(model_seconds=0.3),dict(input_bytes=True),dict(quality_contract=''),
           dict(compression={**c,'comparison_authorized':False}),dict(compression={**c,'quality_contract':'different'})):
    try:candidate.calculate(**kw)
    except ValueError:checks+=1
    else:raise AssertionError(kw)
print(f'{checks} independent checks passed')
