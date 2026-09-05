# OpenURMA

An open-source FPGA implementation of UB's connectionless RDMA-class
transport, built as `.clnp` elements on top of [OpenClickNP].

OpenURMA implements the wire format and behaviour of the **transaction
layer** (BTAH/ATAH, 18 transaction opcodes, all four service modes
ROI/ROT/ROL/UNO, all three execution-order tags NO/RO/SO, application
Fence, and both completion-order modes) and the **transport layer** (RTP
with PSN/GoBackN, UTP for UNO mode, simplified CETPH echo) per
*UB-Base-Specification 2.0.1*. Above that, `libopenurma` exposes the
URMA verb surface from *UB-Software-Reference-Design-for-OS-2.0* §5.3.

The point of the artifact is to *defend three architectural pillars in
open silicon* — the chain of moves UB makes, where each enables the next
(the paper's Figure 1):

1. **Transport / Transaction split.** State scales as O(local Jetties)
   + O(remote endpoints), not their product. UB's TP Channel + Jetty
   model is the design point; OpenURMA puts it in synthesizable RTL.
   Bounding state is what lets the controller sit on-bus (pillar 2).
2. **Native load/store latency.** Because the NIC's working set fits in
   on-chip SRAM, the controller lives on the on-chip bus next to the CPU
   instead of behind PCIe — so a CPU load/store reaches remote memory
   directly (§8.3), collapsing the four PCIe traversals of an RDMA READ
   into a single on-chip-bus crossing. This is the headline result: a
   64-byte remote fetch in **≈500 ns vs 2236 ns** on the matched RoCE
   baseline (**4.47×**).
3. **Graded ordering.** OpenURMA implements the full §7.3 surface —
   four service modes × three execution tags × Fence × two completion
   modes — so applications can opt into precisely the consistency they
   need (it rides on the per-application counters pillar 1 provisions, so
   it costs nothing on operations that don't request gating).

**It runs the unmodified official openEuler UMDK stack.** OpenURMA is not
only RTL. The same `.clnp` design compiles to a cycle-accurate SystemC NIC
that the **stock openEuler UMDK software stack** — `liburma → uburma.ko →
ubcore.ko → openurma_ubcore.ko`, vendored unmodified under
[`integration/umdk/`](integration/umdk/) — drives end-to-end inside a
full-system **gem5** Linux guest. Real applications run against it: the
official `urma_perftest` (write/read/send/atomic × latency & bandwidth), the
URPC `umq` RPC framework, a KV store (up to 60 KB values), distributed atomic
counters, many-client concurrency and §7.3 ordering workloads, and a real
two-node setup (two gem5 guests over a cross-process wire) — across all three
transport modes (RM / RC / UM). By default the NIC's functional data plane
moves the bytes while the SystemC pipeline models cycle-accurate timing; opt
in with `OPENURMA_PIPE_DATA=1` and the real payload **physically traverses the
38-module SC pipeline** itself (MTU-segmented, data byte-verified by every
app). This validates OpenURMA against the *production* UB software stack, not
just synthetic harnesses — see
[`eval/results/IN_GUEST_SUMMARY.md`](eval/results/IN_GUEST_SUMMARY.md) and
[`integration/umdk/RESULTS.md`](integration/umdk/RESULTS.md).

New here? Start with [`docs/architecture.md`](docs/architecture.md) for a
guided tour of how a work-request flows through the element graph and how
the three pillars map onto specific elements. The full tech report (LaTeX
sources + built PDF) is in `paper/`; the research framing and evaluation
plan are in `RESEARCH_PLAN.md`.

A clean-room RoCEv2 RC reference lives **in-tree** under
`baselines/openroce/` and exists only to anchor the apples-to-apples
comparison — same OpenClickNP infrastructure, same FPGA target, only
the *protocol* differs. It is intentionally not packaged as a
standalone repo: the user-facing value of that code is the side-by-
side numbers, which only stay reproducible if both stacks live at the
same commit. See `EVAL.md` for the side-by-side numbers and
`eval/comparison.md` for the headline trade.

## Quick start

After cloning and building [OpenClickNP](#prerequisites) as a sibling:

```sh
./reproduce.sh doctor   # check toolchains (g++, OpenClickNP, SystemC, python)
./reproduce.sh smoke    # build + 17 SW-emu tests + verify headline claims (~2 min)
./reproduce.sh paper    # full dataset + every figure + rebuild the PDF (~15 min)
```

`smoke` builds the stack, runs the correctness suite, and checks the
paper's headline numbers (500 ns load/store, 2236 ns RoCE baseline, 4.47×,
4855× state reduction) against a freshly built simulator. See
`eval/twonode/README.md` for the full experiment → data → figure map.

## The three modeling tiers

OpenURMA realises the same protocol at three levels of fidelity, each
with a matched OpenRoCE baseline so every comparison is apples-to-apples:

| Tier | What it is | What it measures | Where |
|------|-----------|------------------|-------|
| **RTL** | `.clnp` elements compiled to Alveo U50 hardware via OpenClickNP | LUT/BRAM area, synthesizable behaviour | `elements/`, `scripts/synth_hls.sh`, `scripts/vivado_*.sh` |
| **SystemC two-node** | cycle-level simulator wiring two NICs across a link; four stacks (`ub_loadstore`, `ub_urma`, `roce_bf`, `roce_dma`) | end-to-end latency & throughput, state scaling, ordering | `eval/twonode/`, `build/twonode_sim` |
| **gem5 full-system** | two ARM CPUs boot Linux and run real user binaries (the unmodified official openEuler UMDK stack) against the SystemC NIC over TLM | software-path overhead with a real CPU + driver in the loop; optionally (`OPENURMA_PIPE_DATA=1`) the real payload also physically traverses the 38-module SC pipeline in-guest | `eval/twonode/gem5_scaffold/`, `eval/results/IN_GUEST_SUMMARY.md` |

The headline result: a 64-byte remote cache-line fetch — a LOAD on UB
§8.3, a READ on RoCEv2 RC — completes in **500 ns** end-to-end on the UB
load/store path versus **2236 ns** on the matched RoCE baseline (4.47×),
at ~14% of a U50's LUT budget. See [`EVAL.md`](EVAL.md) and [`paper/`](paper/).

## Documentation

A guided map of the docs (start at the top and follow what you need):

**Start here**
- [`docs/architecture.md`](docs/architecture.md) — guided tour: how a work-request
  flows through the element graph; how the three pillars map to elements.
- [`docs/wire_format.md`](docs/wire_format.md) — the on-wire BTAH/ATAH/RTP layout.
- [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md) — research framing, claims, and evaluation plan.

**Evaluation & results**
- [`EVAL.md`](EVAL.md) — how to reproduce every number; experiment → data → figure map.
- [`eval/comparison.md`](eval/comparison.md) — the headline UB-vs-RoCE trade.
- [`eval/results/APP_COVERAGE.md`](eval/results/APP_COVERAGE.md) — which official UMDK
  apps + workloads run, across all tiers.

**The three tiers** (see the table above)
- RTL — `elements/`, `scripts/synth_hls.sh`, `scripts/vivado_*.sh`.
- SystemC two-node (Tier S) — [`eval/twonode/README.md`](eval/twonode/README.md).
- gem5 full-system in-guest (Tier G) — [`eval/twonode/gem5_scaffold/README.md`](eval/twonode/gem5_scaffold/README.md).

**Official openEuler UMDK integration** (run the unmodified UMDK stack on the cycle-accurate sim)
- [`docs/architecture.md` §7](docs/architecture.md#7-official-openeuler-umdk-integration) —
  the integration design (provider seam, three tier backends, RC-over-connectionless mapping).
- [`integration/umdk/README.md`](integration/umdk/README.md) — folder guide: what's in
  `integration/umdk/` and how to build/run each tier.
- [`integration/umdk/RESULTS.md`](integration/umdk/RESULTS.md) — what works end-to-end + evidence.
- [`eval/results/IN_GUEST_SUMMARY.md`](eval/results/IN_GUEST_SUMMARY.md) — in-guest feature
  matrix, including the payload **physically traversing the 38-module SC pipeline**
  (`OPENURMA_PIPE_DATA`), with [`eval/results/gem5_sc_pipeline_datapath.md`](eval/results/gem5_sc_pipeline_datapath.md)
  as the engineering log.

The clean-room RoCEv2 baseline has its own docs under
[`baselines/openroce/`](baselines/openroce/README.md). The full tech report (LaTeX +
PDF) is in [`paper/`](paper/README.md).

## Prerequisites

OpenURMA is a set of OpenClickNP elements; it does **not** vendor its
toolchain. You need:

1. **OpenClickNP** — the FPGA-element compiler and runtime this builds
   on. Clone it as a sibling and build the compiler:

   ```sh
   git clone https://github.com/bojieli/OpenClickNP.git ~/OpenClickNP
   cd ~/OpenClickNP
   cmake -B build -DCMAKE_BUILD_TYPE=Release
   cmake --build build -j
   # produces build/compiler/openclicknp-cc
   ```

   All scripts default to `~/OpenClickNP`; override with the
   `OPENCLICKNP_ROOT` environment variable if you put it elsewhere.

2. **A Linux host with g++ ≥ 11** for the SW-emulator and SystemC tiers.

3. **SystemC 2.3.x** (for the two-node simulator and `tests/systemc/`).
   `scripts/build_libsc.sh` expects a SystemC install; point it at yours
   with `SYSTEMC_HOME` if it is not auto-detected.

4. *(RTL tier only)* AMD/Xilinx Vitis HLS + Vivado targeting Alveo U50.

5. *(gem5 tier only)* a built gem5 and an aarch64 cross-toolchain — see
   `eval/twonode/gem5_scaffold/README` / `PLAN.md`.

6. **UB specifications** — the protocol is implemented from
   *UB-Base-Specification 2.0.1* and *UB-Software-Reference-Design-for-OS
   2.0*. These Huawei PDFs are **not** redistributed in this repo (they
   are git-ignored). Place your own copies in the repo root if you want
   to cross-reference the `§`-section citations throughout the code.

## Layout

```
elements/protocols/ub/        UB protocol elements (.clnp, 41 elements
                              incl. UB_LoadStore_Engine for §8.3)
baselines/openroce/           RoCEv2 RC reference (19 elements)
examples/openurma/            Reference topology (URMA-async path)
examples/openurma_loadstore/  §8.3 Load/Store + TP Bypass topology variant
runtime/openurma/             libopenurma host-side library (URMA verbs)
                              + openurma::sc::NIC / openurma::ls::NIC facades
tests/swemu/                  SW-emulator integration tests
tests/systemc/                cycle-accurate microbenches + facade tests
eval/twonode/                 SystemC two-node end-to-end simulator
                              (libopenurma_sc + libopenurma_ls_sc +
                               libopenroce_sc, three NIC stacks compared)
eval/twonode/gem5_scaffold/   gem5 full-system tier: two ARM CPUs boot
                              Linux + uburma driver, run real binaries
                              against the SystemC NIC over TLM (see its
                              own README/PLAN.md)
scripts/                      build / test wrappers
docs/architecture.md          guided tour: element graph, dataflow, tiers
docs/wire_format.md           bit-level wire-format reference (spec citations)
```

## Reproducing the paper

```sh
# 1. Build the three SystemC NIC libraries.
bash scripts/build_libsc.sh                             # libopenurma_sc.a
OPENURMA_VARIANT=openurma_ls bash scripts/build_libsc.sh   # libopenurma_ls_sc.a
OPENURMA_VARIANT=openroce    bash scripts/build_libsc.sh   # libopenroce_sc.a

# 2. Build the two-node simulator.
bash eval/twonode/build_twonode.sh

# 3. Reproduce the headline 4.47x comparison: the same 64 B remote fetch
#    as a UB §8.3 LOAD vs a RoCEv2 RC READ (matched baseline).
build/twonode_sim --stack ub_loadstore --workload ptr_chase --verb load \
                  --n-ops 500 --link-delay-ns 100 --concurrency 1 \
                  --payload-bytes 64     # -> mean 500 ns
build/twonode_sim --stack roce_dma --workload ptr_chase --verb read \
                  --n-ops 500 --link-delay-ns 100 --concurrency 1 \
                  --payload-bytes 64     # -> mean 2236 ns  (4.47x)

# 4. Regenerate the ENTIRE two-node dataset + every paper figure (~10 min).
bash eval/twonode/reproduce_figures.sh

#    (or just the headline sweep + its figures)
bash eval/twonode/run_sweep.sh
python3 eval/twonode/plot_figs.py   # writes paper/figures/twonode_*.pdf

# 5. Rebuild the paper PDF.
cd paper && make            # pdflatex + bibtex + pdflatex x3
```

For a one-command build-test-reproduce from a clean checkout, use the
top-level driver instead: `./reproduce.sh smoke` (≈2 min: build + tests +
headline numbers) or `./reproduce.sh paper` (full dataset + figures + PDF).
Run `./reproduce.sh doctor` first to check prerequisites.

## Element inventory (41 elements, ~4.1 KLOC `.clnp`)

Header parsers / builders (Eth, NTH, RTPH, UTPH, BTAH):

| File | Role | Spec |
|------|------|------|
| `UB_Eth_Decap.clnp`  | wire → internal flit  | encapsulation MVP |
| `UB_Eth_Encap.clnp`  | internal flit → wire  | encapsulation MVP |
| `UB_NTH_Parse.clnp`  | route by NLP (RTP/UTP) | §5.2.2 |
| `UB_NTH_Build.clnp`  | stamp NTH on TX        | §5.2.2 |
| `UB_RTPH_Parse.clnp` | route data vs ACK      | §6.2.1 |
| `UB_RTPH_Build.clnp` | stamp RTPH on TX       | §6.2.1 |
| `UB_UTPH_Parse.clnp` | UTP path validation    | §6.2.1 |
| `UB_UTPH_Build.clnp` | stamp UTPH on TX       | §6.2.1 |
| `UB_BTAH_Parse.clnp` | route req vs response  | §7.2.1 |
| `UB_BTAH_Build.clnp` | finalize BTAH on TX    | §7.2.1 |

Transport layer:

| File | Role | Spec |
|------|------|------|
| `UB_TPChannel_TX.clnp`  | per-channel sender state, PSN/TPMSN allocator | §6.4.1 |
| `UB_TPChannel_RX.clnp`  | per-channel receiver, PSN window, ROL fusion  | §6.4.1, §7.3.3.4 |
| `UB_PSN_Reorder.clnp`   | OOO reassembly buffer (RTP path)              | §6.4.2.2.2 |
| `UB_Retrans_Buffer.clnp`| GoBackN in-flight buffer + RTO retransmit     | §6.4.2.2 |
| `UB_RTO_Timer.clnp`     | static-timeout retransmit trigger             | §6.4.2.1 |
| `UB_TPACK_Gen.clnp`     | TPACK/TPNAK builder (ROL fuses TAACK)         | §6.2.1 |
| `UB_TPSACK_Gen.clnp`    | selective-ACK bitmap builder (64-bit BitMap)  | §6.2.1 |
| `UB_TPG_Group.clnp`     | TP-group multi-channel load balancing         | §6.4.3 |
| `UB_Cong_Window.clnp`   | LDCP cw / inflight (advisory in MVP)          | §6.6 |
| `UB_Cong_Echo.clnp`     | CETPH echo + CNP gen (stubbed in MVP)         | §5.3.5, §6.2.2 |

Transaction layer:

| File | Role | Spec |
|------|------|------|
| `UB_Jetty_Sched.clnp`             | round-robin WR scheduler with Fence gating  | §8.2.3 + §7.3.2.2 |
| `UB_Txn_Dispatch.clnp`            | opcode-driven RX branch                     | §7.4 |
| `UB_Jetty_Recv.clnp`              | Send delivery to JFR                        | §7.4.3 |
| `UB_Completion_Gen.clnp`          | flip request → ATAH response                | §7.2.2 |
| `UB_Completion_Reorder.clnp`      | in-order vs OOO completion buffer           | §7.3.2.3 |
| `UB_OrderTracker_Initiator.clnp`  | ROI mode SO gating                          | §7.3.3.2 |
| `UB_OrderTracker_Target.clnp`     | ROT mode SO gating (TASSN scoreboard)       | §7.3.3.3 |
| `UB_TAACK_Gen.clnp`               | TAACK builder for ROI/ROT (bypassed in ROL) | §7.3.1.1 |
| `UB_Jetty_Group.clnp`             | Jetty-group fan-out / shared receive        | §8.2.2 |

State tables and memory:

| File | Role | Spec |
|------|------|------|
| `UB_MR_Table.clnp`       | segment lookup + token check        | §8.2.1, §8.2.4 |
| `UB_Jetty_Table.clnp`    | Jetty descriptor store               | §8.2.2 |
| `UB_TP_Table.clnp`       | per-channel state mirror             | §6.1 |
| `UB_HBM_Read.clnp`       | local memory read for Read txn       | §7.4.2.2 |
| `UB_HBM_Write.clnp`      | local memory write for Write txn     | §7.4.2.1 |
| `UBFPGA_HBM_Read.clnp`   | FPGA HBM read port (synthesis path)  | §7.4.2.2 |
| `UBFPGA_HBM_Write.clnp`  | FPGA HBM write port (synthesis path) | §7.4.2.1 |
| `UB_Atomic_CAS.clnp`     | 8-byte atomic CAS on local memory    | §7.4.2.3 |

Load/Store engine, multi-channel, and switch model:

| File | Role | Spec |
|------|------|------|
| `UB_LoadStore_Engine.clnp` | native CPU load/store → bus transaction (TP Bypass) | §8.3 |
| `UB_Switch_CAQM.clnp`      | in-line C-AQM switch model (no fabric in MVP)        | §5.3.5 |

Host I/O:

| File | Role |
|------|------|
| `UB_Doorbell.clnp`           | host-posted WR ingress |
| `UB_Completion_Stream.clnp`  | CQE egress to host_out |

## Wire format

OpenURMA wraps UB packets in standard Ethernet (UB Ethertype `0xCAFE`)
because it does not implement the UB physical/link layer. The
encapsulated bytes are exactly per spec:

```
ETH (14 B) | NTH 24-bit CNA (12 B) | RTPH (16 B) or UTPH (16 B)
          | BTAH full (16 B) | [ MAETAH (16 B) ] [ TVETAH (4 B) ]
          | [ MTETAH (4 B) ] [ Atomic operands (8 B) ] [ Payload ]
```

See `docs/wire_format.md` for bit-level layouts with spec section
references.

## Build & test

Prereqs: see [Prerequisites](#prerequisites) (OpenClickNP built, Linux,
g++ ≥ 11). All commands assume you run them from the repo root.

```sh
# Build the SW-emulator binary for the whole topology.
./scripts/build_swemu.sh

# Run the full SW-emu integration suite (17 tests).
./scripts/run_all_tests.sh
```

Expected output (all 17 print a `PASS` line):

```
=== test_atomic_full_opcode_set ===
PASS: full §7.4.2.3 atomic opcode set — Swap/Store/Load/FAA/FSUB/FAND/FOR/FXOR …
=== test_caqm_endtoend ===
PASS: switch marked FECN, sender backed off cw
=== test_completion_order ===
PASS: completion ordering modes (§7.3.2.3) — ODR[2]=1 reorders, ODR[2]=0 bypasses
=== test_fence ===
PASS: Fence gates Write behind outstanding Read (§7.3.2.2)
... (test_hbm_data_integrity, test_hol_blocking, test_jetty_group,
     test_mixed_modes, test_multi_flit_write, test_multi_ini_parallel,
     test_roi_ordering, test_rol_fused_ack, test_rot_ordering,
     test_roundtrip, test_throughput, test_tx_wire, test_uno) ...
```

A SystemC-level suite (cycle-accurate facade + TLM microbenches) also
lives under `tests/systemc/` and is exercised by the eval build.

The four most load-bearing conformance tests:

- **`test_tx_wire`** — drive a 2-flit Write WR through the entire TX
  pipeline; verify the resulting Ethernet frame contains a spec-
  compliant NTH (24-bit CNA, NLP=RTPH), RTPH (TPOpcode = Reliable TP
  Packet, valid PSN/TPMSN), BTAH (TAOpcode=Write, ODR=RO, INI_RC_ID),
  and MAETAH (Address, TokenID, Length).
- **`test_roundtrip`** — drive the same WR through TX → wire →
  Eth_Decap; verify all UB header fields survive the round trip,
  including the optional TVETAH (TokenValue).
- **`test_roi_ordering`** — Pillar 3 §7.3.3.2 conformance: in ROI mode,
  an SO transaction stays gated until prior RO transactions have
  signalled completion, while NO/RO transactions issue immediately.
- **`test_fence`** — Pillar 3 §7.3.2.2 conformance: a Fence-flagged WR
  blocks until prior Read/Atomic complete, while non-fenced WRs flow
  through.

## What's deliberately not in the MVP

Per `RESEARCH_PLAN.md` §1.3, the following are out of scope. (The list
has shrunk since the original plan — TPG, TP Bypass / Load-Store, the
full atomic suite, the TPSACK bitmap builder, and an in-line C-AQM
switch model have since landed; see the inventory above.)

- UB physical/link layer (we encapsulate in standard Ethernet,
  Ethertype `0xCAFE`)
- Full selective-retransmit: `UB_TPSACK_Gen` builds the 64-bit SACK
  bitmap, but the retransmit engine itself is still GoBackN
- Security partitions, virtualization, device management
- C-AQM *convergence on real hardware* — `UB_Switch_CAQM` models the
  marking behaviour in-line; no open UB switch fabric exists to run it

*Simulation-tier scope (not protocol cuts):* the gem5 in-guest
**pipeline-data** mode (`OPENURMA_PIPE_DATA`, see
[`eval/results/IN_GUEST_SUMMARY.md`](eval/results/IN_GUEST_SUMMARY.md)) routes
the real payload through the SC pipeline **in-order only** (no out-of-order
payload reassembly) and lets the **SimObject — not the pipeline — raise
completions** (so per-JFC completion routing stays in one place). These are
deliberate simplifications of the *simulation integration*, not of the
protocol; with the flag off, Tier G uses the functional data plane and the
results are identical.

What **is** in the MVP, with full coverage:

- All four service modes — **ROI, ROT, ROL, UNO**
- All three execution-order tags — **NO, RO, SO**
- Application **Fence**
- Both **completion-order modes** — in-order & out-of-order
- 18 transaction opcodes, including the full §7.4.2.3 atomic suite
  (CAS/Swap/Store/Load/FAA/FSUB/FAND/FOR/FXOR — all verified by
  `test_atomic_full_opcode_set`)
- §8.3 native **Load/Store** (TP Bypass) path via `UB_LoadStore_Engine`
- RTP with PSN window and GoBackN retransmit; UTP for UNO
- In-line **C-AQM** marking (FECN → cw back-off), end-to-end tested

Pillar 3's full §7.3 ordering surface is load-bearing for the paper —
it's all there.

## Citing OpenURMA

If you use OpenURMA in your research, please cite the tech report
([arXiv:2605.28717](https://arxiv.org/abs/2605.28717)):

```bibtex
@misc{li2026openurmacleanroomopenimplementation,
      title={OpenURMA: A Clean-Room Open Implementation of the Unified Bus Protocol},
      author={Bojie Li},
      year={2026},
      eprint={2605.28717},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.28717},
}
```

## License

Apache-2.0. See [`LICENSE`](LICENSE).

The two UB specification PDFs and the Ascend white paper that this work
is built from are Huawei copyright and are **not** redistributed here
(they are git-ignored); see [Prerequisites](#prerequisites) for where to
obtain them. The in-tree kernel driver under
`eval/twonode/gem5_scaffold/driver/` is GPL-2.0 (Linux module
requirement); the paper sources under `paper/` are CC-BY-4.0. Everything
else is Apache-2.0.

[OpenClickNP]: https://github.com/bojieli/OpenClickNP
