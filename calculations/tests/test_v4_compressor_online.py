from pathlib import Path
import sys
import unittest

try:
    import torch
except ImportError:
    torch = None
for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
import infra_calc.topics

for ancestor in Path(__file__).resolve().parents:
    for name in (
        "v4-attention-projections",
        "v4-compressor-training",
        "v4-compressor-overlap",
    ):
        p = ancestor / name / "public/src/infra_calc/topics"
        if p.is_dir():
            infra_calc.topics.__path__.insert(0, str(p))
infra_calc.topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import v4_compressor_online as m
from infra_calc.topics import v4_compressor_overlap as overlap
from infra_calc.topics import v4_compressor_training as nonoverlap


class OnlineTests(unittest.TestCase):
    def fixture(self, ratio, start, count):
        width = 4 if ratio == 4 else 2
        slots = 2 * ratio if ratio == 4 else ratio
        x = [[(i + j) % 7 / 9 - 0.3 for j in range(3)] for i in range(count)]
        wk = [[(i + j - 2) / 7 for j in range(3)] for i in range(width)]
        wg = [[(2 * i - j + 1) / 11 for j in range(3)] for i in range(width)]
        ape = [[(i % 5 - j) / 13 for j in range(width)] for i in range(ratio)]
        initialkv = [[(i % 7 + j) / 17 for j in range(width)] for i in range(slots)]
        initialscore = [[(i % 11 - j) / 23 for j in range(width)] for i in range(slots)]
        positions = [p for p in range(start, start + count) if (p + 1) % ratio == 0]
        angles = [[0.2 + i * 0.3] for i in range(len(positions))]
        up = [[0.4, -0.3] for _ in positions]
        finalkv = [[(i % 3 + j - 1) / 29 for j in range(width)] for i in range(slots)]
        finalscore = [
            [(i % 5 - j + 1) / 31 for j in range(width)] for i in range(slots)
        ]
        return (
            initialkv,
            initialscore,
            x,
            start,
            ratio,
            wk,
            wg,
            ape,
            [0.8, 1.2],
            angles,
            up,
            finalkv,
            finalscore,
        )

    @unittest.skipIf(torch is None, "FP64 autograd requires torch")
    def test_joint_state_copy_and_parameter_vjp(self):
        for ratio, start, count in [(4, 3, 6), (4, 4, 9), (128, 127, 3)]:
            args = self.fixture(ratio, start, count)
            got = m.reference(*args)
            indices = [0, 1, 2, 5, 6, 7, 8]
            tensors = {
                i: torch.tensor(args[i], dtype=torch.float64, requires_grad=True)
                for i in indices
            }
            kv, score = tensors[0], tensors[1]
            tx, wk, wg, ape, gamma = [tensors[i] for i in (2, 5, 6, 7, 8)]
            out = []
            emits = 0
            d = 2
            for step in range(count):
                pos = start + step
                slot = (ratio if ratio == 4 else 0) + pos % ratio
                kv = kv.clone()
                score = score.clone()
                kv[slot] = wk @ tx[step]
                score[slot] = wg @ tx[step] + ape[pos % ratio]
                if (pos + 1) % ratio == 0:
                    vals = (
                        torch.cat([kv[:ratio, :d], kv[ratio:, d:]], 0)
                        if ratio == 4
                        else kv
                    )
                    scores = (
                        torch.cat([score[:ratio, :d], score[ratio:, d:]], 0)
                        if ratio == 4
                        else score
                    )
                    pooled = (scores.softmax(0) * vals).sum(0)
                    normalized = (
                        pooled * (pooled.square().mean() + 1e-6).rsqrt() * gamma
                    )
                    freq = torch.polar(
                        torch.ones(1, dtype=torch.float64),
                        torch.tensor(args[9][emits], dtype=torch.float64),
                    )
                    out.append(
                        torch.view_as_real(
                            torch.view_as_complex(normalized.reshape(1, 2)) * freq
                        ).flatten()
                    )
                    emits += 1
                    if ratio == 4:
                        kv = torch.cat([kv[ratio:], kv[ratio:]], 0)
                        score = torch.cat([score[ratio:], score[ratio:]], 0)
            loss = (
                sum(
                    (v * torch.tensor(args[10][i], dtype=torch.float64)).sum()
                    for i, v in enumerate(out)
                )
                + (kv * torch.tensor(args[11], dtype=torch.float64)).sum()
                + (score * torch.tensor(args[12], dtype=torch.float64)).sum()
            )
            loss.backward()
            for key, index in [
                ("dinitial_kv", 0),
                ("dinitial_score", 1),
                ("dx", 2),
                ("dwkv", 5),
                ("dwgate", 6),
                ("dape", 7),
                ("dgamma", 8),
            ]:
                self.assertTrue(
                    torch.allclose(
                        torch.tensor(got[key], dtype=torch.float64),
                        tensors[index].grad,
                        atol=2e-10,
                        rtol=2e-10,
                    ),
                    key,
                )

    def close_nested(self, a, b):
        if isinstance(a, list):
            self.assertEqual(len(a), len(b))
            for x, y in zip(a, b):
                self.close_nested(x, y)
        else:
            self.assertAlmostEqual(a, b, places=9)

    def add_nested(self, a, b):
        return (
            [self.add_nested(x, y) for x, y in zip(a, b)]
            if isinstance(a, list)
            else a + b
        )

    def test_ratio4_prefill_then_online_chain(self):
        for prefix in (3, 5):
            fullargs = self.fixture(4, prefix, 9)
            allx = fullargs[2]
            wk, wg, ape, gamma = fullargs[5:9]
            all_angles = [[0.2], [0.5]]
            allup = [[0.4, -0.3], [0.2, 0.7]]
            pre = overlap.reference(
                allx[:prefix],
                wk,
                wg,
                ape,
                gamma,
                all_angles[: prefix // 4],
                allup[: prefix // 4],
            )
            online = m.reference(
                pre["state_kv"],
                pre["state_score"],
                allx[prefix:],
                prefix,
                4,
                wk,
                wg,
                ape,
                gamma,
                all_angles[prefix // 4 :],
                allup[prefix // 4 :],
            )
            joinedpre = overlap.reference(
                allx[:prefix],
                wk,
                wg,
                ape,
                gamma,
                all_angles[: prefix // 4],
                allup[: prefix // 4],
                online["dinitial_kv"],
                online["dinitial_score"],
            )
            whole = overlap.reference(allx, wk, wg, ape, gamma, all_angles, allup)
            self.close_nested(joinedpre["dx"] + online["dx"], whole["dx"])
            for key in ("dwkv", "dwgate", "dape", "dgamma"):
                self.close_nested(
                    self.add_nested(joinedpre[key], online[key]), whole[key]
                )
            self.close_nested(pre["output"] + online["output"], whole["output"])

    def test_ratio128_tail_prefill_chain(self):
        args = self.fixture(128, 127, 256)
        x = args[2]
        wk, wg, ape, gamma = args[5:9]
        initialkv = [[0.0] * 2 for _ in range(128)]
        initialscore = [[float("-inf")] * 2 for _ in range(128)]
        for i, row in enumerate(x[:127]):
            initialkv[i] = m.ops.mv(wk, row)
            initialscore[i] = [v + ape[i][j] for j, v in enumerate(m.ops.mv(wg, row))]
        angles = [[0.2], [0.5]]
        up = [[0.4, -0.3], [0.2, 0.7]]
        online = m.reference(
            initialkv, initialscore, x[127:], 127, 128, wk, wg, ape, gamma, angles, up
        )
        full = nonoverlap.reference(x, wk, wg, ape, gamma, angles, up)
        pre_dx = []
        pre_dwk = [[0.0] * 3 for _ in range(2)]
        pre_dwg = [[0.0] * 3 for _ in range(2)]
        pre_ape = [[0.0] * 2 for _ in range(128)]
        for i, row in enumerate(x[:127]):
            dxk, dwk = m.ops.mv_vjp(wk, row, online["dinitial_kv"][i])
            dxg, dwg = m.ops.mv_vjp(wg, row, online["dinitial_score"][i])
            pre_dx.append(self.add_nested(dxk, dxg))
            pre_dwk = self.add_nested(pre_dwk, dwk)
            pre_dwg = self.add_nested(pre_dwg, dwg)
            pre_ape[i] = online["dinitial_score"][i]
        self.close_nested(pre_dx + online["dx"], full["dx"])
        for key, extra in [("dwkv", pre_dwk), ("dwgate", pre_dwg), ("dape", pre_ape)]:
            self.close_nested(self.add_nested(extra, online[key]), full[key])
        self.close_nested(online["dgamma"], full["dgamma"])
        self.close_nested(online["output"], full["output"])

    def test_timegraph_boundaries_and_no_implicit_history(self):
        for ratio, start, count in [(4, 3, 6), (128, 127, 130), (4, 4, 1)]:
            r = m.calculate(ratio=ratio, start_pos=start, tokens=count)
            self.assertEqual(r, m.calculate(**r["scenario"]))
            expected = (start + count) // ratio - start // ratio
            self.assertEqual(r["dimensions"]["emits_per_batch"], expected)
            self.assertEqual(sum(event["emit"] for event in r["timeline"]), expected)
            self.assertFalse(r["coverage"]["history_producer_vjp_included"])
            self.assertIsNone(r["coverage"]["cast_surrogate_gradient"])
        with self.assertRaises(ValueError):
            m.calculate(start_pos=0)


if __name__ == "__main__":
    unittest.main()
