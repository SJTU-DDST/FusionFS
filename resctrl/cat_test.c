// SPDX-License-Identifier: GPL-2.0
/*
 * Cache Allocation Technology (CAT) test
 *
 * Copyright (C) 2018 Intel Corporation
 *
 * Authors:
 *    Sai Praneeth Prakhya <sai.praneeth.prakhya@intel.com>,
 *    Fenghua Yu <fenghua.yu@intel.com>
 */
#include "resctrl.h"
#include <unistd.h>
#include <time.h>

#include <sys/mman.h>
#include <pthread.h>
#include <pqos.h> // for cache pseudo_locking

#define RESULT_FILE_NAME	"result_cat"
#define NUM_OF_RUNS		100

#define REF 1
#define BOMB 1
#define BOMB_SPAN 100*1024*1024
#define MAX_BOMBS 128

/*
 * Minimum difference in LLC misses between a test with n+1 bits CBM to the
 * test with n bits is MIN_DIFF_PERCENT_PER_BIT * (n - 1). With e.g. 5 vs 4
 * bits in the CBM mask, the minimum difference must be at least
 * MIN_DIFF_PERCENT_PER_BIT * (4 - 1) = 3 percent.
 *
 * The relationship between number of used CBM bits and difference in LLC
 * misses is not expected to be linear. With a small number of bits, the
 * margin is smaller than with larger number of bits. For selftest purposes,
 * however, linear approach is enough because ultimately only pass/fail
 * decision has to be made and distinction between strong and stronger
 * signal is irrelevant.
 */
#define MIN_DIFF_PERCENT_PER_BIT	1UL

#if REF
static int show_results_info_ref(__u64 sum_llc_val, __u64 sum_llc_ref, int no_of_bits,
			     unsigned long cache_span,
			     unsigned long min_diff_percent,
			     unsigned long num_of_runs, bool platform,
			     __s64 *prev_avg_llc_val, __s64 *prev_avg_llc_ref, const struct user_params *uparams)
{
	__u64 avg_llc_val = 0, avg_llc_ref = 0;
	float avg_diff;
	int ret = 0;

	avg_llc_val = sum_llc_val / num_of_runs;
	avg_llc_ref = sum_llc_ref / num_of_runs;
	if (*prev_avg_llc_val && *prev_avg_llc_ref) {
		float delta = (__s64)(avg_llc_val - *prev_avg_llc_val);

		avg_diff = delta / *prev_avg_llc_val;

		if (no_of_bits) { // CAT enabled
			ret = platform && (avg_diff * 100) < (float)min_diff_percent;

			ksft_print_msg("%s Check cache miss rate changed more than %.1f%%\n",
					ret ? "Fail:" : "Pass:", (float)min_diff_percent);

			ksft_print_msg("Percent diff=%.1f\n", avg_diff * 100);
		}
	}
	*prev_avg_llc_val = avg_llc_val;
	*prev_avg_llc_ref = avg_llc_ref;

	show_cache_info_ref(no_of_bits, avg_llc_val, avg_llc_ref, cache_span, false, uparams);

	return ret;
}
#else
static int show_results_info(__u64 sum_llc_val, int no_of_bits,
			     unsigned long cache_span,
			     unsigned long min_diff_percent,
			     unsigned long num_of_runs, bool platform,
			     __s64 *prev_avg_llc_val)
{
	__u64 avg_llc_val = 0;
	float avg_diff;
	int ret = 0;

	avg_llc_val = sum_llc_val / num_of_runs;
	if (*prev_avg_llc_val) {
		float delta = (__s64)(avg_llc_val - *prev_avg_llc_val);

		avg_diff = delta / *prev_avg_llc_val;
		ret = platform && (avg_diff * 100) < (float)min_diff_percent;

		// print avg_llc_val, *prev_avg_llc_val, delta, avg_diff, min_diff_percent, ret
		// ksft_print_msg("Avg LLC misses=%llu, Prev avg LLC misses=%llu, Delta=%.1f, Avg diff=%.1f%%, Min diff=%.1f%%, Ret=%d\n",
		// 	       avg_llc_val, *prev_avg_llc_val, delta, avg_diff * 100,
		// 	       (float)min_diff_percent, ret);

		ksft_print_msg("%s Check cache miss rate changed more than %.1f%%\n",
			       ret ? "Fail:" : "Pass:", (float)min_diff_percent);

		ksft_print_msg("Percent diff=%.1f\n", avg_diff * 100);
	}
	*prev_avg_llc_val = avg_llc_val;

	show_cache_info(no_of_bits, avg_llc_val, cache_span, true);

	return ret;
}
#endif

/* Remove the highest bit from CBM */
static unsigned long next_mask(unsigned long current_mask)
{
	return current_mask & (current_mask >> 1);
}

static int check_results(struct resctrl_val_param *param, const char *cache_type,
			 unsigned long cache_total_size, unsigned long full_cache_mask,
			 unsigned long current_mask, const struct user_params *uparams)
{
	char *token_array[8], temp[512];
	__u64 sum_llc_perf_miss = 0;
	__s64 prev_avg_llc_val = 0;
	unsigned long alloc_size;
	int runs = 0;
	int fail = 0;
	int ret;
	FILE *fp;
#if REF
	__u64 sum_llc_perf_ref = 0;
	__s64 prev_avg_llc_ref = 0;
#endif

	ksft_print_msg("Checking for pass/fail\n");
	fp = fopen(param->filename, "r");
	if (!fp) {
		ksft_perror("Cannot open file");

		return -1;
	}

	while (fgets(temp, sizeof(temp), fp)) { // temp: Pid: 1568791     llc_value: 520946
		char *token = strtok(temp, ":\t");
		int fields = 0;
		int bits;

		// print runs & temp
		while (token) {
			token_array[fields++] = token;
			token = strtok(NULL, ":\t");
			// ksft_print_msg("Runs: %d, token: %s\n", runs, token);
		}

		sum_llc_perf_miss += strtoull(token_array[3], NULL, 0);
#if REF
		sum_llc_perf_ref += strtoull(token_array[5], NULL, 0);
#endif
		runs++;
		
		// print runs, sum_llc_perf_miss, token_array[3]
		// ksft_print_msg("Runs: %d, Sum LLC perf miss: %llu, Token array[3]: %s\n", runs, sum_llc_perf_miss, token_array[3]);
		// print each str in token_array
		// for (int i = 0; i < fields; i++) {
		// 	ksft_print_msg("Token array[%d]: %s\n", i, token_array[i]);
		// }

		// if (runs < NUM_OF_RUNS) // instead of measuring NUM_OF_RUNS times, we measure the whole test
		// 	continue;

		if (!current_mask) {
			ksft_print_msg("Unexpected empty cache mask, no CAT?\n");
			// break;
		}

		alloc_size = cache_portion_size(cache_total_size, current_mask, full_cache_mask);
		if (uparams->preset == SET_CONTENTION && uparams->half_alloc_size)
			alloc_size = cache_portion_size(cache_total_size, uparams->fixed_cat_mask, full_cache_mask) - alloc_size / 2;
		if (uparams->preset == DRAM_ENLARGE_WSS && uparams->half_alloc_size)
			alloc_size /= 2;

		bits = count_bits(current_mask);
#if REF
		ret = show_results_info_ref(sum_llc_perf_miss, sum_llc_perf_ref, bits,
					alloc_size, // bytes
					MIN_DIFF_PERCENT_PER_BIT * (bits - 1),
					runs, get_vendor() == ARCH_INTEL,
					&prev_avg_llc_val, &prev_avg_llc_ref, uparams);
#else
		ret = show_results_info(sum_llc_perf_miss, bits,
					alloc_size / 64,
					MIN_DIFF_PERCENT_PER_BIT * (bits - 1),
					runs, get_vendor() == ARCH_INTEL,
					&prev_avg_llc_val);
#endif
		if (ret)
			fail = 1;

		runs = 0;
		sum_llc_perf_miss = 0;
#if REF
		sum_llc_perf_ref = 0;
#endif
		current_mask = next_mask(current_mask);
	}

	fclose(fp);

	return fail;
}

void cat_test_cleanup(void)
{
	remove(RESULT_FILE_NAME);
}

#if BOMB
pid_t bomb_pids[MAX_BOMBS], delegate_pid;
volatile sig_atomic_t should_stop = 0;

void bomb_stop() {
	should_stop = 1;
}

void delegate_function(size_t span)
{
	int pm_fd, counter = 0;
	unsigned char *bomb_buf = alloc_pm_buffer(span, 1, &pm_fd);

	printf("Delegate pid: %d, CPU: %d\n", getpid(), sched_getcpu());

	signal(SIGTERM, bomb_stop);
	ksft_print_msg("Delegate pid: %d, bomb_buf: %p, span=%lu, should_stop=%d\n", getpid(), bomb_buf, span,should_stop);
	if (!bomb_buf) {
		ksft_print_msg("Delegate alloc PM buffer failed\n");
		goto free_buf;
	}
	mem_flush(bomb_buf, span);
	fill_cache_read(bomb_buf, span, true);
	time_t start_time = time(NULL);
	while (!should_stop) {
		fill_cache_write(bomb_buf, span, true, false);
		// usleep(100);
		counter++;
		time_t current_time = time(NULL);
		if (current_time - start_time >= 5) {
			break;
		}
	}
	printf("Delegate pid: %d scanned %d times, sleeping\n", getpid(), counter);
	// sleep(30);

	while (!should_stop) {
		fill_cache_write(bomb_buf, span, true, false);
		// sleep(1);
	}

free_buf:
	munmap(bomb_buf, span);
	close(pm_fd);
}

void bomb_function()
{
	unsigned char *bomb_buf = alloc_buffer(BOMB_SPAN, 1);
	// printf("Bomb pid: %d, CPU: %d\n", getpid(), sched_getcpu());

	signal(SIGTERM, bomb_stop);
	// ksft_print_msg("Bomb pid: %d, bomb_buf: %p\n", getpid(), bomb_buf);
	if (!bomb_buf) {
		ksft_print_msg("alloc buffer failed\n");
		goto free_buf;
	}

	mem_flush(bomb_buf, BOMB_SPAN);
	fill_cache_read(bomb_buf, BOMB_SPAN, true);

	while (!should_stop) {
		fill_cache_write(bomb_buf, BOMB_SPAN, true, false);
	}
    
free_buf:
	if (bomb_buf)
		free(bomb_buf);

	// ksft_print_msg("Bomb pid: %d, bomb_buf: %p is freed, exiting...\n", getpid(), bomb_buf);
}

void bomb_thread_function(unsigned char *bomb_buf)
{
	ksft_print_msg("PID=%d running bomb_thread_function\n", getpid());
	mem_flush(bomb_buf, BOMB_SPAN);
	fill_cache_read(bomb_buf, BOMB_SPAN, true);

	while (!should_stop) {
		fill_cache_write(bomb_buf, BOMB_SPAN, true, false);
		pthread_testcancel();
	}
}
#endif

#define MAX_L3CAT_NUM 16
#define DIM(x)        (sizeof(x) / sizeof(x[0]))

static int m_is_chunk_allocated = 0;
static char *m_chunk_start = NULL;
static size_t m_chunk_size = 0;
static unsigned m_num_clos = 0;
static struct {
	unsigned id;
	struct pqos_l3ca *cos_tab;
} m_l3cat_cos[MAX_L3CAT_NUM];

static void
mem_read(const void *p, const size_t s)
{
    register size_t i;

    if (p == NULL || s <= 0)
        return;

    for (i = 0; i < (s / sizeof(uint32_t)); i++) {
        asm volatile("xor (%0,%1,4), %%eax\n\t"
                     :
                     : "r"(p), "r"(i)
                     : "%eax", "memory");
    }

    for (i = s & (~(sizeof(uint32_t) - 1)); i < s; i++) {
        asm volatile("xorb (%0,%1,1), %%al\n\t"
                     :
                     : "r"(p), "r"(i)
                     : "%al", "memory");
    }
}

/**
 * @brief Calculates number of cache ways required to fit a number of \a bytes
 *
 * @param cat_cap pointer to L3CA PQoS capability structure
 * @param bytes number of bytes
 * @param ways pointer to store number of required cache ways
 *
 * @return Operation status
 * @retval 0 OK
 * @retval <0 error
 */
static int
bytes_to_cache_ways(const struct pqos_capability *cat_cap,
		    const size_t bytes,
		    size_t *ways)
{
	size_t llc_size = 0, num_ways = 0;
	const struct pqos_cap_l3ca *cat = NULL;

	if (cat_cap == NULL || ways == NULL)
		return -1;

	if (cat_cap->type != PQOS_CAP_TYPE_L3CA)
		return -2;

	cat = cat_cap->u.l3ca;
	llc_size = cat->way_size * cat->num_ways;
	if (bytes > llc_size)
		return -3;

	num_ways = (bytes + cat->way_size - 1) / cat->way_size;
	if (num_ways >= cat->num_ways)
		return -4;

	if (num_ways < 2)
		num_ways = 2;

	*ways = num_ways;
	return 0;
}

/**
 * @brief Initializes the memory block with random data
 *
 * This is to avoid any page faults or copy-on-write exceptions later on.
 *
 * @param p pointer to memory block
 * @param s size of memory block in bytes
 */
static void
mem_init(void *p, const size_t s)
{
	char *cp = (char *)p;
	size_t i;

	if (p == NULL || s <= 0)
		return;

	for (i = 0; i < s; i++)
		cp[i] = (char)rand();
}

int
dlock_init(void *ptr, const size_t size, const int clos, const int cpuid)
{
	const struct pqos_cpuinfo *p_cpu = NULL;
	const struct pqos_cap *p_cap = NULL;
	const struct pqos_capability *p_l3ca_cap = NULL;
	unsigned *l3cat_ids = NULL;
	unsigned l3cat_id_count = 0, i = 0;
	int ret = 0, res = 0;
	size_t num_cache_ways = 0;
	unsigned clos_save = 0;
	char err_buf[64];

#ifdef __linux__
	cpu_set_t cpuset_save, cpuset;
#endif
#ifdef __FreeBSD__
	cpuset_t cpuset_save, cpuset;
#endif

	// print num_cache_ways

	if (m_chunk_start != NULL)
		return -1;

	if (size <= 0)
		return -2;

	if (ptr != NULL) {
		m_chunk_start = ptr;
		m_is_chunk_allocated = 0;
	} else {
		printf("ptr is NULL\n");
		/**
		 * For best results allocated memory should be physically
		 * contiguous. Yet this would require allocating memory in
		 * kernel space or using huge pages.
		 * Let's use malloc() and 4K pages for simplicity.
		 */
		m_chunk_start = malloc(size);
		if (m_chunk_start == NULL)
			return -3;
		m_is_chunk_allocated = 1;
		mem_init(m_chunk_start, size);
	}
	m_chunk_size = size;

	/**
	 * Get task affinity to restore it later
	 */
#ifdef __linux__
	res = sched_getaffinity(0, sizeof(cpuset_save), &cpuset_save);
#endif
#ifdef __FreeBSD__
	res = cpuset_getaffinity(CPU_LEVEL_WHICH, CPU_WHICH_TID, -1,
				 sizeof(cpuset_save), &cpuset_save);
#endif
	if (res != 0) {
		printf("sched_getaffinity() error!\n");

		snprintf(err_buf, sizeof(err_buf), "%s() error", __func__);
		perror(err_buf);
		ret = -4;
		goto dlock_init_error1;
	}

	/**
	 * Set task affinity to cpuid for data locking phase
	 */
	CPU_ZERO(&cpuset);
	CPU_SET(cpuid, &cpuset);
#ifdef __linux__
	res = sched_setaffinity(0, sizeof(cpuset), &cpuset);
#endif
#ifdef __FreeBSD__
	res = cpuset_setaffinity(CPU_LEVEL_WHICH, CPU_WHICH_TID, -1,
				 sizeof(cpuset), &cpuset);
#endif
	if (res != 0) {
		printf("sched_setaffinity() error!\n");
		snprintf(err_buf, sizeof(err_buf), "%s() error", __func__);
		perror(err_buf);
		ret = -4;
		goto dlock_init_error1;
	}

	/**
	 * Clear table for restoring CAT configuration 函数接着清除用于恢复 CAT（Cache Allocation Technology）配置的表格，并获取 CPU 的拓扑结构和 PQoS（Platform Quality of Service）能力。
	 */
	for (i = 0; i < DIM(m_l3cat_cos); i++) {
		m_l3cat_cos[i].id = 0;
		m_l3cat_cos[i].cos_tab = NULL;
	}

	/**
	 * Retrieve CPU topology and PQoS capabilities
	 */
	res = pqos_cap_get(&p_cap, &p_cpu);
	if (res != PQOS_RETVAL_OK) {
		printf("pqos_cap_get() error!\n");
		ret = -5;
		goto dlock_init_error2;
	}

	/**
	 * Retrieve list of CPU l3cat_ids 接下来，函数遍历所有的 l3cat_ids，并获取当前的 CAT 类别。它保存这些类别以便稍后恢复，并修改这些类别，使得如果类别 id 等于 clos，那么该类别将独占访问 num_cache_ways，否则，该类别将被排除在 num_cache_ways 的访问之外。
	 */
	l3cat_ids = pqos_cpu_get_l3cat_ids(p_cpu, &l3cat_id_count);
	if (l3cat_ids == NULL) {
		printf("pqos_cpu_get_l3cat_ids() error!\n");
		ret = -6;
		goto dlock_init_error2;
	}

	/**
	 * Get CAT capability structure 并获取当前的 CAT 类别。它保存这些类别以便稍后恢复
	 */
	res = pqos_cap_get_type(p_cap, PQOS_CAP_TYPE_L3CA, &p_l3ca_cap);
	if (res != PQOS_RETVAL_OK) {
		printf("pqos_cap_get_type() error!\n");
		ret = -7;
		goto dlock_init_error2;
	}

	/**
	 * Compute number of cache ways required for the data
	 */
	res = bytes_to_cache_ways(p_l3ca_cap, size, &num_cache_ways);
	if (res != 0) {
		printf("bytes_to_cache_ways() error!\n");
		ret = -8;
		goto dlock_init_error2;
	}
	// print ptr, size, num_cache_ways, clos, cpuid
	// printf("dlock_init: ptr=%p, size=%lu, num_cache_ways=%lu, clos=%d, cpuid=%d\n", ptr, size, num_cache_ways, clos, cpuid);

	/**
	 * Compute class bit mask for data lock and
	 * retrieve number of classes of service
	 */
	m_num_clos = p_l3ca_cap->u.l3ca->num_classes;

	for (i = 0; i < l3cat_id_count; i++) {
		/**
		 * This would be enough to run the below code for the l3cat_id
		 * corresponding to \a cpuid. Yet it is safer to keep CLOS
		 * definitions coherent across l3cat_ids.
		 */
		const uint64_t dlock_mask = (1ULL << num_cache_ways) - 1ULL;

		// ASSERT(m_num_clos > 0);
		if (m_num_clos <= 0)
			printf("Number of classes of service error!\n");
		struct pqos_l3ca cos[m_num_clos];
		unsigned num = 0, j;

		/* get current CAT classes on this l3cat_ids */
		res = pqos_l3ca_get(l3cat_ids[i], m_num_clos, &num, &cos[0]);
		if (res != PQOS_RETVAL_OK) {
			printf("pqos_l3ca_get() error!\n");
			ret = -9;
			goto dlock_init_error2;
		}

		/* paranoia check */
		if (m_num_clos != num) {
			printf("CLOS number mismatch!\n");
			ret = -9;
			goto dlock_init_error2;
		}

		/* save CAT classes to restore it later */
		m_l3cat_cos[i].id = l3cat_ids[i];
		m_l3cat_cos[i].cos_tab = malloc(m_num_clos * sizeof(cos[0]));
		if (m_l3cat_cos[i].cos_tab == NULL) {
			printf("malloc() error!\n");
			ret = -9;
			goto dlock_init_error2;
		}
		memcpy(m_l3cat_cos[i].cos_tab, cos,
		       m_num_clos * sizeof(cos[0]));

		/**
		 * Modify the classes in the following way:
		 * if class_id == clos then
		 *   set class mask so that it has exclusive access to
		 *   \a num_cache_ways
		 * else
		 *   exclude class from accessing \a num_cache_ways
		 */
		for (j = 0; j < m_num_clos; j++) {
			if (cos[j].cdp) {
				if (cos[j].class_id == (unsigned)clos) {
					cos[j].u.s.code_mask = dlock_mask;
					cos[j].u.s.data_mask = dlock_mask;
				} else {
					cos[j].u.s.code_mask &= ~dlock_mask;
					cos[j].u.s.data_mask &= ~dlock_mask;
				}
			} else {
				if (cos[j].class_id == (unsigned)clos)
					cos[j].u.ways_mask = dlock_mask;
				else
					cos[j].u.ways_mask &= ~dlock_mask;
			}
		}

		res = pqos_l3ca_set(l3cat_ids[i], m_num_clos, &cos[0]);
		if (res != PQOS_RETVAL_OK) {
			printf("pqos_l3ca_set() error!\n");
			ret = -10;
			goto dlock_init_error2;
		}
	}

	/**
	 * Read current cpuid CLOS association and set the new one 函数接着读取当前 cpuid 的 CLOS 关联，并设置新的关联。然后，它从缓存层次结构中移除缓冲区数据，并将其读回到选定的缓存方式中。
	 */
	res = pqos_alloc_assoc_get(cpuid, &clos_save);
	if (res != PQOS_RETVAL_OK) {
		printf("pqos_alloc_assoc_get() error!\n");
		ret = -11;
		goto dlock_init_error2;
	}
	res = pqos_alloc_assoc_set(cpuid, clos);
	if (res != PQOS_RETVAL_OK) {
		printf("pqos_alloc_assoc_set() error!\n");
		ret = -12;
		goto dlock_init_error2;
	}

	/**
	 * Remove buffer data from cache hierarchy and read it back into
	 * selected cache ways.
	 * WBINVD is another option to remove data from cache but it is
	 * privileged instruction and as such has to be done in kernel space.
	 */
	mem_flush((unsigned char *) m_chunk_start, m_chunk_size);

	/**
	 * Read the data couple of times. This may help as this is ran in
	 * user space and code can be interrupted and data removed
	 * from cache hierarchy.
	 * Ideally all locking should be done at privileged level with
	 * full system control.
	 */
	for (i = 0; i < 10; i++)
		mem_read(m_chunk_start, m_chunk_size);

	/**
	 * Restore cpuid clos association
	 */
	res = pqos_alloc_assoc_set(cpuid, clos_save);
	if (res != PQOS_RETVAL_OK) {
		printf("pqos_alloc_assoc_set() error (revert)!\n");
		ret = -13;
		goto dlock_init_error2;
	}

dlock_init_error2:
	for (i = 0; (i < DIM(m_l3cat_cos)) && (ret != 0); i++)
		if (m_l3cat_cos[i].cos_tab != NULL)
			free(m_l3cat_cos[i].cos_tab);

#ifdef __linux__
	res = sched_setaffinity(0, sizeof(cpuset_save), &cpuset_save);
#endif
#ifdef __FreeBSD__
	res = cpuset_setaffinity(CPU_LEVEL_WHICH, CPU_WHICH_TID, -1,
				 sizeof(cpuset_save), &cpuset_save);
#endif
	if (res != 0) {
		printf("sched_setaffinity() error!\n");
		snprintf(err_buf, sizeof(err_buf),
			 "%s() error restoring affinity", __func__);
		perror(err_buf);
	}

dlock_init_error1:
	if (m_is_chunk_allocated && ret != 0)
		free(m_chunk_start);

	if (ret != 0) {
		printf("dlock_init() error, ret=%d\n", ret);
		m_chunk_start = NULL;
		m_chunk_size = 0;
		m_is_chunk_allocated = 0;
	}

	if (l3cat_ids != NULL)
		free(l3cat_ids);

	return ret;
}

int
dlock_exit(void)
{
	int ret = 0;
	unsigned i;

	if (m_chunk_start == NULL)
		return -1;

	for (i = 0; i < DIM(m_l3cat_cos); i++) {
		if (m_l3cat_cos[i].cos_tab != NULL) {
			int res = pqos_l3ca_set(m_l3cat_cos[i].id, m_num_clos,
						m_l3cat_cos[i].cos_tab);

			if (res != PQOS_RETVAL_OK)
				ret = -2;
		}
		free(m_l3cat_cos[i].cos_tab);
		m_l3cat_cos[i].cos_tab = NULL;
		m_l3cat_cos[i].id = 0;
	}

	if (m_is_chunk_allocated)
		free(m_chunk_start);

	m_chunk_start = NULL;
	m_chunk_size = 0;
	m_is_chunk_allocated = 0;

	return ret;
}


/*
 * cat_test - Execute CAT benchmark and measure cache misses
 * @test:		Test information structure
 * @uparams:		User supplied parameters
 * @param:		Parameters passed to cat_test()
 * @span:		Buffer size for the benchmark
 * @current_mask	Start mask for the first iteration
 *
 * Run CAT selftest by varying the allocated cache portion and comparing the
 * impact on cache misses (the result analysis is done in check_results()
 * and show_results_info(), not in this function).
 *
 * One bit is removed from the CAT allocation bit mask (in current_mask) for
 * each subsequent test which keeps reducing the size of the allocated cache
 * portion. A single test flushes the buffer, reads it to warm up the cache,
 * and reads the buffer again. The cache misses are measured during the last
 * read pass.
 *
 * Return:		0 when the test was run, < 0 on error.
 */
static int cat_test(const struct resctrl_test *test,
		    const struct user_params *uparams,
		    struct resctrl_val_param *param,
		    size_t span, unsigned long current_buf_mask, unsigned long full_cache_mask, unsigned long cache_total_size)
{
	char *resctrl_val = param->resctrl_val;
	struct perf_event_read pe_read;
	struct perf_event_attr pea;
	cpu_set_t old_affinity;
	unsigned char *buf = NULL, *dram_buf = NULL;
	char schemata[64];
	int ret, i, pe_fd = 0;
	pid_t bm_pid = 0;
#if REF
	struct perf_event_read pe_read_ref;
	struct perf_event_attr pea_ref;
	int pe_fd_ref = 0;
#endif
#if PM_BUFFER
	int pm_fd;
#endif
#if BOMB
	unsigned char *bomb_thread_buf = NULL;
	pthread_t bomb_thread;

	if (uparams->cat_type == DELEGATE_CAT) {
		// cpu_set_t cpuset;
		// CPU_ZERO(&cpuset);
		// CPU_SET(uparams->cpu, &cpuset);
		// if (sched_setaffinity(0, sizeof(cpuset), &cpuset) == -1) {
		// 	perror("sched_setaffinity");
		// 	exit(EXIT_FAILURE);
		// }
		// printf("Main pid: %d, CPU: %d\n", getpid(), sched_getcpu());
		
		delegate_pid = fork();
		if (delegate_pid < 0) {
			printf("fork failed\n");
			return -1;
		} else if (delegate_pid == 0) {
			// cpu_set_t cpuset;
			// CPU_ZERO(&cpuset);
			// CPU_SET(uparams->cpu, &cpuset);
			// if (sched_setaffinity(0, sizeof(cpuset), &cpuset) == -1) {
			// 	perror("sched_setaffinity");
			// 	exit(EXIT_FAILURE);
			// }
			// printf("delegate_pid=%d run on CPU %d\n", getpid(), uparams->cpu);
			delegate_function(14*1024*1024);
			exit(EXIT_SUCCESS);
		}
		if (uparams->cat_type == DELEGATE_CAT) {
			unsigned long cat_mask = uparams->fixed_cat_mask ? uparams->fixed_cat_mask : current_buf_mask;

			ret = write_bm_pid_to_resctrl(delegate_pid, param->ctrlgrp, param->mongrp,
						resctrl_val);
			printf("write_bm_pid_to_resctrl delegate_pid=%d\n", delegate_pid);
			if (ret)
				goto reset_affinity;

			cat_mask = 0xff;//>>= 2; // borrow 2 ways from the bombs
			snprintf(schemata, sizeof(schemata), "%lx", param->mask & ~cat_mask);
			ret = write_schemata("", schemata, uparams->cpu, test->resource);
			if (ret)
				goto free_buf;
			snprintf(schemata, sizeof(schemata), "%lx", cat_mask);
			ret = write_schemata(param->ctrlgrp, schemata, uparams->cpu, test->resource);
			if (ret)
				goto free_buf;
		}
	}

	for (int i = 0; i < uparams->n_bombs; i++) {
		bomb_pids[i] = fork();
		if (bomb_pids[i] < 0) {
			printf("fork failed\n");
			return -1;
		} else if (bomb_pids[i] == 0) {
			bomb_function();
			exit(EXIT_SUCCESS);
		}
	}
	if (uparams->n_bombs)
		sleep(5); // wait for bombs to be ready
	if (uparams->cat_type == DELEGATE_CAT) {
		ksft_print_msg("Delegate CAT: %d is ready\n", delegate_pid);
	}
	ksft_print_msg("All bombs: ");
	for (int i = 0; i < uparams->n_bombs; i++) {
		ksft_print_msg("%d ", bomb_pids[i]);
	}
	ksft_print_msg("are ready\n");

	if (uparams->cat_type == WRITER_BOMB_CAT) {
		// create a thread (share same PID with main process) that runs bomb_function() in the background
		int ret;
		bomb_thread_buf = alloc_buffer(BOMB_SPAN, 1);
		if (!bomb_thread_buf) {
			ksft_print_msg("alloc buffer failed\n");
			goto free_buf;
		}

		ret = pthread_create(&bomb_thread, NULL, (void *)bomb_thread_function, bomb_thread_buf);
		if (ret) {
			ksft_print_msg("pthread_create failed\n");
			return -1;
		}
		pthread_detach(bomb_thread);
	}
#endif
	if (strcmp(param->filename, "") == 0)
		sprintf(param->filename, "stdio");

	bm_pid = getpid();

	/* Taskset benchmark to specified cpu */
	ret = taskset_benchmark(bm_pid, uparams->cpu, &old_affinity);
	if (ret)
		return ret;

	if (uparams->cat_type != CACHE_PSEUDO_LOCKING) {
		if (uparams->cat_type != REVERSED_CAT && uparams->cat_type != DELEGATE_CAT) {
			/* Write benchmark to specified con_mon grp, mon_grp in resctrl FS*/
			ret = write_bm_pid_to_resctrl(bm_pid, param->ctrlgrp, param->mongrp,
							resctrl_val);
			if (ret)
				goto reset_affinity;
		}
		if (uparams->cat_type == REVERSED_CAT || uparams->cat_type == ALL_CAT) {
			/* Place BOMBS in a separate CAT group and continue monitoring the LLC misses and PM bandwidth of the main process running in the default CAT group */
			for (int i = 0; i < uparams->n_bombs; i++) {
				ret = write_bm_pid_to_resctrl(bomb_pids[i], param->ctrlgrp, param->mongrp,
							resctrl_val);
				if (ret)
					goto reset_affinity;
			}
		}
	}

	if (uparams->just_run_bomb) {
		if (uparams->cat_type != NO_CAT && uparams->cat_type != CACHE_PSEUDO_LOCKING) {
			unsigned long cat_mask = uparams->fixed_cat_mask ? uparams->fixed_cat_mask : current_buf_mask;
			
			if (uparams->cat_type == REVERSED_CAT || uparams->cat_type == ALL_CAT)
				cat_mask >>= 2; // note that 2 ways in main group are shared with other devices, so we borrow 2 ways from the bombs

			snprintf(schemata, sizeof(schemata), "%lx", param->mask & ~cat_mask);
			ret = write_schemata("", schemata, uparams->cpu, test->resource);
			if (ret)
				goto free_buf;
			snprintf(schemata, sizeof(schemata), "%lx", cat_mask);
			ret = write_schemata(param->ctrlgrp, schemata, uparams->cpu, test->resource);
			if (ret)
				goto free_buf;
		}
		ksft_print_msg("Running bombs, any key to quit\n");
		getchar();

		goto reset_affinity;
	}
	if (!uparams->monitor_ipmctl) {
		perf_event_attr_initialize(&pea, PERF_COUNT_HW_CACHE_MISSES);
		perf_event_initialize_read_format(&pe_read);
		pe_fd = perf_open(&pea, bm_pid, uparams->cpu);
		if (pe_fd < 0) {
			ret = -1;
			goto reset_affinity;
		}
#if REF
		perf_event_attr_initialize(&pea_ref, PERF_COUNT_HW_CACHE_REFERENCES);
		perf_event_initialize_read_format(&pe_read_ref);
		pe_fd_ref = perf_open(&pea_ref, bm_pid, uparams->cpu);
		if (pe_fd_ref < 0) {
			ret = -1;
			goto reset_affinity;
		}
#endif
	}

#if PM_BUFFER
	if (uparams->cat_type == DEVDAX_CAT || uparams->cat_type == MARGIN_DEVDAX_CAT)
		buf = alloc_devdax_buffer(span, 1, &pm_fd);
	else if (uparams->cat_type == DRAM_CAT)
		buf = alloc_buffer(span, 1);
	else if (uparams->cat_type == DRAM_HUGE_PAGE_CAT)
		buf = alloc_huge_page_buffer(span, 1, &pm_fd);
	else
		buf = alloc_pm_buffer(span, 1, &pm_fd);
	#if FILE_WRITE
	// munmap(buf, span);
	// buf = NULL;
	#endif
#else
	buf = alloc_buffer(span, 1);
#endif
	if (uparams->cat_type == CACHE_PSEUDO_LOCKING) {
		if (dlock_init(buf, span, 1, 0))
            printf("dlock err\n");
		else
			printf("dlock init ok\n");
	}

	// if (!buf) { // NULL for FILE_WRITE
	// 	ret = -1;
	// 	goto pe_close;
	// }

	if (uparams->preset == DRAM_ENLARGE_WSS) {
		dram_buf = alloc_buffer(span, 1);
		if (!dram_buf) {
			ret = -1;
			goto free_buf;
		}
	} else dram_buf = NULL;

	while (true) {
		unsigned long cat_mask = uparams->fixed_cat_mask ? uparams->fixed_cat_mask : current_buf_mask;
		unsigned long buf_size = cache_portion_size(cache_total_size, current_buf_mask, full_cache_mask), buf_size_print = buf_size, dram_buf_size = buf_size, cache_size = cache_portion_size(cache_total_size, cat_mask, full_cache_mask);
		clock_t start_time = 0, end_time = 0;
		double cpu_time_used = 0;

		if (uparams->preset == SET_CONTENTION && uparams->half_alloc_size) {
			buf_size = cache_size - buf_size / 2;
			buf_size_print = buf_size;
		}
		if (uparams->preset == DRAM_ENLARGE_WSS && uparams->half_alloc_size) {
			buf_size_print /= 2;
			dram_buf_size /= 2;
		}

		if (uparams->preset != DRAM_ENLARGE_WSS && uparams->preset != SET_CONTENTION && current_buf_mask <= uparams->end_mask)
			break;

		if (uparams->cat_type == MARGIN_CAT || uparams->cat_type == MARGIN_DEVDAX_CAT)
			buf_size = cache_portion_size(cache_total_size, current_buf_mask >> 1, full_cache_mask);
			// buf_size *= 0.9; // shrink to reduce set contention

		if (uparams->cat_type == REVERSED_CAT || uparams->cat_type == ALL_CAT)
			cat_mask >>= 2; // note that 2 ways in main group are shared with other devices, so we borrow 2 ways from the bombs
#if !FILE_WRITE
		if (uparams->cat_type != DELEGATE_CAT) // do not flush cache already pinned by delegate process
			mem_flush(buf, buf_size_print); // move here to avoid interference with PM bandwidth
#endif
		if (uparams->monitor_ipmctl) {
			ksft_print_msg("Before Perf Start: cat_type: %d, allocated_cache: %lu, n_bombs: %d\n", uparams->cat_type, buf_size_print, uparams->n_bombs);
			ret = system("sudo ipmctl show -dimm -performance");
			if (ret)
				return ret;
			ksft_print_msg("Before Perf End: cat_type: %d, allocated_cache: %lu, n_bombs: %d\n", uparams->cat_type, buf_size_print, uparams->n_bombs);
			start_time = clock();
		}
		if (uparams->cat_type != NO_CAT && uparams->cat_type != CACHE_PSEUDO_LOCKING && uparams->cat_type != DELEGATE_CAT) {
			snprintf(schemata, sizeof(schemata), "%lx", param->mask & ~cat_mask); // for other apps
			ret = write_schemata("", schemata, uparams->cpu, test->resource);
			if (ret)
				goto free_buf;
			snprintf(schemata, sizeof(schemata), "%lx", cat_mask); // for cat_test
			ret = write_schemata(param->ctrlgrp, schemata, uparams->cpu, test->resource);
			if (ret)
				goto free_buf;
		}
		// why mask is 0x3ff rather than 0xfff?
		// Parts of a cache may be shared with other devices such as GPU.
		// /sys/fs/resctrl/info/L3/shareable_bits: 0xc00

		// print mask, correspond cache size, buf_size
		ksft_print_msg("Mask: %lx, Cache size: %lu, Buf size: %lu\n", cat_mask, cache_portion_size(cache_total_size, cat_mask, full_cache_mask), buf_size_print);

		if (!uparams->monitor_ipmctl) { // instead of measuring NUM_OF_RUNS times, we measure the whole test
			ret = perf_event_reset_enable(pe_fd);
			if (ret)
				goto free_buf;
#if REF
			ret = perf_event_reset_enable(pe_fd_ref);
			if (ret)
				goto free_buf;
#endif
		}

		for (i = 0; i < NUM_OF_RUNS; i++) {
			#if FILE_WRITE
				if (uparams->cat_type == DEVDAX_CAT)
					fill_cache_write(buf, uparams->preset == DRAM_ENLARGE_WSS ? cache_size : buf_size, true, uparams->cat_type == CAT_FLUSH); // test write
				else
					fill_cache_write_file(&pm_fd, uparams->preset == DRAM_ENLARGE_WSS ? cache_size : buf_size, true);
			#else
				fill_cache_write(buf, uparams->preset == DRAM_ENLARGE_WSS ? cache_size : buf_size, true, uparams->cat_type == CAT_FLUSH); // test write
			#endif
			// if (uparams->cat_type == CAT_FLUSH)
			// 	mem_flush(buf, uparams->preset == DRAM_ENLARGE_WSS ? cache_size : buf_size);
			if (uparams->preset == DRAM_ENLARGE_WSS)
				fill_cache_write(dram_buf, dram_buf_size, true, false);
		}
		if (!uparams->monitor_ipmctl) { // instead of measuring NUM_OF_RUNS times, we measure the whole test
#if REF
			ret = perf_event_measure_ref(pe_fd, &pe_read, pe_fd_ref, &pe_read_ref, param->filename, bm_pid);
#else
			ret = perf_event_measure(pe_fd, &pe_read, param->filename, bm_pid);
#endif
		}
		if (ret)
			goto free_buf;
		if (current_buf_mask == uparams->end_mask) current_buf_mask = 9999;
		else current_buf_mask = next_mask(current_buf_mask); // remove the highest bit from mask
		if (uparams->monitor_ipmctl) {
			ksft_print_msg("After Perf Start: cat_type: %d, allocated_cache: %lu, n_bombs: %d\n", uparams->cat_type, buf_size_print, uparams->n_bombs);
			ret = system("sudo ipmctl show -dimm -performance");
			if (ret)
				return ret;
			end_time = clock();
			cpu_time_used = ((double) (end_time - start_time)) / CLOCKS_PER_SEC;
			ksft_print_msg("After Perf End: cat_type: %d, allocated_cache: %lu, n_bombs: %d, CPU time used: %f\n", uparams->cat_type, buf_size_print, uparams->n_bombs, cpu_time_used);
		}

		if ((uparams->preset == DRAM_ENLARGE_WSS || uparams->preset == SET_CONTENTION) && current_buf_mask == 9999)
			break;
	}

free_buf:
	if (uparams->cat_type == CACHE_PSEUDO_LOCKING) {
		if (dlock_exit())
            printf("dlock err\n");
	}
#if PM_BUFFER
	if (uparams->cat_type == DEVDAX_CAT || uparams->cat_type == MARGIN_DEVDAX_CAT)
		free_devdax_buffer(buf, span, pm_fd);
	else if (uparams->cat_type == DRAM_CAT)
		free(buf);
	else if (uparams->cat_type == DRAM_HUGE_PAGE_CAT)
		free_huge_page_buffer(buf, span, pm_fd);
	else
		free_pm_buffer(buf, span, pm_fd);
#else
	free(buf);
#endif
	if (uparams->preset == DRAM_ENLARGE_WSS)
		free(dram_buf);
	if (uparams->cat_type == WRITER_BOMB_CAT) {
		should_stop = 1;
		pthread_cancel(bomb_thread);
		free(bomb_thread_buf);
		ksft_print_msg("Free bomb_thread_buf: %p\n", bomb_thread_buf);
	}
pe_close:
	if (!uparams->monitor_ipmctl) {
		close(pe_fd);
#if REF
		close(pe_fd_ref);
#endif
	}
reset_affinity:
	taskset_restore(bm_pid, &old_affinity);
		// before run, any key to continue
		// ksft_print_msg("Before kill, any key to continue\n");
		// getchar();
#if BOMB
	if (uparams->cat_type == DELEGATE_CAT) {
		kill(delegate_pid, SIGTERM);
		waitpid(delegate_pid, NULL, 0);
		// ksft_print_msg("Delegate pid: %d is killed\n", delegate_pid);
	}

	for (int i = 0; i < uparams->n_bombs; i++) {
		kill(bomb_pids[i], SIGTERM);
		waitpid(bomb_pids[i], NULL, 0);
		// ksft_print_msg("Bomb pid: %d is killed\n", bomb_pids[i]);
	}
	ksft_print_msg("All bombs are killed\n");
#endif
		// before run, any key to continue
		// ksft_print_msg("After run, any key to continue\n");
		// getchar();

	return ret;
}

static int cat_run_test(const struct resctrl_test *test, const struct user_params *uparams)
{
	unsigned long long_mask, start_mask, full_cache_mask;
	unsigned long cache_total_size = 0;
	int n = uparams->bits;
	unsigned int start;
	int count_of_bits;
	size_t span;
	int ret;

	ret = get_full_cbm(test->resource, &full_cache_mask);
	if (ret)
		return ret;
	/* Get the largest contiguous exclusive portion of the cache */
	// ret = get_mask_no_shareable(test->resource, &long_mask);
	ret = get_full_cbm(test->resource, &long_mask); // get full cache mask, including shareable bits
	if (ret)
		return ret;

	/* Get L3/L2 cache size */
	ret = get_cache_size(uparams->cpu, test->resource, &cache_total_size);
	if (ret)
		return ret;
	ksft_print_msg("Cache size :%lu\n", cache_total_size);

	count_of_bits = count_contiguous_bits(long_mask, &start);

	if (uparams->start_n)
		n = uparams->start_n;

	if (!n)
		n = 6; //count_of_bits / 2; // start from 6 bits

	// if (n > count_of_bits - 1) {
	// 	ksft_print_msg("Invalid input value for no_of_bits n!\n");
	// 	ksft_print_msg("Please enter value in range 1 to %d\n",
	// 		       count_of_bits - 1);
	// 	return -1;
	// }
	start_mask = create_bit_mask(start, n);

	struct resctrl_val_param param = {
		.resctrl_val	= CAT_STR,
		.ctrlgrp	= "c1",
		.filename	= RESULT_FILE_NAME,
		.num_of_runs	= 0,
	};
	param.mask = long_mask;
	span = cache_portion_size(cache_total_size, start_mask, full_cache_mask);
	// print cache_total_size, start_mask, full_cache_mask, span
	ksft_print_msg("Cache total size: %lu, Start mask: %lx, Full cache mask: %lx, Span: %lu\n", cache_total_size, start_mask, full_cache_mask, span);
	// print long_mask, start, count_of_bits
	ksft_print_msg("Long mask: %lx, Start: %d, Count of bits: %d\n", long_mask, start, count_of_bits);
	remove(param.filename);

	// ksft_print_msg("No cat: %d\n", uparams->cat_type);

	ret = cat_test(test, uparams, &param, span, start_mask, full_cache_mask, cache_total_size);
	if (ret)
		goto out;

	if (!uparams->just_run_bomb)
		ret = check_results(&param, test->resource,
					cache_total_size, full_cache_mask, start_mask, uparams);
out:
	cat_test_cleanup();

	return ret;
}

static int noncont_cat_run_test(const struct resctrl_test *test,
				const struct user_params *uparams)
{
	unsigned long full_cache_mask, cont_mask, noncont_mask;
	unsigned int eax, ebx, ecx, edx, sparse_masks;
	int bit_center, ret;
	char schemata[64];

	/* Check to compare sparse_masks content to CPUID output. */
	ret = resource_info_unsigned_get(test->resource, "sparse_masks", &sparse_masks);
	if (ret)
		return ret;

	if (!strcmp(test->resource, "L3"))
		__cpuid_count(0x10, 1, eax, ebx, ecx, edx);
	else if (!strcmp(test->resource, "L2"))
		__cpuid_count(0x10, 2, eax, ebx, ecx, edx);
	else
		return -EINVAL;

	if (sparse_masks != ((ecx >> 3) & 1)) {
		ksft_print_msg("CPUID output doesn't match 'sparse_masks' file content!\n");
		return 1;
	}

	/* Write checks initialization. */
	ret = get_full_cbm(test->resource, &full_cache_mask);
	if (ret < 0)
		return ret;
	bit_center = count_bits(full_cache_mask) / 2;

	/*
	 * The bit_center needs to be at least 3 to properly calculate the CBM
	 * hole in the noncont_mask. If it's smaller return an error since the
	 * cache mask is too short and that shouldn't happen.
	 */
	if (bit_center < 3)
		return -EINVAL;
	cont_mask = full_cache_mask >> bit_center;

	/* Contiguous mask write check. */
	snprintf(schemata, sizeof(schemata), "%lx", cont_mask);
	ret = write_schemata("", schemata, uparams->cpu, test->resource);
	if (ret) {
		ksft_print_msg("Write of contiguous CBM failed\n");
		return 1;
	}

	/*
	 * Non-contiguous mask write check. CBM has a 0xf hole approximately in the middle.
	 * Output is compared with support information to catch any edge case errors.
	 */
	noncont_mask = ~(0xfUL << (bit_center - 2)) & full_cache_mask;
	snprintf(schemata, sizeof(schemata), "%lx", noncont_mask);
	ret = write_schemata("", schemata, uparams->cpu, test->resource);
	if (ret && sparse_masks)
		ksft_print_msg("Non-contiguous CBMs supported but write of non-contiguous CBM failed\n");
	else if (ret && !sparse_masks)
		ksft_print_msg("Non-contiguous CBMs not supported and write of non-contiguous CBM failed as expected\n");
	else if (!ret && !sparse_masks)
		ksft_print_msg("Non-contiguous CBMs not supported but write of non-contiguous CBM succeeded\n");

	return !ret == !sparse_masks;
}

static bool noncont_cat_feature_check(const struct resctrl_test *test)
{
	if (!resctrl_resource_exists(test->resource))
		return false;

	return resource_info_file_exists(test->resource, "sparse_masks");
}

struct resctrl_test l3_cat_test = {
	.name = "L3_CAT",
	.group = "CAT",
	.resource = "L3",
	.feature_check = test_resource_feature_check,
	.run_test = cat_run_test,
};

struct resctrl_test l3_noncont_cat_test = {
	.name = "L3_NONCONT_CAT",
	.group = "CAT",
	.resource = "L3",
	.feature_check = noncont_cat_feature_check,
	.run_test = noncont_cat_run_test,
};

struct resctrl_test l2_noncont_cat_test = {
	.name = "L2_NONCONT_CAT",
	.group = "CAT",
	.resource = "L2",
	.feature_check = noncont_cat_feature_check,
	.run_test = noncont_cat_run_test,
};
