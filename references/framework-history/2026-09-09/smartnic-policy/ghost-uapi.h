// Copyright 2021 Google LLC
//
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file or at
// https://developers.google.com/open-source/licenses/bsd

#ifndef _SCHED_GHOST_H_
#define _SCHED_GHOST_H_

#include <linux/ioctl.h>

#ifdef __KERNEL__
#include <linux/limits.h>
#else
#include <limits.h>
#include <sched.h>
#include <stdint.h>
#endif

// NOLINTBEGIN
// clang-format off

/*
 * The version of ghOSt. It is important that the kernel and the userspace
 * process are the same version as each other. Each successive version changes
 * values in this header file, assumptions about operations in the kernel, etc.
 */
#define GHOST_VERSION 84

/*
 * Define SCHED_GHOST via the ghost uapi unless it has already been defined
 * via the proper channels (i.e. the official <sched.h> uapi header file).
 */
#ifndef SCHED_GHOST
#define SCHED_GHOST		18
#endif

/*
 * This is userspace API so the usual suspects like __cacheline_aligned
 * will not work.
 *
 * TODO: these are architecture-specific.
 */
#define __ghost_cacheline_aligned	__attribute__((__aligned__(64)))
#define __ghost_page_aligned		__attribute__((__aligned__(4096)))

enum ghost_type {
	GHOST_AGENT,
	GHOST_TASK,
};

/*
 * Collateral for GHOST_CONFIG_QUEUE_WAKEUP op:
 * - kernel supports up to 'GHOST_MAX_WINFO' wakeup targets for a queue.
 * - 'prio' must be zero (intended to be a tiebreaker but not defined yet).
 */
#define GHOST_MAX_WINFO	2
struct ghost_agent_wakeup {
	int cpu;
	int prio;
};

/*
 * <type,arg> tuple decoding:
 * 'type' is GHOST_TASK	 -> 'arg' is <gtid>
 * 'type' is GHOST_AGENT -> 'arg' is <cpu>
 */
struct ghost_msg_src {
	enum ghost_type type;
	uint64_t arg;
};

/* GHOST_TIMERFD_SETTIME */
struct timerfd_ghost {
	int cpu;
	int flags;
	uint64_t type;
	uint64_t cookie;
};
#define TIMERFD_GHOST_ENABLED	(1 << 0)

struct ghost_sw_info {
	uint32_t id;		/* status_word region id */
	uint32_t index;		/* index into the status_word array */
};

struct ghost_ioc_sw_get_info {
	struct ghost_msg_src request;
	struct ghost_sw_info response;
};

struct ghost_ioc_create_queue {
	int elems;
	int node;
	int flags;
	uint64_t mapsize;
};

struct ghost_ioc_assoc_queue {
	int fd;
	struct ghost_msg_src src;
	uint32_t barrier;
	int flags;
};

struct ghost_ioc_set_default_queue {
	int fd;
};

struct ghost_ioc_config_queue_wakeup {
	int qfd;
	struct ghost_agent_wakeup *w;
	int ninfo;
	int flags;
};

struct ghost_ioc_get_cpu_time {
	int64_t gtid;
	uint64_t runtime;
};

struct ghost_ioc_commit_txn {
#ifdef __KERNEL__
	ulong *mask_ptr;
#else
	cpu_set_t *mask_ptr;
#endif
	uint32_t mask_len;
	int flags;
};

struct ghost_ioc_timerfd_settime {
	int timerfd;
	int flags;
#ifdef __KERNEL__
	struct __kernel_itimerspec *in_tmr;
	struct __kernel_itimerspec *out_tmr;
#else
	struct itimerspec *in_tmr;
	struct itimerspec *out_tmr;
#endif
	struct timerfd_ghost timerfd_ghost;
};

struct ghost_ioc_run {
	int64_t gtid;
	uint32_t agent_barrier;
	uint32_t task_barrier;
	int run_cpu;
	int run_flags;
};

#define GHOST_IOC_NULL			_IO('g', 0)
#define GHOST_IOC_SW_GET_INFO		_IOWR('g', 1, struct ghost_ioc_sw_get_info)
#define GHOST_IOC_SW_FREE		_IOW('g', 2, struct ghost_sw_info)
#define GHOST_IOC_CREATE_QUEUE		_IOWR('g', 3, struct ghost_ioc_create_queue)
#define GHOST_IOC_ASSOC_QUEUE		_IOW('g', 4, struct ghost_ioc_assoc_queue)
#define GHOST_IOC_SET_DEFAULT_QUEUE	_IOW('g', 5, struct ghost_ioc_set_default_queue)
#define GHOST_IOC_CONFIG_QUEUE_WAKEUP	_IOW('g', 6, struct ghost_ioc_config_queue_wakeup)
#define GHOST_IOC_GET_CPU_TIME		_IOWR('g', 7, struct ghost_ioc_get_cpu_time)
#define GHOST_IOC_COMMIT_TXN		_IOW('g', 8, struct ghost_ioc_commit_txn)
#define GHOST_IOC_SYNC_GROUP_TXN	_IOW('g', 9, struct ghost_ioc_commit_txn)
#define GHOST_IOC_TIMERFD_SETTIME	_IOWR('g', 10, struct ghost_ioc_timerfd_settime)
#define GHOST_IOC_RUN			_IOW('g', 11, struct ghost_ioc_run)

/*
 * Status word region APIs.
 */
struct ghost_sw_region_header {
	uint32_t version;	/* ABI version */
	uint32_t id;		/* region id */
	uint32_t numa_node;
	uint32_t start;		/* offset of the first status word */
	uint32_t capacity;	/* total status words in this region */
	uint32_t available;	/* free status words in this region */
} __ghost_cacheline_aligned;
#define GHOST_SW_REGION_VERSION	0

/*
 * Align status words up to the next power of two so we do not cross cache lines
 * unnecessarily.  At our current size, that is one cache line per status word,
 * and two status words per cache line.
 */
struct ghost_status_word {
	uint32_t barrier;
	uint32_t flags;
	uint64_t gtid;
	int64_t switch_time;	/* time at which task was context-switched onto CPU */
	uint64_t runtime;	/* total time spent on the CPU in nsecs */
} __attribute__((__aligned__(32)));

#define GHOST_SW_F_INUSE	(1U << 0)    /* status_word in use */
#define GHOST_SW_F_CANFREE	(1U << 1)    /* status_word can be freed */
#define GHOST_SW_F_ALLOCATED	(1U << 2)    /* status_word is allocated */

/* agent-specific status_word.flags */
#define GHOST_SW_CPU_AVAIL	(1U << 8)    /* CPU available hint */
#define GHOST_SW_BOOST_PRIO     (1U << 9)    /* agent with boosted prio */

/* task-specific status_word.flags */
#define GHOST_SW_TASK_ONCPU	(1U << 16)   /* task is oncpu */
#define GHOST_SW_TASK_RUNNABLE	(1U << 17)   /* task is runnable */
#define GHOST_SW_TASK_IS_AGENT  (1U << 18)
#define GHOST_SW_TASK_MSG_GATED (1U << 19)   /* all task msgs are gated until
                                              * status_word is freed by agent */

/*
 * Queue APIs.
 */
struct ghost_queue_header {
	uint32_t version;	/* ABI version */
	uint32_t start;		/* offset from the header to start of ring */
	uint32_t nelems;	/* power-of-2 size of ghost_ring.msgs[] */
} __ghost_cacheline_aligned;
#define GHOST_QUEUE_VERSION	0

struct ghost_msg {
	uint16_t type;		/* message type */
	uint16_t length;	/* length of this message including payload */
	uint32_t seqnum;	/* sequence number for this msg source */
	uint32_t payload[0];	/* variable length payload */
};

/*
 * Messages are grouped by type and each type can have up to 64 messages.
 * (the limit of 64 is arbitrary).
 */
#define _MSG_TASK_FIRST	64
#define _MSG_TASK_LAST	(_MSG_TASK_FIRST + 64 - 1)

#define _MSG_CPU_FIRST	128
#define _MSG_CPU_LAST	(_MSG_CPU_FIRST + 64 - 1)

/* ghost message types */
enum {
	/* misc msgs */
	MSG_NOP			= 0,

	/* task messages */
	MSG_TASK_DEAD		= _MSG_TASK_FIRST,
	MSG_TASK_BLOCKED,
	MSG_TASK_WAKEUP,
	MSG_TASK_NEW,
	MSG_TASK_PREEMPT,
	MSG_TASK_YIELD,
	MSG_TASK_DEPARTED,
	MSG_TASK_SWITCHTO,
	MSG_TASK_AFFINITY_CHANGED,
	MSG_TASK_ON_CPU,
	MSG_TASK_PRIORITY_CHANGED,
	MSG_TASK_LATCH_FAILURE,

	/* cpu messages */
	MSG_CPU_TICK		= _MSG_CPU_FIRST,
	MSG_CPU_TIMER_EXPIRED,
	MSG_CPU_NOT_IDLE,	/* requested via run_flags: NEED_CPU_NOT_IDLE */
	MSG_CPU_AVAILABLE,
	MSG_CPU_BUSY,
	MSG_CPU_AGENT_BLOCKED,
	MSG_CPU_AGENT_WAKEUP,
};

/* TODO: Move payload to header once all clients updated. */
struct ghost_msg_payload_task_new {
	uint64_t gtid;
	uint64_t parent_gtid;
	uint64_t runtime;	/* cumulative runtime in ns */
	uint16_t runnable;
	int nice;		/* task priority in nice value [-20, 19] */
	struct ghost_sw_info sw_info;
};

struct ghost_msg_payload_task_preempt {
	uint64_t gtid;
	uint64_t runtime;	/* cumulative runtime in ns */
	uint64_t cpu_seqnum;	/* cpu sequence number */
	uint64_t agent_data;
	int cpu;
	char from_switchto;
	char was_latched;
};

struct ghost_msg_payload_task_yield {
	uint64_t gtid;
	uint64_t runtime;	/* cumulative runtime in ns */
	uint64_t cpu_seqnum;
	uint64_t agent_data;
	int cpu;
	char from_switchto;
};

struct ghost_msg_payload_task_blocked {
	uint64_t gtid;
	uint64_t runtime;	/* cumulative runtime in ns */
	uint64_t cpu_seqnum;
	int cpu;
	char from_switchto;
};

struct ghost_msg_payload_task_dead {
	uint64_t gtid;
};

struct ghost_msg_payload_task_departed {
	uint64_t gtid;
	uint64_t cpu_seqnum;
	int cpu;
	char from_switchto;
	char was_current;
};

struct ghost_msg_payload_task_affinity_changed {
	uint64_t gtid;
};

struct ghost_msg_payload_task_priority_changed {
	uint64_t gtid;
	int nice;	/* task priority in nice value [-20, 19]. */
};

struct ghost_msg_payload_task_wakeup {
	uint64_t gtid;
	uint64_t agent_data;
	char deferrable;	/* bool: 0 or 1 */

	int last_ran_cpu;	/*
				 * CPU that task last ran on (may be different
				 * than where it was last scheduled by the
				 * agent due to switchto).
				 */

	int wake_up_cpu;	/*
				 * CPU where the task was woken up (this is
				 * typically where the task last ran but it
				 * may also be the waker's cpu).
				 */

	int waker_cpu;		/* CPU of the waker task */
};

struct ghost_msg_payload_task_switchto {
	uint64_t gtid;
	uint64_t runtime;	/* cumulative runtime in ns */
	uint64_t cpu_seqnum;
	int cpu;
};

struct ghost_msg_payload_task_on_cpu {
	uint64_t gtid;
	uint64_t commit_time;
	uint64_t cpu_seqnum;
	int cpu;
};

struct ghost_msg_payload_task_latch_failure {
	uint64_t gtid;
	int errno;
};

struct ghost_msg_payload_cpu_not_idle {
	int cpu;
	uint64_t next_gtid;
};

struct ghost_msg_payload_cpu_tick {
	int cpu;
};

struct ghost_msg_payload_timer {
	int cpu;
  uint64_t type;
	uint64_t cookie;
};

struct ghost_msg_payload_cpu_available {
	int cpu;
};

struct ghost_msg_payload_cpu_busy {
	int cpu;
};

struct ghost_msg_payload_agent_blocked {
	int cpu;
};

struct ghost_msg_payload_agent_wakeup {
	int cpu;
};

struct bpf_ghost_msg {
	union {
		struct ghost_msg_payload_task_dead	dead;
		struct ghost_msg_payload_task_blocked	blocked;
		struct ghost_msg_payload_task_wakeup	wakeup;
		struct ghost_msg_payload_task_new	newt;
		struct ghost_msg_payload_task_preempt	preempt;
		struct ghost_msg_payload_task_yield	yield;
		struct ghost_msg_payload_task_departed	departed;
		struct ghost_msg_payload_task_switchto	switchto;
		struct ghost_msg_payload_task_affinity_changed	affinity;
		struct ghost_msg_payload_task_priority_changed	priority;
		struct ghost_msg_payload_task_on_cpu	on_cpu;
		struct ghost_msg_payload_task_latch_failure	latch_failure;
		struct ghost_msg_payload_cpu_tick	cpu_tick;
		struct ghost_msg_payload_timer		timer;
		struct ghost_msg_payload_cpu_not_idle	cpu_not_idle;
		struct ghost_msg_payload_cpu_available	cpu_available;
		struct ghost_msg_payload_cpu_busy	cpu_busy;
		struct ghost_msg_payload_agent_blocked	agent_blocked;
		struct ghost_msg_payload_agent_wakeup	agent_wakeup;
	};
	uint16_t type;
	uint32_t seqnum;

	/*
	 * BPF can inform the kernel which cpu it would prefer to wake up
	 * in response to this message.
	 * -1 indicates no preference.
	 */
	int pref_cpu;
};

#ifdef __cplusplus
#include <atomic>
typedef std::atomic<uint32_t> _ghost_ring_index_t;
#else
typedef volatile uint32_t _ghost_ring_index_t;
#endif

struct ghost_ring {
	/*
	 * kernel produces at 'head & (nelems-1)' and
	 * agent consumes from 'tail & (nelems-1)'.
	 *
	 * kernel increments 'overflow' any time there aren't enough
	 * free slots to produce a message.
	 */
	_ghost_ring_index_t head;
	_ghost_ring_index_t tail;
	_ghost_ring_index_t overflow;
	struct ghost_msg msgs[0];  /* array of size 'header->nelems' */
};

#define GHOST_MAX_QUEUE_ELEMS	65536	/* arbitrary */

/*
 * 'ops' supported by gsys_ghost().
 */
enum ghost_ops {
	GHOST_GTID_LOOKUP,
};

/*
 * 'ops' supported by gsys_ghost() that are used by the 'base' library in
 * userspace. Arbitrary applications may use the 'base' library requiring
 * these 'ops' to be immutable (both in terms of the entry-point and the
 * functionality).
 *
 * The 'base' library can detect support for a particular op as follows:
 * - return value 0 indicates that the 'op' was successful.
 * - return value of -1 indicates that 'op' was not successful:
 *   - ENOSYS: kernel does not support ghost.
 *   - EOPNOTSUPP: kernel supports ghost but doesn't recognize this op.
 *     (for e.g. newer binary running on an older kernel).
 *   - any other errno indicates an op-specific error.
 */
enum ghost_base_ops {
	_GHOST_BASE_OP_FIRST = 65536,	/* avoid overlap with 'ghost_ops' */
	GHOST_BASE_GET_GTID = _GHOST_BASE_OP_FIRST,

	/*
	 * New ops must be added to the end of this enumeration.
	 */
};

/* status flags for GHOST_ASSOCIATE_QUEUE */
#define GHOST_ASSOC_SF_ALREADY		(1 << 0) /* Queue already set */
#define GHOST_ASSOC_SF_BRAND_NEW	(1 << 1) /* TASK_NEW not sent yet */

/* flags accepted by ghost_run() */
#define RTLA_ON_PREEMPT	  (1 << 0)  /* Return To Local Agent on preemption */
#define RTLA_ON_BLOCKED	  (1 << 1)  /* Return To Local Agent on block */
#define RTLA_ON_YIELD	  (1 << 2)  /* Return To Local Agent on yield */
#define RTLA_ON_IDLE	  (1 << 5)  /* Return To Local Agent on idle */
#define NEED_L1D_FLUSH	  (1 << 6)  /* Flush L1 dcache before entering guest */
#define NEED_CPU_NOT_IDLE (1 << 7)  /* Notify agent when a non-idle task is
				     * scheduled on the cpu.
				     */
#define ELIDE_PREEMPT     (1 << 9)  /* Do not send TASK_PREEMPT if we preempt
				     * a previous ghost task on this cpu
				     */
#define SEND_TASK_ON_CPU  (1 << 10) /* Send TASK_ON_CPU when on cpu */
/* After the task is latched, don't immediately preempt it if the cpu local
 * agent is picked to run; wait at least until the next sched tick hits
 * (assuming the agent is still running). This provides a good tradeoff between
 * avoiding spurious preemption and preventing an unbounded blackout for the
 * latched task while the agent is runnable.
 */
#define DEFER_LATCHED_PREEMPTION_BY_AGENT (1 << 11)
#define DO_NOT_PREEMPT	  (1 << 12) /* Do not preempt running tasks */

/* txn->commit_flags */
#define COMMIT_AT_SCHEDULE	(1 << 0) /* commit when oncpu task schedules */
#define COMMIT_AT_TXN_COMMIT	(1 << 1) /* commit in GHOST_COMMIT_TXN op */
#define ALLOW_TASK_ONCPU	(1 << 2) /* If task is running on a remote cpu
					  * then let continue running there.
					  */
#define ELIDE_AGENT_BARRIER_INC	(1 << 3) /* Do not increment the agent
					  * barrier (ie. on successfully
					  * latching the task).
					  */
#define INC_AGENT_BARRIER_ON_FAILURE	(1 << 4) /* Increment agent_barrier on
					  * transaction failure.
					  */

/* Union of all COMMIT_AT_XYZ flags */
#define COMMIT_AT_FLAGS		(COMMIT_AT_SCHEDULE | COMMIT_AT_TXN_COMMIT)

/* flags accepted by bpf_ghost_resched_cpu2 */
#define RESCHED_ANY_CLASS       (1 << 0) /* resched no matter what type of task is running */
#define RESCHED_GHOST_CLASS     (1 << 1) /* resched if the running task is a ghost task */
#define RESCHED_IDLE_CLASS      (1 << 2) /* resched if the running task is an idle task */
#define RESCHED_OTHER_CLASS     (1 << 3) /* resched if the running task is neither ghost nor idle */
#define SET_MUST_RESCHED        (1 << 4) /* set rq->ghost.must_resched as part of the resched */
#define WAKE_AGENT              (1 << 5) /* if we resched, also force the agent to wake */
#define GHOST_RESCHED_CPU_MAX   (1 << 6) /* Must be the last value here. */

/* special 'gtid' encodings that can be passed to ghost_run() */
#define GHOST_NULL_GTID		(0)
#define GHOST_AGENT_GTID	(-1)
#define GHOST_IDLE_GTID		(-2)

/* ghost transaction */

/*
 * (txn->state == GHOST_TXN_READY)		    transaction is ready
 * (txn->state >= 0 && txn->state < nr_cpu_ids)	    transaction is claimed
 * (txn->state < 0)				    transaction is committed
 */
enum ghost_txn_state {
	GHOST_TXN_COMPLETE		= INT_MIN,
	GHOST_TXN_ABORTED,
	GHOST_TXN_TARGET_ONCPU,
	GHOST_TXN_TARGET_STALE,
	GHOST_TXN_TARGET_NOT_FOUND,
	GHOST_TXN_TARGET_NOT_RUNNABLE,
	GHOST_TXN_AGENT_STALE,
	GHOST_TXN_CPU_OFFLINE,
	GHOST_TXN_CPU_UNAVAIL,
	GHOST_TXN_INVALID_FLAGS,
	GHOST_TXN_INVALID_TARGET,
	GHOST_TXN_NOT_PERMITTED,
	GHOST_TXN_INVALID_CPU,
	GHOST_TXN_NO_AGENT,
	GHOST_TXN_UNSUPPORTED_VERSION,
	GHOST_TXN_POISONED,

	/*
	 * Values [0-nr_cpu_ids) indicates that the transaction is claimed
	 * by the specific CPU.
	 */

	GHOST_TXN_READY			= INT_MAX,
};

/*
 * _ghost_txn_state_t is not expected to be used anywhere except as the type
 * of ghost_txn::state below. See cl/350179823 as an example of unintentional
 * consequences.
 */
#ifdef __cplusplus
#include <atomic>
typedef std::atomic<ghost_txn_state> _ghost_txn_state_t;
/*
 * To be safe, check that the size of '_ghost_txn_state_t' is equal to the size
 * of 'int32_t', which is the size that the kernel assumes the state is.
 */
static_assert(sizeof(_ghost_txn_state_t) == sizeof(int32_t));
typedef std::atomic<int32_t> _ghost_txn_owner_t;
#else
typedef int32_t _ghost_txn_state_t;
typedef int32_t _ghost_txn_owner_t;
#endif

struct ghost_txn {
	int32_t version;
	int32_t cpu;		/* readonly-after-init */
	_ghost_txn_state_t state;
	uint32_t agent_barrier;
	uint32_t task_barrier;
	uint16_t run_flags;
	uint8_t commit_flags;
	uint8_t unused;
	int64_t gtid;
	int64_t commit_time;	/* the time that the txn commit succeeded/failed */
	uint64_t cpu_seqnum;
	/*
	 * Context-dependent fields.
	 */
	union {
		/* only used during a sync-group commit */
		_ghost_txn_owner_t sync_group_owner;
	} u;
} __ghost_cacheline_aligned;

struct ghost_cpu_data {
	struct ghost_txn	txn;
} __ghost_page_aligned;

#define GHOST_TXN_VERSION	0

/* GHOST_GTID_LOOKUP */
enum {
	GHOST_GTID_LOOKUP_TGID,		/* return group_leader pid */
};

// clang-format on
// NOLINTEND

#endif	/* _SCHED_GHOST_H_ */
