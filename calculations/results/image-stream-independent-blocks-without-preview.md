# 图片分块依赖与独立交付点

模式：independent_blocks；完整成片 309/25 秒；预览 None 秒（None表示未声明）。
原图 30000000 bytes；成片 5000000 bytes；额外预览 0 bytes。

| 事件 | 资源 | 开始 s | 结束 s | 前置事件 |
| --- | --- | ---: | ---: | --- |
| prepare | client | 0 | 0 |  |
| connect | client | 0 | 0 | prepare |
| upload.0 | uplink | 0 | 4 | connect |
| input_arrival.0 | None | 4 | 81/20 | upload.0 |
| upload.1 | uplink | 4 | 8 | upload.0 |
| input_arrival.1 | None | 8 | 161/20 | upload.1 |
| upload.2 | uplink | 8 | 12 | upload.1 |
| input_arrival.2 | None | 12 | 241/20 | upload.2 |
| process.0 | server | 81/20 | 83/20 | input_arrival.0 |
| encode.0 | server | 83/20 | 83/20 | process.0 |
| process.1 | server | 161/20 | 163/20 | input_arrival.1, encode.0 |
| encode.1 | server | 163/20 | 163/20 | process.1 |
| process.2 | server | 241/20 | 243/20 | input_arrival.2, encode.1 |
| encode.2 | server | 243/20 | 243/20 | process.2 |
| download.final.0 | downlink | 83/20 | 423/100 | encode.0 |
| arrival.final.0 | None | 423/100 | 107/25 | download.final.0 |
| download.final.1 | downlink | 163/20 | 831/100 | encode.1, download.final.0 |
| arrival.final.1 | None | 831/100 | 209/25 | download.final.1 |
| download.final.2 | downlink | 243/20 | 1231/100 | encode.2, download.final.1 |
| arrival.final.2 | None | 1231/100 | 309/25 | download.final.2 |
| final_usable | client | 309/25 | 309/25 | arrival.final.0, arrival.final.1, arrival.final.2 |

- Given file-block bytes, not inferred RAW/JPEG sizes. No codec, model or network executes.
- Independent mode requires caller authorization that input, model and encoded output blocks preserve the same final quality without cross-block dependencies; this is not asserted for real RAW/JPEG editing.
- One serial uplink, one shared server for processing/encoding including preview, one serial downlink; these three resources may overlap. Fixed block order and non-preemptive FIFO downlink; no optimal scheduling claim.
- Forward/reverse propagation applies after each serialization and consumes no link capacity; packets can be in flight together. It is not repeatedly added to serialization resource occupancy. No separate RTT term exists.
- Whole-image mode adds all-input and all-final-encoding barriers while preserving identical per-block work/bytes. It is an explicitly declared barrier comparison, not a claim about actual monolithic runtime.
- Optional preview consumes processed prefix0..after_processed_chunk, extra encoding work and additional downlink bytes. Its quality requirement differs from final; preview never substitutes for complete final delivery.
- Final assembly starts only after every final block arrives. Times omit undeclared queueing, loss recovery, handshake RTTs, protocol overhead, flow control and codec global work. Connection cost must be supplied separately.

```json
{
  "calculation": "image-request-streaming",
  "scenario": {
    "chunks": [
      {
        "input_bytes": 10000000,
        "output_bytes": 1000000,
        "process_seconds": "1/10",
        "encode_seconds": "0",
        "required_inputs": [
          0
        ]
      },
      {
        "input_bytes": 10000000,
        "output_bytes": 2000000,
        "process_seconds": "1/10",
        "encode_seconds": "0",
        "required_inputs": [
          1
        ]
      },
      {
        "input_bytes": 10000000,
        "output_bytes": 2000000,
        "process_seconds": "1/10",
        "encode_seconds": "0",
        "required_inputs": [
          2
        ]
      }
    ],
    "mode": "independent_blocks",
    "independent_blocks_authorized": true,
    "quality_contract": "same original information and usable final-image quality",
    "upload_bits_per_second": 20000000,
    "download_bits_per_second": 100000000,
    "forward_propagation_seconds": "1/20",
    "reverse_propagation_seconds": "1/20",
    "preparation_seconds": "0",
    "connection_seconds": "0",
    "final_assembly_seconds": "0",
    "preview": null
  },
  "events": [
    {
      "id": "prepare",
      "resource": "client",
      "start_seconds_exact": "0",
      "duration_seconds_exact": "0",
      "end_seconds_exact": "0",
      "dependencies": []
    },
    {
      "id": "connect",
      "resource": "client",
      "start_seconds_exact": "0",
      "duration_seconds_exact": "0",
      "end_seconds_exact": "0",
      "dependencies": [
        "prepare"
      ]
    },
    {
      "id": "upload.0",
      "resource": "uplink",
      "start_seconds_exact": "0",
      "duration_seconds_exact": "4",
      "end_seconds_exact": "4",
      "dependencies": [
        "connect"
      ],
      "bytes": 10000000
    },
    {
      "id": "input_arrival.0",
      "resource": null,
      "start_seconds_exact": "4",
      "duration_seconds_exact": "1/20",
      "end_seconds_exact": "81/20",
      "dependencies": [
        "upload.0"
      ]
    },
    {
      "id": "upload.1",
      "resource": "uplink",
      "start_seconds_exact": "4",
      "duration_seconds_exact": "4",
      "end_seconds_exact": "8",
      "dependencies": [
        "upload.0"
      ],
      "bytes": 10000000
    },
    {
      "id": "input_arrival.1",
      "resource": null,
      "start_seconds_exact": "8",
      "duration_seconds_exact": "1/20",
      "end_seconds_exact": "161/20",
      "dependencies": [
        "upload.1"
      ]
    },
    {
      "id": "upload.2",
      "resource": "uplink",
      "start_seconds_exact": "8",
      "duration_seconds_exact": "4",
      "end_seconds_exact": "12",
      "dependencies": [
        "upload.1"
      ],
      "bytes": 10000000
    },
    {
      "id": "input_arrival.2",
      "resource": null,
      "start_seconds_exact": "12",
      "duration_seconds_exact": "1/20",
      "end_seconds_exact": "241/20",
      "dependencies": [
        "upload.2"
      ]
    },
    {
      "id": "process.0",
      "resource": "server",
      "start_seconds_exact": "81/20",
      "duration_seconds_exact": "1/10",
      "end_seconds_exact": "83/20",
      "dependencies": [
        "input_arrival.0"
      ]
    },
    {
      "id": "encode.0",
      "resource": "server",
      "start_seconds_exact": "83/20",
      "duration_seconds_exact": "0",
      "end_seconds_exact": "83/20",
      "dependencies": [
        "process.0"
      ]
    },
    {
      "id": "process.1",
      "resource": "server",
      "start_seconds_exact": "161/20",
      "duration_seconds_exact": "1/10",
      "end_seconds_exact": "163/20",
      "dependencies": [
        "input_arrival.1",
        "encode.0"
      ]
    },
    {
      "id": "encode.1",
      "resource": "server",
      "start_seconds_exact": "163/20",
      "duration_seconds_exact": "0",
      "end_seconds_exact": "163/20",
      "dependencies": [
        "process.1"
      ]
    },
    {
      "id": "process.2",
      "resource": "server",
      "start_seconds_exact": "241/20",
      "duration_seconds_exact": "1/10",
      "end_seconds_exact": "243/20",
      "dependencies": [
        "input_arrival.2",
        "encode.1"
      ]
    },
    {
      "id": "encode.2",
      "resource": "server",
      "start_seconds_exact": "243/20",
      "duration_seconds_exact": "0",
      "end_seconds_exact": "243/20",
      "dependencies": [
        "process.2"
      ]
    },
    {
      "id": "download.final.0",
      "resource": "downlink",
      "start_seconds_exact": "83/20",
      "duration_seconds_exact": "2/25",
      "end_seconds_exact": "423/100",
      "dependencies": [
        "encode.0"
      ],
      "bytes": 1000000
    },
    {
      "id": "arrival.final.0",
      "resource": null,
      "start_seconds_exact": "423/100",
      "duration_seconds_exact": "1/20",
      "end_seconds_exact": "107/25",
      "dependencies": [
        "download.final.0"
      ]
    },
    {
      "id": "download.final.1",
      "resource": "downlink",
      "start_seconds_exact": "163/20",
      "duration_seconds_exact": "4/25",
      "end_seconds_exact": "831/100",
      "dependencies": [
        "encode.1",
        "download.final.0"
      ],
      "bytes": 2000000
    },
    {
      "id": "arrival.final.1",
      "resource": null,
      "start_seconds_exact": "831/100",
      "duration_seconds_exact": "1/20",
      "end_seconds_exact": "209/25",
      "dependencies": [
        "download.final.1"
      ]
    },
    {
      "id": "download.final.2",
      "resource": "downlink",
      "start_seconds_exact": "243/20",
      "duration_seconds_exact": "4/25",
      "end_seconds_exact": "1231/100",
      "dependencies": [
        "encode.2",
        "download.final.1"
      ],
      "bytes": 2000000
    },
    {
      "id": "arrival.final.2",
      "resource": null,
      "start_seconds_exact": "1231/100",
      "duration_seconds_exact": "1/20",
      "end_seconds_exact": "309/25",
      "dependencies": [
        "download.final.2"
      ]
    },
    {
      "id": "final_usable",
      "resource": "client",
      "start_seconds_exact": "309/25",
      "duration_seconds_exact": "0",
      "end_seconds_exact": "309/25",
      "dependencies": [
        "arrival.final.0",
        "arrival.final.1",
        "arrival.final.2"
      ]
    }
  ],
  "summary": {
    "input_file_bytes": 30000000,
    "final_file_bytes": 5000000,
    "additional_preview_bytes": 0,
    "total_downlink_bytes": 5000000,
    "complete_final_image_seconds_exact": "309/25",
    "preview_ready_seconds_exact": null,
    "preview_is_complete_final_image": false,
    "measured_seconds": null
  },
  "scope": [
    "Given file-block bytes, not inferred RAW/JPEG sizes. No codec, model or network executes.",
    "Independent mode requires caller authorization that input, model and encoded output blocks preserve the same final quality without cross-block dependencies; this is not asserted for real RAW/JPEG editing.",
    "One serial uplink, one shared server for processing/encoding including preview, one serial downlink; these three resources may overlap. Fixed block order and non-preemptive FIFO downlink; no optimal scheduling claim.",
    "Forward/reverse propagation applies after each serialization and consumes no link capacity; packets can be in flight together. It is not repeatedly added to serialization resource occupancy. No separate RTT term exists.",
    "Whole-image mode adds all-input and all-final-encoding barriers while preserving identical per-block work/bytes. It is an explicitly declared barrier comparison, not a claim about actual monolithic runtime.",
    "Optional preview consumes processed prefix0..after_processed_chunk, extra encoding work and additional downlink bytes. Its quality requirement differs from final; preview never substitutes for complete final delivery.",
    "Final assembly starts only after every final block arrives. Times omit undeclared queueing, loss recovery, handshake RTTs, protocol overhead, flow control and codec global work. Connection cost must be supplied separately."
  ]
}
```
