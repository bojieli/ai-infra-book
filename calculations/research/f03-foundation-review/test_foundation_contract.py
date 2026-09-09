import unittest, tempfile, hashlib, json, io, ast
from pathlib import Path
from unittest.mock import patch
from infra_calc import sources, reproduce, cli
from infra_calc.schema import Weight, Operator, Scenario, linear
from infra_calc.units import positive_number


class Response:
    def __init__(self, data=b"abc", status=200, headers=None):
        self.data = data
        self.status = status
        self.headers = headers or {}
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def read(self, n):
        self.read_sizes.append(n)
        return self.data[:n]


class FoundationContract(unittest.TestCase):
    def test_weight_positive_and_scalar_shape(self):
        for shape in [(True, 2), (-1, 2), (0, 2), (1.5, 2)]:
            with self.assertRaises(ValueError):
                Weight("x", shape)
        self.assertEqual(Weight("scalar", ()).parameters, 1)
        with self.assertRaises(ValueError):
            Weight("x", (2,)).record(True)

    def test_zero_linear_and_nested_symbolic_shapes(self):
        a = linear("empty", 0, 2, 3, Scenario())
        self.assertEqual(a.matrix_flops, 0)
        self.assertEqual(a.activation_read_bytes, 0)
        Operator("x", "special", {"nested": {"shape": [0, "T", None]}}, repeats=0)
        for n in [-1, True, 1.5]:
            with self.assertRaises(ValueError):
                linear("invalid", n, 2, 3, Scenario())

    def test_operator_invalid_counts(self):
        for v in [True, -1, float("nan"), float("inf"), 1.5]:
            with self.assertRaises(ValueError):
                Operator("x", "custom", {}, scalar_flops=v)

    def test_mutated_operator_and_large_integer(self):
        for field, value in [
            ("matrix_flops", True),
            ("scalar_flops", float("nan")),
            ("activation_write_bytes", -1),
        ]:
            op = Operator("x", "custom", {})
            setattr(op, field, value)
            with self.assertRaises(ValueError):
                op.record()
        self.assertEqual(positive_number(10**400, "big"), 10**400)

    def test_positive_number_bad_types(self):
        for v in [None, "2", True, float("nan"), float("inf"), 0]:
            with self.assertRaises(ValueError):
                positive_number(v, "value")

    def run_fetch(self, response, row_changes=None, failure=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "x").write_bytes(b"old")
            row = {
                "model": "exact",
                "file": "x",
                "status": "downloaded",
                "url": "https://example.invalid/fixed",
                "bytes": 3,
                "sha256": hashlib.sha256(b"abc").hexdigest(),
            }
            row.update(row_changes or {})
            with patch.object(sources, "PROJECT", root), patch.object(
                sources, "records", return_value=[row]
            ), patch.object(sources, "urlopen", return_value=response):
                if failure:
                    with self.assertRaises(failure):
                        sources.fetch_sources("exact")
                    self.assertEqual((root / "x").read_bytes(), b"old")
                else:
                    sources.fetch_sources("exact")
                    self.assertEqual((root / "x").read_bytes(), b"abc")
                self.assertEqual(sorted(p.name for p in root.iterdir()), ["x"])

    def test_full_get_optional_length_and_bound(self):
        for headers in [{}, {"Content-Length": "3"}]:
            r = Response(headers=headers)
            self.run_fetch(r)
            self.assertEqual(r.read_sizes, [4])

    def test_range_valid(self):
        r = Response(status=206, headers={"Content-Range": "bytes 8-10/20"})
        self.run_fetch(r, {"http_range": "bytes=8-10"})
        self.assertEqual(r.read_sizes, [4])

    def test_response_failures_preserve_original(self):
        cases = [
            Response(data=b"ab"),
            Response(data=b"abcd"),
            Response(data=b"xyz"),
            Response(headers={"Content-Length": "4"}),
            Response(headers={"Content-Length": "three"}),
            Response(status=206),
            Response(headers={"Content-Range": "bytes 0-2/3"}),
        ]
        for response in cases:
            self.run_fetch(response, failure=ValueError)

    def test_range_failures_preserve_original(self):
        for response in [
            Response(),
            Response(status=206, headers={"Content-Range": "bytes 8-10/*"}),
            Response(status=206, headers={"Content-Range": "bytes 8-10/10"}),
            Response(status=206, headers={"Content-Range": "bytes 8-10/20junk"}),
            Response(status=206, headers={"Content-Range": "bytes 9-11/20"}),
        ]:
            self.run_fetch(response, {"http_range": "bytes=8-10"}, ValueError)
        self.run_fetch(Response(), {"http_range": "bytes=8-"}, ValueError)
        self.run_fetch(Response(), {"http_range": "bytes=8-11"}, ValueError)

    def test_replace_failure_cleans_unique_temp(self):
        with patch.object(Path, "replace", side_effect=OSError("replace blocked")):
            self.run_fetch(Response(), failure=OSError)

    def test_source_bytes_and_exact_group(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "x").write_bytes(b"abc")
            row = {
                "model": "exact",
                "file": "x",
                "status": "downloaded",
                "bytes": 2,
                "sha256": hashlib.sha256(b"abc").hexdigest(),
            }
            with patch.object(sources, "PROJECT", root), patch.object(
                sources, "records", return_value=[row]
            ):
                with self.assertRaises(ValueError):
                    sources.read_source("x")
                with self.assertRaises(ValueError):
                    sources.fetch_sources("exa")

    def test_cli_json_rejects_nan(self):
        with patch.object(cli, "model_list", return_value={"nan": float("nan")}), patch(
            "sys.stderr", io.StringIO()
        ):
            with self.assertRaises(SystemExit) as e:
                cli.main(["models"])
        self.assertEqual(e.exception.code, 2)

    def test_manifest_validation_and_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "results").mkdir()
            (root / "results/README.md").write_text("ok")
            good = {
                "file": "results/README.md",
                "sha256": hashlib.sha256(b"ok").hexdigest(),
            }
            core = [good]
            for name in ["hardware.md", "hardware-audit.json", "hardware-audit.md"]:
                (root / "results" / name).write_text("ok")
                core.append({"file": "results/" + name, "sha256": good["sha256"]})
            with patch.object(reproduce, "PROJECT", root), patch.object(
                reproduce, "verify_sources", return_value={}
            ), patch.object(reproduce, "input_hashes", return_value=[]):
                for rows in [
                    [],
                    [good],
                    [good, good],
                    [{"file": "../README.md", "sha256": good["sha256"]}],
                    [{"file": "results/other", "sha256": "invalid"}],
                ]:
                    (root / "results/manifest.json").write_text(
                        json.dumps({"inputs": [], "artifacts": rows, "scope": "test"})
                    )
                    with self.assertRaises(ValueError):
                        reproduce.verify_results(False)
                (root / "results/manifest.json").write_text(
                    json.dumps({"inputs": [], "artifacts": core, "scope": "test"})
                )
                self.assertEqual(
                    reproduce.verify_results(False)["verified_artifacts"], 4
                )
                # A removed scene's old file survives reproduce, but is no longer owned.
                obsolete = root / "results/removed-scene.json"
                obsolete.write_text("{}")
                prior = core + [
                    {
                        "file": "results/removed-scene.json",
                        "sha256": hashlib.sha256(b"{}").hexdigest(),
                    }
                ]
                manifest_path = root / "results/manifest.json"
                manifest_path.write_text(
                    json.dumps({"inputs": [], "artifacts": prior, "scope": "test"})
                )
                self.assertEqual(
                    reproduce.verify_results(False)["verified_artifacts"], 5
                )
                # Reproduce rebuilds its explicit artifacts list from the remaining scenes.
                manifest_path.write_text(
                    json.dumps({"inputs": [], "artifacts": core, "scope": "test"})
                )
                self.assertEqual(
                    reproduce.verify_results(False)["verified_artifacts"], 4
                )
                self.assertTrue(obsolete.exists())
                (root / "results/README.md").write_text("changed")
                with self.assertRaises(ValueError):
                    reproduce.verify_results(False)

    def test_manifest_path_normalization(self):
        for name in [
            "results/./README.md",
            "results//README.md",
            "./results/README.md",
        ]:
            self.assertNotEqual(name, Path(name).as_posix())

    def test_reproduce_save_rejects_nonfinite(self):
        tree = ast.parse(Path(reproduce.__file__).read_text())
        run = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"
        )
        save = next(
            n for n in run.body if isinstance(n, ast.FunctionDef) and n.name == "save"
        )
        module = ast.Module(body=[save], type_ignores=[])
        with tempfile.TemporaryDirectory() as temp:
            namespace = {
                "json": json,
                "output": Path(temp),
                "artifacts": [],
                "markdown": lambda x: "md",
            }
            exec(compile(module, "extracted_real_save", "exec"), namespace)
            with self.assertRaises(ValueError):
                namespace["save"]("bad", {"n": float("inf")})
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_calc_entry_bound(self):
        self.assertIn("calc.py", {r["file"] for r in reproduce.input_hashes()})


if __name__ == "__main__":
    unittest.main()
