"""Hand-derived sequence timings and cross-request credit/identity invariants."""

from fractions import Fraction
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.connection_sequence import calculate


def small_inputs(**overrides):
    inputs = dict(
        input_bytes=2, output_bytes=1, segment_bytes=1,
        upload_bits_per_second=8, download_bits_per_second=8,
        forward_propagation_seconds=1, reverse_propagation_seconds=1,
        initial_window_bytes=1, max_window_bytes=4, receive_window_bytes=4,
        ack_growth_bytes=1, data_header_bytes=0, ack_bytes=0,
        rto_seconds=100, model_seconds=0, handshake=[],
    )
    inputs.update(overrides)
    return inputs


class ConnectionSequenceTests(unittest.TestCase):
    def test_four_handshake_strategies_match_hand_derivation(self):
        # Each one-byte message costs one second on wire plus one in flight.
        graph = [{"direction": direction, "bytes": 1}
                 for direction in ("c2s", "s2c", "c2s", "s2c")]
        expected = {
            "fresh": ([15, 31, 47, 63], [16, 32, 48, 64], 16),
            "ticket": ([11, 23, 35, 47], [12, 24, 36, 48], 8),
            "reuse_reset": ([15, 23, 31, 39], [16, 24, 32, 40], 4),
            "reuse_warm": ([15, 21, 27, 33], [16, 22, 28, 34], 4),
        }
        for strategy, (complete, quiet, handshake_bytes) in expected.items():
            with self.subTest(strategy=strategy):
                result = calculate(**small_inputs(
                    strategy=strategy, submit_on="quiet", handshake=graph))
                self.assertEqual([Fraction(r["complete_received_seconds_exact"])
                                  for r in result["requests"]], complete)
                self.assertEqual([Fraction(r["last_ack_seconds_exact"])
                                  for r in result["requests"]], quiet)
                self.assertEqual(result["summary"]["handshake_wire_bytes"], handshake_bytes)
                self.assertEqual(result["summary"]["total_wire_bytes"], 12 + handshake_bytes)

    def test_pending_ack_occupies_forward_link_across_requests(self):
        # ACK [5,6] is still on wire when response one arrives at t=5.
        expected = {
            "complete_received": ([0, 5, 11, 17], [0, 6, 12, 18],
                                  [5, 11, 17, 23], [7, 13, 19, 25]),
            "quiet": ([0, 7, 14, 21], [0, 7, 14, 21],
                      [5, 12, 19, 26], [7, 14, 21, 28]),
        }
        for mode, (submits, starts, complete, quiet) in expected.items():
            with self.subTest(mode=mode):
                result = calculate(**small_inputs(input_bytes=1, ack_bytes=1,
                    max_window_bytes=1, receive_window_bytes=1,
                    ack_growth_bytes=0, submit_on=mode))
                for field, values in (("submit_seconds_exact", submits),
                        ("complete_received_seconds_exact", complete),
                        ("last_ack_seconds_exact", quiet)):
                    self.assertEqual([Fraction(r[field]) for r in result["requests"]], values)
                uploads = [r for r in result["transmissions"]
                           if r["kind"] == "data" and r["transfer"] == "upload"]
                self.assertEqual([Fraction(r["start_seconds_exact"]) for r in uploads], starts)
                for direction in ("c2s", "s2c"):
                    wires = [r for r in result["transmissions"] if r["direction"] == direction]
                    self.assertTrue(all(Fraction(a["end_seconds_exact"]) <=
                                        Fraction(b["start_seconds_exact"])
                                        for a, b in zip(wires, wires[1:])))

    def test_reset_retains_pending_credit_and_warm_windows_are_directional(self):
        result = calculate(**small_inputs(input_bytes=1, ack_bytes=1, strategy="reuse_reset"))
        submits = [e for e in result["application_events"] if e["event"] == "request_submit"]
        for request_id in range(1, 4):
            next_submit = submits[request_id]
            self.assertEqual(next_submit["outstanding_unique_bytes"]["download"], 1)
            self.assertEqual(next_submit["cwnd_bytes"]["download"], 1)
            late_ack = next(e for e in result["window_events"]
                if e["request_id"] == request_id and e["transfer"] == "download"
                and e["reason"] == "ack" and Fraction(e["time_seconds_exact"]) >
                Fraction(next_submit["time_seconds_exact"]))
            self.assertEqual(late_ack["cwnd_bytes"], 2)
            self.assertEqual(late_ack["connection_outstanding_unique_bytes"], 0)
        warm = calculate(**small_inputs(submit_on="quiet", strategy="reuse_warm"))
        # Two upload ACKs versus one download ACK; do not copy the larger window.
        self.assertEqual(warm["requests"][1]["initial_cwnd_bytes"], {"upload": 3, "download": 2})
        unequal = calculate(**small_inputs(request_count=1,
            initial_upload_window_bytes=3, initial_download_window_bytes=2))
        self.assertEqual(unequal["requests"][0]["initial_cwnd_bytes"], {"upload": 3, "download": 2})

    def test_loss_is_confined_to_selected_request_identity(self):
        result = calculate(**small_inputs(drop_upload_packet=0, loss_request_id=2))
        retries = [r for r in result["transmissions"] if r.get("retransmission")]
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0]["request_id"], 2)
        self.assertEqual(retries[0]["transfer"], "upload")
        self.assertEqual(result["summary"]["recoveries"], 1)
        self.assertEqual(result["summary"]["unique_input_bytes"], 8)
        self.assertEqual(result["summary"]["unique_output_bytes"], 4)
        self.assertEqual(result["summary"]["total_wire_bytes"], 13)
        self.assertEqual([r["retransmission_wire_bytes"] for r in result["requests"]], [0, 1, 0, 0])
        for request in result["requests"]:
            self.assertEqual(request["transfers"]["upload"]["unique_received_bytes"], 2)

    def test_reject_invalid_sequence_and_directional_credit(self):
        invalid = [dict(request_count=True), dict(request_count=1.0),
            dict(request_count=101), dict(think_seconds=-1),
            dict(max_total_packets=11), dict(loss_request_id=5),
            dict(initial_upload_window_bytes=0), dict(initial_download_window_bytes=5),
            dict(connection_ready_seconds=1), dict(strategy="new_warm"),
            dict(submit_on="timer_heap_empty")]
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                calculate(**small_inputs(**overrides))


if __name__ == "__main__":
    unittest.main()
