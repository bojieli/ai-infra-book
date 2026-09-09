"""Freeze summaries for realistic loads and one fully replayable small trace."""

from pathlib import Path
import json
from calculate import calculate

ROOT = Path(__file__).resolve().parent


def main():
    rows = []
    for workload, changes in [
        ("image", {}),
        ("small", dict(input_bytes=65536, output_bytes=65536)),
    ]:
        for submit_on in ["quiet", "complete_received"]:
            for strategy in ["fresh", "ticket", "reuse_reset", "reuse_warm"]:
                inputs = dict(changes, submit_on=submit_on, strategy=strategy)
                result = calculate(**inputs)
                rows.append(
                    dict(
                        id=f"{workload}-{submit_on}-{strategy}",
                        inputs=inputs,
                        requests=result["requests"],
                        summary=result["summary"],
                        links=result["links"],
                    )
                )
    inputs = dict(
        strategy="reuse_warm",
        submit_on="complete_received",
        drop_upload_packet=12,
        loss_request_id=2,
    )
    result = calculate(**inputs)
    assert result["summary"]["recoveries"] == 1
    assert {
        x["request_id"] for x in result["transmissions"] if x.get("retransmission")
    } == {2}
    rows.append(
        dict(
            id="image-request2-loss",
            inputs=inputs,
            requests=result["requests"],
            summary=result["summary"],
            links=result["links"],
        )
    )
    (ROOT / "result.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = dict(
        input_bytes=1,
        output_bytes=1,
        segment_bytes=1,
        upload_bits_per_second=8,
        download_bits_per_second=8,
        forward_propagation_seconds="1",
        reverse_propagation_seconds="1",
        initial_window_bytes=1,
        max_window_bytes=1,
        receive_window_bytes=1,
        ack_growth_bytes=0,
        data_header_bytes=0,
        ack_bytes=1,
        rto_seconds="100",
        model_seconds="0",
        handshake=[],
    )
    result = calculate(**inputs)
    assert [r["complete_received_seconds_exact"] for r in result["requests"]] == [
        "5",
        "11",
        "17",
        "23",
    ]
    assert [r["last_ack_seconds_exact"] for r in result["requests"]] == [
        "7",
        "13",
        "19",
        "25",
    ]
    (ROOT / "small-pending-ack-trace.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(dict(scenarios=len(rows), small_trace="passed")))


if __name__ == "__main__":
    main()
