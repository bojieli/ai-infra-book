"""Exact external hand oracles and packet/key/credit boundary regressions."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics import protocol_handshake as handshake
from infra_calc.topics import protocol_early_stream as streaming


def equal_packet_inputs(outcome="accept", retry=True):
    p = streaming.example()
    p.update(
        early_result=outcome, application_retry_authorized=retry,
        request_payload_bytes=7008, response_payload_bytes=100,
        packet_payload_bytes=1168, zero_rtt_overhead_bytes=32,
        one_rtt_overhead_bytes=32, response_overhead_bytes=1100,
        c2s_bits_per_second=9824, s2c_bits_per_second=9824,
        c2s_propagation_seconds=1, s2c_propagation_seconds=1, model_seconds=0,
        packets={"client_hello": [1200], "server_flight": [1200, 1200],
                 "handshake_ack": [1200], "client_finished": [1200]},
    )
    return p


class ProtocolTransportTests(unittest.TestCase):
    def test_six_hand_derived_handshake_completion_times(self):
        # Declared actual lengths: TCPrequest180,response280; QUIC adds28B.
        # These constants were derived from the message flights, not summaries.
        expected = {
            ("tcp_tls13", "fresh"): "0.3106192",
            ("tcp_tls13", "resume"): "0.3104352",
            ("tcp_tls13", "early_accept"): "0.2103472",
            ("tcp_tls13", "early_reject"): "0.3104352",
            ("quic_v1", "fresh"): "0.21088992",
            ("quic_v1", "early_accept"): "0.11059904",
        }
        for (protocol, mode), complete in expected.items():
            with self.subTest(protocol=protocol, mode=mode):
                result = handshake.calculate(handshake.example(protocol, mode))
                self.assertEqual(F(result["milestones"]["complete_response"]), F(complete))
                self.assertEqual(result["summary"]["application_execution_count"], 1)

    def test_rejected_early_data_needs_application_retry_authorization(self):
        for protocol in ("tcp_tls13", "quic_v1"):
            for retry in (False, True):
                with self.subTest(protocol=protocol, retry=retry):
                    p = handshake.example(protocol, "early_reject")
                    p["application_retry_authorized"] = retry
                    r = handshake.calculate(p)
                    self.assertEqual(r["summary"]["request_payload_sent_bytes"], 100 * (1 + retry))
                    self.assertEqual(r["summary"]["accepted_unique_request_bytes"], 100 if retry else 0)
                    self.assertEqual(r["summary"]["application_execution_count"], int(retry))
                    self.assertEqual("complete_response" in r["milestones"], retry)
            p = handshake.example(protocol, "early_accept")
            p["application_early_data_authorized"] = False
            with self.assertRaises(ValueError):
                handshake.calculate(p)

    def test_quic_amplification_uses_received_udp_and_handshake_arrival(self):
        for sizes, ack, completes in (([1200] * 3, False, True),
                                     ([1200] * 4, False, False),
                                     ([1200] * 4, True, True),
                                     ([1200, 1200, 1228], False, False)):
            with self.subTest(sizes=sizes, ack=ack):
                p = handshake.example()
                p["packets"]["server_flight"] = sizes
                p["server_flight_ack"] = ack
                r = handshake.calculate(p)
                self.assertEqual(r["status"] == "complete", completes)
                sent = 0
                validation = r["milestones"].get("server_address_validated")
                for packet in sorted(r["transmissions"], key=lambda e: F(e["start"])):
                    if packet["direction"] != "s2c":
                        continue
                    sent += packet["declared_bytes"]
                    if validation is None or F(packet["start"]) < F(validation):
                        received = sum(e["declared_bytes"] for e in r["transmissions"]
                                       if e["direction"] == "c2s" and F(e["arrival"]) <= F(packet["start"]))
                        self.assertLessEqual(sent, 3 * received)
                if not completes:
                    self.assertEqual(r["status"], "budget_blocked_in_declared_graph")
                    self.assertTrue(r["pending_packets"])
                if ack:
                    proof = next(e for e in r["transmissions"] if e["flight"] == "handshake_ack")
                    self.assertEqual(F(validation), F(proof["arrival"]))
                    self.assertGreater(F(validation), F(proof["end"]))

    def test_stream_same_time_keys_and_rejection_match_integer_hand_oracle(self):
        # All datagrams serialize for1s. Keys at5; fourth early packet ends5.
        cases = (("accept", True, 2336, 10, 12),
                 ("reject", True, 7008, 14, 16),
                 ("reject", False, 0, None, None))
        for outcome, retry, normal, execution, complete in cases:
            with self.subTest(outcome=outcome, retry=retry):
                r = streaming.calculate(equal_packet_inputs(outcome, retry))
                m, s = r["milestones"], r["summary"]
                self.assertEqual(F(m["client_1rtt_keys_installed"]), 5)
                self.assertEqual(F(m["server_address_validated"]), 7)
                self.assertEqual(s["early_payload_sent_bytes"], 4672)
                self.assertEqual(s["one_rtt_payload_sent_bytes"], normal)
                for key, expected in (("application_execution", execution), ("complete_response", complete)):
                    self.assertEqual(None if key not in m else F(m[key]), expected)
                early = [e for e in r["transmissions"] if e["kind"] == "request" and e["encryption_level"] == "0rtt"]
                self.assertEqual([(F(e["start"]), F(e["end"])) for e in early],
                                 [(1, 2), (2, 3), (3, 4), (4, 5)])

    def test_keys_arriving_midpacket_do_not_preempt_or_relabel(self):
        for outcome, retry, complete in (("accept", True, F(47, 4)),
                                         ("reject", True, F(63, 4)),
                                         ("reject", False, None)):
            with self.subTest(outcome=outcome, retry=retry):
                p = equal_packet_inputs(outcome, retry)
                p["s2c_bits_per_second"] = "39296/3"
                r = streaming.calculate(p)
                key_time = F(r["milestones"]["client_1rtt_keys_installed"])
                self.assertEqual(key_time, F(9, 2))
                request = [e for e in r["transmissions"] if e["kind"] == "request"]
                crossing = [e for e in request if F(e["start"]) < key_time < F(e["end"])]
                self.assertEqual(len(crossing), 1)
                self.assertEqual(crossing[0]["encryption_level"], "0rtt")
                self.assertEqual(F(crossing[0]["end"]), 5)
                for e in request:
                    self.assertEqual(e["encryption_level"] == "0rtt", F(e["start"]) < key_time)
                actual = r["milestones"].get("complete_response")
                self.assertEqual(None if actual is None else F(actual), complete)

    def test_retries_preserve_offsets_with_new_packet_numbers_and_unique_tail(self):
        # One-byte tail exercises nonmultiple payload boundaries independently.
        p = equal_packet_inputs("reject", True)
        p["request_payload_bytes"] = 7009
        r = streaming.calculate(p)
        request = [e for e in r["transmissions"] if e["kind"] == "request"]
        self.assertEqual([e["packet_number"] for e in request], list(range(len(request))))
        self.assertTrue(all(e["packet_number_space"] == "application" for e in request))
        coverage = Counter()
        early = Counter()
        accepted = Counter()
        for e in request:
            span = range(e["offset"], e["end_offset"])
            self.assertEqual(len(span), e["payload_bytes"])
            coverage.update(span)
            if e["encryption_level"] == "0rtt":
                early.update(span)
                self.assertFalse(e["accepted"])
            if e["accepted"]:
                accepted.update(span)
        self.assertEqual(accepted, Counter({i: 1 for i in range(7009)}))
        self.assertEqual(coverage, accepted + early)
        self.assertEqual(max(early.values()), 1)
        self.assertEqual(r["summary"]["application_execution_count"], 1)
        self.assertEqual([e["payload_bytes"] for e in request if e["encryption_level"] == "1rtt"][-1], 1)

    def test_controls_share_serializers_and_final_bytes_are_conserved(self):
        r = streaming.calculate(equal_packet_inputs())
        for direction in ("c2s", "s2c"):
            records = sorted((e for e in r["transmissions"] if e["direction"] == direction),
                             key=lambda e: F(e["start"]))
            self.assertTrue(all(F(a["end"]) <= F(b["start"]) for a, b in zip(records, records[1:])))
            self.assertEqual(r["summary"]["modeled_wire_bytes_by_direction"][direction],
                             sum(e["udp_bytes"] + 28 for e in records))
        controls = {e["kind"]: e for e in r["transmissions"] if e["kind"] in ("handshake_ack", "client_finished")}
        self.assertEqual((F(controls["handshake_ack"]["start"]), F(controls["handshake_ack"]["end"])), (5, 6))
        self.assertEqual((F(controls["client_finished"]["start"]), F(controls["client_finished"]["end"])), (6, 7))
        response = [e for e in r["transmissions"] if e["kind"] == "response"]
        self.assertEqual(sum(e["payload_bytes"] for e in response), 100)
        self.assertEqual(F(r["milestones"]["complete_response"]), max(F(e["arrival"]) for e in response))

    def test_invalid_authorization_initial_payload_and_scale_are_rejected(self):
        cases = []
        for field, value in (("valid_psk", 1), ("application_early_data_authorized", False)):
            p = handshake.example(mode="early_accept")
            p[field] = value
            cases.append((handshake.calculate, p))
        p = handshake.example()
        p["packets"]["client_hello"] = [1199]
        cases.append((handshake.calculate, p))
        p = handshake.example("tcp_tls13", "early_accept")
        p["packets"]["early_request"] = [161]  #100payload cannot fit62overhead.
        cases.append((handshake.calculate, p))
        for field, value in (("one_rtt_overhead_bytes", 31), ("packet_payload_bytes", 0),
                             ("request_payload_bytes", 10**12), ("application_retry_authorized", 1)):
            p = equal_packet_inputs()
            p[field] = value
            cases.append((streaming.calculate, p))
        for index, (calculate, inputs) in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                calculate(inputs)


if __name__ == "__main__":
    unittest.main()
