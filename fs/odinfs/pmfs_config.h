/*
 * pmfs_config.h
 *
 *  Created on: Sep 2, 2021
 *      Author: dzhou
 */

#ifndef __PMFS_CONFIG_H_
#define __PMFS_CONFIG_H_

#define PMFS_DELEGATION_ENABLE 1
#define RANDOM_DELEGATION 0
#if RANDOM_DELEGATION
#pragma message "轮流选择委托和不委托"
#endif

#define PMFS_ADAPTIVE_FLUSH 1
#if PMFS_ADAPTIVE_FLUSH
#pragma message "自适应刷新"
#endif

#define PMFS_DELEGATE_HOT 1
#if PMFS_DELEGATE_HOT
#pragma message "只委托热数据"
#endif

#define PMFS_CAT 1
#if PMFS_CAT
#pragma message "启用CAT"
#endif

#define PMFS_HASH_RING 1
#if PMFS_HASH_RING
#pragma message "根据哈希选择委托线程"
#endif

#define PMFS_MAX_SOCKET 8
#define PMFS_MAX_AGENT_PER_SOCKET 28
#define PMFS_MAX_AGENT (PMFS_MAX_SOCKET * PMFS_MAX_AGENT_PER_SOCKET)

#define PMFS_DEBUG_MEM_ERROR 0

#define PMFS_RUN_IN_VM 0
#define PMFS_MEASURE_TIME 0

#define PMFS_AGENT_TASK_MAX_SIZE (8 + 1)

/*
 * Do cond_schuled()/kthread_should_stop() every 100ms when agents are serving
 * requests. The 3000 value is set with 32KB strip size where memcpy 32KB
 * takes around 70000 cycles. So (2.2*10^9) / 70000 = 3000
 */
#define PMFS_AGENT_REQUEST_CHECK_COUNT 3000

/*
 * Do cond_schuled()/kthread_should_stop() every 100ms when agents are spinning
 * on the ring buffer
 *
 * This assumes that one ring buffer acquire operation takes 100 cycles
 */

#define PMFS_AGENT_RING_BUFFER_CHECK_COUNT 220000

/*
 * Do cond_schuled()/kthread_should_stop() every 100ms when the application
 * threads are sending requests to the ring buffer
 *
 * This assumes that copying to the ring buffer takes around 100000 to complete
 *
 * The current ring buffer performance is unreasonable with 210+ application
 * threads, need to revise.
 */

#define PMFS_APP_RING_BUFFER_CHECK_COUNT 220

/*
 * Do cond_schuled() every 100ms when the application thread is waiting for
 * the delegation request to complete.
 */
#define PMFS_APP_CHECK_COUNT 220000000

#define PMFS_SOLROS_RING_BUFFER 1

/* write delegation limits: 256 */ // IMPORTANT: This is the limit for the number of writes that can be delegated to the agents
#define PMFS_WRITE_DELEGATION_LIMIT 256
// #pragma message "NO DELEGATION"

/* read delegation limits: 32K */
#define PMFS_READ_DELEGATION_LIMIT (32 * 1024)

/* Number of default delegation threads per socket */
#define PMFS_DEF_DELE_THREADS_PER_SOCKET 1

/* When set, use nt store to write to memory */
#define PMFS_NT_STORE 1 // We now use non-temporal stores to write to memory in delegation threads to avoid cache pollution

/* 2MB */
#define PMFS_RING_SIZE (2 * 1024 * 1024)

/*
 * Add this config to eliminate the effects of journaling when
 * study performance
 */
#define PMFS_ENABLE_JOURNAL  1

#define PMFS_FINE_GRAINED_LOCK 1

/* stock inode lock in the linux kernel */
#define PMFS_INODE_LOCK_STOCK        1
/* PCPU_RWSEM from the max paper */
#define PMFS_INODE_LOCK_MAX_PERCPU   2
/* stock per_cpu_rwsem in the  linux kernel */
#define PMFS_INODE_LOCK_PERCPU       3

#define PMFS_INODE_LOCK PMFS_INODE_LOCK_MAX_PERCPU

#define PMFS_ENABLE_RANGE_LOCK_KMEM_CACHE 1

#define PMFS_WRITE_WAIT_THRESHOLD 2097152L
#define PMFS_READ_WAIT_THRESHOLD 2097152L

#define PMFS_DELE_THREAD_BIND_TO_NUMA 0

#define PMFS_DELE_THREAD_SLEEP 1



#endif /* __PMFS_CONFIG_H_ */
