"""Read SHA-locked TFRecord events without executing training or fitting data."""
from tensorboard.compat.proto.event_pb2 import Event
from pathlib import Path
import json
import math
import struct

root = Path(__file__).resolve().parent
rows = []
for path in sorted(root.glob('*.tfevents')):
    data = path.read_bytes()
    position = 0
    while position < len(data):
        length = struct.unpack_from('<Q', data, position)[0]
        start = position + 12
        assert start + length + 4 <= len(data)
        event = Event.FromString(data[start:start + length])
        position = start + length + 4
        for value in event.summary.value:
            scalar = value.simple_value if value.HasField('simple_value') else (
                value.tensor.float_val[0] if value.tensor.float_val else None)
            if scalar is not None:
                rows.append(dict(file=path.name, tag=value.tag, step=event.step,
                                 value=scalar, wall_time=event.wall_time))
loss = next(row['value'] for row in rows if row['tag'].endswith('/lm loss validation'))
ppl = next(row['value'] for row in rows if row['tag'].endswith('/lm loss validation ppl'))
assert abs(math.exp(loss) - ppl) / ppl < 1e-7
assert round(loss, 6) == 2.574117
(root/'val-log-scalars.json').write_text(json.dumps(dict(records=rows, loss=loss, ppl=ppl,
    exp_loss=math.exp(loss), relative_difference=abs(math.exp(loss)-ppl)/ppl,
    notebook_rounded_loss=2.574117), indent=2)+'\n')
