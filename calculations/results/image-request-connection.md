# 图片请求的完整成片预算

文件bytes与所有阶段时间由输入声明；不执行文件编解码或模型。

## original

上传 30000000 bytes，成片 5000000 bytes。

| 阶段 | 秒（精确分数） |
| --- | ---: |
| input_preparation | 0 |
| extra_input_compression | 0 |
| connection | 1/5 |
| request_round_trip | 1/10 |
| upload | 12 |
| queue | 0 |
| input_decode | 0 |
| extra_input_decompression | 0 |
| model | 3/10 |
| final_image_encode | 0 |
| download | 2/5 |
| output_use | 0 |

完整成片：13 秒；复用连接：64/5 秒。预览时间未知。

## 条件与边界

- File bytes are explicit metadata, not derived from pixels or a VAE tensor. No RAW/JPEG codec executes.
- Same-quality authorization is a caller assertion, not a measured quality guarantee; a JPEG label alone does not establish RAW equivalence.
- All stages are serial. Server waits for the entire input; download follows final-image encoding. No chunk or preview overlap is assumed.
- request_rtt_seconds is one declared residual request/response propagation/control budget, excluding serialization and connection establishment. It is charged once; no RTT is added per stage.
- Times exclude anything not included in explicit stage inputs. Default zero terms are teaching assumptions, not measurements. Supplied-file metadata does not make service times measured.
- Complete-final-image delivery is the comparison endpoint. Preview time remains unknown; earlier preview cannot substitute for full-image completion.
- Local time, when given, must cover the same original-input to usable-final-image boundary and quality requirement.
- Connection reuse removes only the explicit connection term; request RTT remains. Local thresholds are for each displayed original connection state.

```json
{
  "calculation": "image-request-budget",
  "scenario": {
    "input_bytes": 30000000,
    "output_bytes": 5000000,
    "upload_bits_per_second": 20000000,
    "download_bits_per_second": 100000000,
    "preparation_seconds": "0",
    "connection_seconds": "1/5",
    "request_rtt_seconds": "1/10",
    "queue_seconds": "0",
    "input_decode_seconds": "0",
    "model_seconds": "3/10",
    "output_encode_seconds": "0",
    "output_use_seconds": "0",
    "local_seconds": null,
    "compression": null,
    "quality_contract": "same original information and same final-image requirement",
    "metadata_kind": "declared_teaching",
    "input_format": "RAW",
    "output_format": "JPEG"
  },
  "variants": [
    {
      "variant": "original",
      "transmitted_input_bytes": 30000000,
      "output_file_bytes": 5000000,
      "stages": [
        {
          "stage": "input_preparation",
          "start_seconds_exact": "0",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "0"
        },
        {
          "stage": "extra_input_compression",
          "start_seconds_exact": "0",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "0"
        },
        {
          "stage": "connection",
          "start_seconds_exact": "0",
          "duration_seconds_exact": "1/5",
          "end_seconds_exact": "1/5"
        },
        {
          "stage": "request_round_trip",
          "start_seconds_exact": "1/5",
          "duration_seconds_exact": "1/10",
          "end_seconds_exact": "3/10"
        },
        {
          "stage": "upload",
          "start_seconds_exact": "3/10",
          "duration_seconds_exact": "12",
          "end_seconds_exact": "123/10"
        },
        {
          "stage": "queue",
          "start_seconds_exact": "123/10",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "123/10"
        },
        {
          "stage": "input_decode",
          "start_seconds_exact": "123/10",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "123/10"
        },
        {
          "stage": "extra_input_decompression",
          "start_seconds_exact": "123/10",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "123/10"
        },
        {
          "stage": "model",
          "start_seconds_exact": "123/10",
          "duration_seconds_exact": "3/10",
          "end_seconds_exact": "63/5"
        },
        {
          "stage": "final_image_encode",
          "start_seconds_exact": "63/5",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "63/5"
        },
        {
          "stage": "download",
          "start_seconds_exact": "63/5",
          "duration_seconds_exact": "2/5",
          "end_seconds_exact": "13"
        },
        {
          "stage": "output_use",
          "start_seconds_exact": "13",
          "duration_seconds_exact": "0",
          "end_seconds_exact": "13"
        }
      ],
      "complete_final_image_seconds_exact": "13",
      "preview_ready_seconds": null,
      "reused_connection_final_seconds_exact": "64/5",
      "connection_reuse_saving_seconds_exact": "1/5",
      "local_comparison": {
        "local_complete_seconds_exact": null,
        "remote_strictly_faster": null,
        "upload_equal_time_bits_per_second_exact": null,
        "relation": "unknown_local_time"
      }
    }
  ],
  "compression_comparison": null,
  "scope": [
    "File bytes are explicit metadata, not derived from pixels or a VAE tensor. No RAW/JPEG codec executes.",
    "Same-quality authorization is a caller assertion, not a measured quality guarantee; a JPEG label alone does not establish RAW equivalence.",
    "All stages are serial. Server waits for the entire input; download follows final-image encoding. No chunk or preview overlap is assumed.",
    "request_rtt_seconds is one declared residual request/response propagation/control budget, excluding serialization and connection establishment. It is charged once; no RTT is added per stage.",
    "Times exclude anything not included in explicit stage inputs. Default zero terms are teaching assumptions, not measurements. Supplied-file metadata does not make service times measured.",
    "Complete-final-image delivery is the comparison endpoint. Preview time remains unknown; earlier preview cannot substitute for full-image completion.",
    "Local time, when given, must cover the same original-input to usable-final-image boundary and quality requirement.",
    "Connection reuse removes only the explicit connection term; request RTT remains. Local thresholds are for each displayed original connection state."
  ]
}
```
