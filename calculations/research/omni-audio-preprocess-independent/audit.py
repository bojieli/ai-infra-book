"""Independent geometry, filter construction, source execution and interface audit."""
from pathlib import Path
import hashlib
import json
import sys
import unittest
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'omni-audio-preprocess'
sys.path.insert(0, str(CANDIDATE))
import omni_audio_preprocess as candidate
from source_runner import load

checks = []
def check(name, truth):
    assert truth, name
    checks.append(name)

for row in json.loads((CANDIDATE / 'bindings.json').read_text()):
    check('frozen:' + row['file'], hashlib.sha256((CANDIDATE / row['file']).read_bytes()).hexdigest() == row['sha256'])
for row in candidate.evidence():
    check('source:' + row['file'], True)
e = load()
check('constructor overrides serialized fields', (e.chunk_length, e.n_samples, e.nb_max_frames) == (30, 480000, 3000))
# Independent piecewise Slaney centers and direct triangle formula, not source helpers.
max_mel = 15 + 27 * np.log(8) / np.log(6.4)
mels = np.linspace(0, max_mel, 130)
centers = np.where(mels < 15, mels * 200 / 3, 1000 * np.exp((mels - 15) * np.log(6.4) / 27))
freqs = np.arange(201) * 40
bank = np.empty((201, 128))
for j in range(128):
    lo, middle, hi = centers[j:j+3]
    bank[:, j] = np.maximum(0, np.minimum((freqs-lo)/(middle-lo), (hi-freqs)/(hi-middle))) * 2/(hi-lo)
check('independent Slaney bank', np.max(np.abs(bank - e.mel_filters)) < 1e-14)
check('Slaney logarithmic center count', candidate.mel_filter_initialization()['logarithmic_centers'] == int(sum(mels >= 15)))
rng = np.random.default_rng(24091)
cases = [[201], [319], [320], [321], [479], [479, 800], [1, 961], [200, 640], [480001], [4800000]]
records = []
for lengths in cases:
    waves = [rng.normal(0, .1, n).astype(np.float32) for n in lengths]
    actual = e(waves, sampling_rate=16000, padding=True, return_attention_mask=True, return_tensors='np')
    result = candidate.calculate(lengths)
    retained = [min(n, 480000) for n in lengths]
    p = max(retained)
    starts = list(range(0, p+1, 160))
    # Include final centered frame then drop it; use explicit frame start list.
    frame_count = len(starts) - 1
    mask = np.array([[int(i < n) for i in range(0, p, 160)] for n in retained], dtype=np.int32)[:, :frame_count]
    check(str(lengths) + ':mask enumeration', np.array_equal(mask, actual['attention_mask']))
    check(str(lengths) + ':geometry', result['geometry']['valid_mel_lengths'] == mask.sum(-1).tolist())
    check(str(lengths) + ':shape', list(actual['input_features'].shape) == [len(lengths), 128, frame_count])
    check(str(lengths) + ':matrix', result['summary']['matrix_flops'] == 2*len(lengths)*128*201*frame_count)
    check(str(lengths) + ':scalar', result['summary']['known_scalar_flops'] == 1205 + len(lengths)*(400*(frame_count+1) + 457*frame_count + 1))
    valid_features = torch.from_numpy(actual['input_features']).permute(0, 2, 1)[torch.from_numpy(mask).bool()].T
    check(str(lengths) + ':bridge bytes', valid_features.numel()*valid_features.element_size() == result['summary']['encoder_input_bytes'])
    error = None
    if p < 2000:
        expected = []
        window = np.sin(np.pi * np.arange(400)/400)**2
        for wave in waves:
            padded = np.pad(np.pad(wave, (0, p-len(wave))), (200,200), mode='reflect')
            frames = np.array([padded[s:s+400] * window for s in starts])
            power = np.abs(np.fft.rfft(frames, axis=1)[:-1]).T**2
            log = np.log10(np.maximum(bank.T @ power, 1e-10))
            expected.append((np.maximum(log, log.max()-8)+4)/4)
        error = float(np.max(np.abs(np.array(expected) - actual['input_features'])))
        check(str(lengths) + ':independent numpy RFFT mel', error < 1e-4)
    records.append(dict(lengths=lengths, frames=frame_count, valid=mask.sum(-1).tolist(), max_error=error))
# Native periodic implementation really owns 401 float32 values, returns a narrow view.
hann = torch.hann_window(400)
check('Hann401 storage', hann.untyped_storage().nbytes() == 401*4 and hann.numel() == 400)
# Dimension max returns both values and indices, even when caller only keeps values.
x = torch.randn(2,128,5)
time_max = x.max(dim=2, keepdim=True)
mel_max = time_max.values.max(dim=1, keepdim=True)
max_interfaces = dict(time_index_dtype=str(time_max.indices.dtype), time_index_bytes=time_max.indices.numel()*8, mel_index_bytes=mel_max.indices.numel()*8)
check('max indices allocation', max_interfaces['time_index_bytes'] == 8*2*128 and max_interfaces['mel_index_bytes'] == 8*2)
# Independent recursion tree expansion for the separate full-complex FFT reference.
nodes = [(400,1)]
products = additions = 0
while nodes:
    n, multiplicity = nodes.pop()
    if n == 1:
        continue
    radix = 2 if n % 2 == 0 else 5
    products += multiplicity*n*radix
    additions += multiplicity*(2*n*radix + 2*n*(radix-1))
    nodes.append((n//radix, multiplicity*radix))
check('separate FFT arithmetic', candidate.reference_fft_work() == dict(real_multiplications=4*products, real_additions=additions, complex_products=products))
for path in sorted((CANDIDATE/'results').glob('*.json')):
    old = json.loads(path.read_text())
    check('replay:' + path.name, candidate.calculate(**old['scenario']) == old)
suite = unittest.defaultTestLoader.discover(str(CANDIDATE), pattern='test_omni_audio_preprocess.py')
test_result = unittest.TextTestRunner(verbosity=2).run(suite)
check('original tests no skip', test_result.wasSuccessful() and not test_result.skipped)
output = dict(check_count=len(checks), checks=checks, numeric_cases=records, max_interfaces=max_interfaces, tests=dict(run=test_result.testsRun, skips=len(test_result.skipped)), torch_version=torch.__version__, torch_git=torch.version.git_version, candidate_sha=hashlib.sha256((CANDIDATE/'omni_audio_preprocess.py').read_bytes()).hexdigest())
(HERE/'results.json').write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps({k:v for k,v in output.items() if k not in ('checks','numeric_cases')}, indent=2))
