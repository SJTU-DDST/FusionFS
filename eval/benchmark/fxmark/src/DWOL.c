/**
 * Nanobenchmark: block write
 *   BW. PROCESS = {ovewrite file at /test/$PROCESS}
 *       - TEST: ideal, no conention
 */	      
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#include <stdlib.h>
#include <assert.h>
#include "fxmark.h"
#include "util.h"

#include <stdbool.h>

#define LARGE_WSS 1
#define WRITER_BOMB 0

#if WRITER_BOMB
#define BOMB_SPAN 1000*1024*1024
#define CL_SIZE			(64)
#define FILL_IDX_MULT	23

unsigned char *bomb_thread_buf = NULL;
pthread_t bomb_thread;
volatile int should_stop = 0;

/* Volatile memory sink to prevent compiler optimizations */
static volatile int sink_target;
volatile int *value_sink = &sink_target;

static void sb(void)
{
#if defined(__i386) || defined(__x86_64)
	asm volatile("sfence\n\t"
		     : : : "memory");
#endif
}

static void cl_flush(void *p)
{
#if defined(__i386) || defined(__x86_64)
	asm volatile("clflush (%0)\n\t"
		     : : "r"(p) : "memory");
#endif
}


static void mem_flush(unsigned char *buf, size_t buf_size)
{
	unsigned char *cp = buf;
	size_t i = 0;

	buf_size = buf_size / CL_SIZE; /* mem size in cache lines */

	for (i = 0; i < buf_size; i++)
		cl_flush(&cp[i * CL_SIZE]);

	sb();
}

static int fill_one_span_read(unsigned char *buf, size_t buf_size)
{
	unsigned int size = buf_size / (CL_SIZE / 2); // span / 32
	unsigned int i, idx = 0;
	unsigned char sum = 0;

	/*
	 * Read the buffer in an order that is unexpected by HW prefetching
	 * optimizations to prevent them interfering with the caching pattern.
	 *
	 * The read order is (in terms of halves of cachelines):
	 *	i * FILL_IDX_MULT % size
	 * The formula is open-coded below to avoiding modulo inside the loop
	 * as it improves MBA/MBM result stability on some architectures.
	 */
	for (i = 0; i < size; i++) {
		sum += buf[idx * (CL_SIZE / 2)];

		idx += FILL_IDX_MULT;
		while (idx >= size)
			idx -= size;
	}

	return sum;
}

static void fill_one_span_write(unsigned char *buf, size_t buf_size)
{
	unsigned char *end_ptr = buf + buf_size;
	unsigned char *p;

	p = buf;
	while (p < end_ptr) {
		*p = '1';
		p += (CL_SIZE / 2);
	}
}

static void fill_cache_read(unsigned char *buf, size_t buf_size, bool once)
{
	int ret = 0;

	while (1) {
		ret = fill_one_span_read(buf, buf_size);
		if (once)
			break;
	}

	/* Consume read result so that reading memory is not optimized out. */
	*value_sink = ret;
}

static void fill_cache_write(unsigned char *buf, size_t buf_size, bool once)
{
	while (1) {
		fill_one_span_write(buf, buf_size);
		if (once)
			break;
	}
}

static void bomb_thread_function(unsigned char *bomb_buf)
{
	// ksft_print_msg("PID=%d running bomb_thread_function\n", getpid());
	mem_flush(bomb_buf, BOMB_SPAN);
	fill_cache_read(bomb_buf, BOMB_SPAN, true);

	while (!should_stop) {
		fill_cache_write(bomb_buf, BOMB_SPAN, true);
		pthread_testcancel();
	}
}
#endif

static void set_test_root(struct worker *worker, char *test_root)
{
	struct fx_opt *fx_opt = fx_opt_worker(worker);
	sprintf(test_root, "%s/%d", fx_opt->root, worker->id);
}

static int pre_work(struct worker *worker)
{
        char *page = NULL;
        struct bench *bench = worker->bench;
	char test_root[PATH_MAX];
	char file[PATH_MAX];
	int fd, rc = 0;

	/* create test root */
	set_test_root(worker, test_root);
	rc = mkdir_p(test_root);
	if (rc) return rc;

	/* create a test file */ 
	snprintf(file, PATH_MAX, "%s/n_blk_wrt.dat", test_root);
	if ((fd = open(file, O_CREAT | O_RDWR, S_IRWXU)) == -1)
		goto err_out;

	if(posix_memalign((void **)&(worker->page), PAGE_SIZE, PAGE_SIZE))
	  goto err_out;
	page = worker->page;
	if (!page)
		goto err_out;

#if DEBUG
	/*to debug*/
	fprintf(stderr, "DEBUG: worker->id[%d], page address :%p\n",worker->id, page);
#endif

	/*set flag with O_DIRECT if necessary*/
	if(bench->directio && (fcntl(fd, F_SETFL, O_DIRECT)==-1))
	  goto err_out;

	if (write(fd, page, PAGE_SIZE) != PAGE_SIZE)
	  goto err_out;
out:
	/* put fd to worker's private */
	worker->private[0] = (uint64_t)fd;
	return rc;
err_out:
	bench->stop = 1;
	rc = errno;
	free(page);
	goto out;
}

static int main_work(struct worker *worker)
{
  	char *page = worker->page;
	struct bench *bench = worker->bench;
	int fd, rc = 0;
	uint64_t iter = 0;

#if WRITER_BOMB
	bomb_thread_buf = malloc(BOMB_SPAN);
#endif

#if DEBUG 
	fprintf(stderr, "DEBUG: worker->id[%d], main worker address :%p\n",
		worker->id, worker->page);
#endif
	assert(page);

	/* fsync */
	fd = (int)worker->private[0];
	for (iter = 0; !bench->stop; ++iter) {
	#if LARGE_WSS // 3.5MB=896, 7MB=1792, 10.5MB=2688, 14MB=3584, 17.5MB=4480, 21MB=5376, 24.5MB=6272, 28MB=7168, 31.5MB=8064, 35MB=8960
		if (pwrite(fd, page, PAGE_SIZE, (rand() % (int)(14*256)) * PAGE_SIZE) != PAGE_SIZE) // 7MB here; 64*56*4kb=14MB=3584 pages
	#else
     	if (pwrite(fd, page, PAGE_SIZE, 0) != PAGE_SIZE)
	#endif
		goto err_out;

		#if WRITER_BOMB
		fill_cache_write(bomb_thread_buf, BOMB_SPAN, true);
		#endif
	}
out:
	close(fd);
	worker->works = (double)iter;
#if WRITER_BOMB
	free(bomb_thread_buf);
#endif
	return rc;
err_out:
	bench->stop = 1;
	rc = errno;
        free(page);
	goto out;
}

struct bench_operations n_blk_wrt_ops = {
	.pre_work  = pre_work, 
	.main_work = main_work,
};
