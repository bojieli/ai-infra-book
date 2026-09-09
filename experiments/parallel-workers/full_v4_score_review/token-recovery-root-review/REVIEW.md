# Independent review: 11-4 token recovery

PASS within the documented two-task, local single-worker scope. No sealed experimental files were changed, and no model was loaded or inference started.

- Verified every sealed file: 297 SHA-256 hashes and sizes, total 5,338,435 bytes.
- Replayed the original analyzer in a temporary complete directory copy with the existing MLX environment, offline tokenizer only. Formal 6,778 checks and smoke 474 checks passed; both regenerated checks.json and summary.json were byte-identical to the sealed originals. Temporary copies were removed.
- Independently compared every formal SQLite snapshot row with its first nonduplicate commit event. Confirmed 12 paths, 20 workers, 3,256 actual sampled tokens, 3,000 unique committed positions, 256 duplicate deliveries, and 8 actual SIGKILL interruptions.
- Checked commit completion before kill, missing ACK at the cut, exactly K pre-kill generated records, old process termination before new process start, persisted high-water marks, and no recorded remaining process-group members. Reviewed EOS mapping/position and strict JSON quality logic, including duplicate-key rejection and integer types.
- Verified every README result-table row against the sealed summary. Independent raw-resource aggregation reproduces RSS 4,717,379,584 bytes, MLX active 4,521,207,816 bytes and MLX framework peak 4,874,725,488 bytes. Controller wall 121.10145583300618 s and all four reported prefix-rebuild times round to the documented values.
- Viewed recovery-work.png: both panels, axis labels, legend and limitation note are legible; bars reflect actual counts and timing, including sequence K96 preserve being slower than restart. SVG is included in the verified seal.

The corrected analyzer now connects DB rows to commit events, true EOS IDs, task-derived prompt IDs and worker identity, recovery sequence numbers and observed high-water marks. No remaining material correctness defect was found in these delivered paths.

Limits remain appropriate: these are two fixed tasks with paired baseline repeats, not 12 independent tasks; prefix recovery performs actual KV rebuild; conflicting duplicate payloads were not experimentally injected; the manager survives the interruption; no stable speedup, multi-host, random-sampling, cost, or numerical-generalization claim follows.
