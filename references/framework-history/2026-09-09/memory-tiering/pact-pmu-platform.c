/* SPDX-License-Identifier: MIT */
/* Copyright (c) 2026 MoatLab, Virginia Tech. */

#include <stdio.h>
#include <cpuid.h>

#include "pmu-platform.h"
#include "pmu.h"
#include "error.h"

pmu_platform_t g_pmu_platform;

/* Skylake Xeon CHA-to-core mapping (CloudLab c220g5) */
static const int skx_cha_to_core_map[10] = {2, 3, 4, 5, 6, 7, 8, 9, 0, 1};
static const int skx_core_to_tid[10] = {0x00, 0x10, 0x20, 0x30, 0x40, 0x08, 0x18, 0x28, 0x38, 0x48};

/*
 * Sapphire/Emerald Rapids CHA-to-core mapping. Both uarchs share the same
 * server CHA design and TOR event encodings, so one descriptor covers both.
 * SPR (Xeon Gold 6430) exposes 32 uncore_cha devices, all usable. EMR (Xeon
 * Gold 6530) exposes 64 but only CHAs 0-31 return non-zero TOR counters; the
 * upper half reads zero and is filtered out during discovery (cha_offset >=
 * nr_cha_mapping in filter_active_chas).
 */
static const int emr_cha_to_core_map[32] = {0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  10,
                                            11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
                                            22, 23, 24, 25, 26, 27, 28, 29, 30, 31};
static const int emr_core_to_tid[32] = {
    0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70, 0x78,
    0x80, 0x88, 0x90, 0x98, 0xA0, 0xA8, 0xB0, 0xB8, 0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0, 0xF8};

/* TID goes into config1 (ORed with config1_base). */
static void generic_fill_tor_config(const pmu_platform_t *plat, tor_pe_config_t *out, int event_idx,
                                    int tier, int core_id)
{
    out->config = plat->tor_base[event_idx][tier];
    out->config1 = plat->config1_base[tier];
    out->config2 = 0;

    if (core_id >= 0 && core_id < plat->nr_cha_mapping) {
        out->config |= plat->tid_en_bit;
        out->config1 |= plat->core_to_tid[core_id];
    }
}

static pmu_platform_id_t detect_platform(void)
{
    unsigned int eax, ebx, ecx, edx;

    if (!__get_cpuid(1, &eax, &ebx, &ecx, &edx)) {
        return PMU_PLATFORM_UNKNOWN;
    }

    unsigned int family = (eax >> 8) & 0xF;
    unsigned int model = (eax >> 4) & 0xF;

    if (family == 0xF) {
        family += (eax >> 20) & 0xFF;
    }
    if (family == 6 || family == 0xF) {
        model += ((eax >> 16) & 0xF) << 4;
    }

    /* Family 6: Intel Core microarchitectures */
    if (family == 6) {
        switch (model) {
        case 0x55: /* Skylake-X / Cascade Lake */
            return PMU_PLATFORM_SKX;
        case 0x8F: /* Sapphire Rapids */
        case 0xCF: /* Emerald Rapids */
            return PMU_PLATFORM_EMR;
        }
    }

    return PMU_PLATFORM_UNKNOWN;
}

/* Per-platform descriptors. Built once at file scope; pmu_platform_init copies
 * the matching descriptor into the global g_pmu_platform. */
static const pmu_platform_t platform_skx = {
    .id = PMU_PLATFORM_SKX,
    .name = "Skylake-X",
    .event_llc_miss_local = 0x01d3,
    .event_llc_miss_remote = 0x02d3,
    .nr_cha_mapping = 10,
    .cha_to_core_map = skx_cha_to_core_map,
    .core_to_tid = skx_core_to_tid,
    .tor_base =
        {
            {0x2136, 0x2136},               /* [TOR_OCC][local], [TOR_OCC][remote] */
            {0x0100211fULL, 0x0100211fULL}, /* [TOR_CYC][local], [TOR_CYC][remote] */
        },
    .config1_base =
        {
            0x4043200000000ULL, /* tier 0 (local): DRD_LOC opcode << 32. */
            0x4043100000000ULL, /* tier 1 (remote): DRD_REM opcode << 32. */
        },
    .tid_en_bit = (1ULL << 19),
    .fill_tor_config = generic_fill_tor_config,
    .mlp_min = 1.0,
    .mlp_max = 16.0,
    .k_constant_dram = 238,
    .k_constant_cxl = 771,
};

/*
 * Sapphire/Emerald Rapids. Core DRD events are unchanged from SKX
 * (MEM_LOAD_L3_MISS_RETIRED.LOCAL/REMOTE_DRAM). The CHA TOR events move to
 * the SPR/EMR encoding: the opcode match (DRD, local vs remote) lives in the
 * extended umask (config bits 32-55) inside tor_base, so config1_base is 0,
 * and the TID-enable bit is config:16. tor_base and the DRD opcode-match ext
 * bits (0xc816fe local, 0xc8177e remote) were validated on real SPR (hds04)
 * and EMR (hds06) silicon against Intel perfmon; see the validation notes.
 *
 * NOTE: k_constant_dram / k_constant_cxl are still the SKX values pending
 * per-uarch latency calibration on SPR/EMR.
 */
static const pmu_platform_t platform_emr = {
    .id = PMU_PLATFORM_EMR,
    .name = "Sapphire/Emerald Rapids",
    .event_llc_miss_local = 0x01d3,
    .event_llc_miss_remote = 0x02d3,
    .nr_cha_mapping = 32,
    .cha_to_core_map = emr_cha_to_core_map,
    .core_to_tid = emr_core_to_tid,
    .tor_base =
        {
            /* [TOR_OCC][local], [TOR_OCC][remote] — DRD opcode in ext umask. */
            {0x00c816fe00000136ULL, 0x00c8177e00000136ULL},
            /* [TOR_CYC][local], [TOR_CYC][remote] — cycles with >=1 outstanding. */
            {0x00c816fe0100011fULL, 0x00c8177e0100011fULL},
        },
    .config1_base = {0, 0}, /* opcode is in config ext umask, not config1 */
    .tid_en_bit = (1ULL << 16),
    .fill_tor_config = generic_fill_tor_config,
    .mlp_min = 1.0,
    .mlp_max = 20.0,
    .k_constant_dram = 238,
    .k_constant_cxl = 771,
};

int pmu_platform_init(void)
{
    pmu_platform_id_t id = detect_platform();
    const pmu_platform_t *src;
    switch (id) {
    case PMU_PLATFORM_EMR:
        src = &platform_emr;
        break;
    case PMU_PLATFORM_SKX:
        src = &platform_skx;
        break;
    case PMU_PLATFORM_UNKNOWN:
    default:
        log_warning("pmu_platform_init", "Unknown CPU (falling back to SKX defaults)");
        src = &platform_skx;
        break;
    }
    g_pmu_platform = *src;
    if (id == PMU_PLATFORM_UNKNOWN) {
        g_pmu_platform.id = PMU_PLATFORM_UNKNOWN;
        g_pmu_platform.name = "Unknown (SKX fallback)";
    }

    printf("PMU platform detected: %s\n", g_pmu_platform.name);

    extern event_config_t core_event_configs[CORE_EVENT_COUNT];
    core_event_configs[CORE_EVENT_LLC_MISS_FAST] =
        (event_config_t){g_pmu_platform.event_llc_miss_local, "LLC_MISS_FAST"};
    core_event_configs[CORE_EVENT_LLC_MISS_SLOW] =
        (event_config_t){g_pmu_platform.event_llc_miss_remote, "LLC_MISS_SLOW"};

    return (id == PMU_PLATFORM_UNKNOWN) ? -1 : 0;
}
