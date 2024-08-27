// SPDX-License-Identifier: GPL-2.0
/*
 * fill_buf benchmark
 *
 * Copyright (C) 2018 Intel Corporation
 *
 * Authors:
 *    Sai Praneeth Prakhya <sai.praneeth.prakhya@intel.com>,
 *    Fenghua Yu <fenghua.yu@intel.com>
 */
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <inttypes.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <linux/mman.h>

#include "resctrl.h"

#define CL_SIZE			(64)
#define PAGE_SIZE		(4 * 1024)
#define MB			(1024 * 1024)
#define BUF_SIZE_SHRINK		(0)
#define ALLOC_HUGE_PAGE_SIZE	(1024 * 1024 * 1024)

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

void mem_flush(unsigned char *buf, size_t buf_size)
{
	unsigned char *cp = buf;
	size_t i = 0;

	buf_size = buf_size / CL_SIZE; /* mem size in cache lines */

	for (i = 0; i < buf_size; i++)
		cl_flush(&cp[i * CL_SIZE]);

	sb();
}

/*
 * Buffer index step advance to workaround HW prefetching interfering with
 * the measurements.
 *
 * Must be a prime to step through all indexes of the buffer.
 *
 * Some primes work better than others on some architectures (from MBA/MBM
 * result stability point of view).
 */
#define FILL_IDX_MULT	23

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

static void fill_one_span_write(unsigned char *buf, size_t buf_size, bool flush) // 顺序写
{
	unsigned char *end_ptr = buf + buf_size;
	unsigned char *p;

	p = buf;
	while (p < end_ptr) {
		*p = '1';
		p += (CL_SIZE / 2); // TODO: memset -> prefetch -> 20% miss rate
		// memset(p, '1', CL_SIZE);
        // p += CL_SIZE;


		// if p is aligned to a cacheline, flush previous cacheline
		if (((unsigned long)p & (CL_SIZE - 1)) == 0) {
			if (flush)
				cl_flush(p - CL_SIZE);
		}
	}
}

// static void fill_one_span_write(unsigned char *buf, size_t buf_size) // 预防prefetch的随机写，当争用高时可能更明显
// {
// 	unsigned int size = buf_size / (CL_SIZE / 2); // span / 32
// 	unsigned int i, idx = 0;
// 	// unsigned char sum = 0;

// 	/*
// 	 * Read the buffer in an order that is unexpected by HW prefetching
// 	 * optimizations to prevent them interfering with the caching pattern.
// 	 *
// 	 * The read order is (in terms of halves of cachelines):
// 	 *	i * FILL_IDX_MULT % size
// 	 * The formula is open-coded below to avoiding modulo inside the loop
// 	 * as it improves MBA/MBM result stability on some architectures.
// 	 */
// 	for (i = 0; i < size; i++) {
// 		buf[idx * (CL_SIZE / 2)] = '1';

// 		idx += FILL_IDX_MULT;
// 		while (idx >= size)
// 			idx -= size;
// 	}

// 	// return sum;
// }

static void fill_one_span_write_file(int *pm_fd, size_t buf_size)
{
    unsigned char c = '1';
    off_t offset = 0;
    while (offset < buf_size) {
        if (pwrite(*pm_fd, &c, 1, offset) < 0) {
            printf("Error writing to file: %s\n", strerror(errno));
            return;
        }
        offset += (CL_SIZE / 2);
    }
}

void fill_cache_read(unsigned char *buf, size_t buf_size, bool once)
{
	int ret = 0;
	// shrink buf_size a little for the program's DRAM usage
	buf_size = buf_size - BUF_SIZE_SHRINK;

	while (1) {
		ret = fill_one_span_read(buf, buf_size);
		if (once)
			break;
	}

	/* Consume read result so that reading memory is not optimized out. */
	*value_sink = ret;
}

// static 
void fill_cache_write(unsigned char *buf, size_t buf_size, bool once, bool flush)
{
	// shrink buf_size a little for the program's DRAM usage
	buf_size = buf_size - BUF_SIZE_SHRINK;
	while (1) {
		fill_one_span_write(buf, buf_size, flush);
		if (once)
			break;
	}
}

void fill_cache_write_file(int *pm_fd, size_t buf_size, bool once)
{
	// shrink buf_size a little for the program's DRAM usage
	buf_size = buf_size - BUF_SIZE_SHRINK;
	while (1) {
		fill_one_span_write_file(pm_fd, buf_size);
		if (once)
			break;
	}
}

unsigned char *alloc_buffer(size_t buf_size, int memflush)
{
	void *buf = NULL;
	uint64_t *p64;
	size_t s64;
	int ret;

	ret = posix_memalign(&buf, PAGE_SIZE, buf_size);
	if (ret < 0)
		return NULL;

	/* Initialize the buffer */
	p64 = buf;
	s64 = buf_size / sizeof(uint64_t);

	while (s64 > 0) {
		*p64 = (uint64_t)rand();
		p64 += (CL_SIZE / sizeof(uint64_t));
		s64 -= (CL_SIZE / sizeof(uint64_t));
	}

	/* Flush the memory before using to avoid "cache hot pages" effect */
	if (memflush)
		mem_flush(buf, buf_size);

	return buf;
}

unsigned char *alloc_huge_page_buffer(size_t buf_size, int memflush, int *pm_fd)
{
	// void *buf = NULL;
	uint64_t *p64;
	size_t s64;
	// int ret;

	// Open the /dev/zero device
    int fd = open("/dev/zero", O_RDWR);
    if (fd < 0) {
        perror("Open failed");
        exit(1);
    }

    // Use mmap to allocate a huge page
    void *buf = mmap(0, ALLOC_HUGE_PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB | MAP_HUGE_1GB, fd, 0);
    if (buf == MAP_FAILED) {
        perror("mmap failed");
        exit(1);
    }

	/* Initialize the buffer */
	p64 = buf;
	s64 = buf_size / sizeof(uint64_t);

	while (s64 > 0) {
		*p64 = (uint64_t)rand();
		p64 += (CL_SIZE / sizeof(uint64_t));
		s64 -= (CL_SIZE / sizeof(uint64_t));
	}

	/* Flush the memory before using to avoid "cache hot pages" effect */
	if (memflush)
		mem_flush(buf, buf_size);

	*pm_fd = fd;
	return buf;
}

void free_huge_page_buffer(unsigned char *buf, size_t buf_size, int fd)
{
	munmap(buf, ALLOC_HUGE_PAGE_SIZE);
	close(fd);
}

unsigned char *alloc_devdax_buffer(size_t buf_size, int memflush, int *pm_fd)
{
	// void *buf = NULL;
	uint64_t *p64;
	size_t s64;
	// int ret;

	// Open the /dev/dax device
	int fd = open("/dev/dax1.0", O_RDWR); // we use pmem0 for FS, so we use dax1.0 here for convenience
	if (fd < 0) {
		perror("Open failed");
		exit(1);
	}

	// Use mmap to allocate a huge page
	void *buf = mmap(0, ALLOC_HUGE_PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (buf == MAP_FAILED) {
		perror("mmap failed");
		exit(1);
	}

	/* Initialize the buffer */
	p64 = buf;
	s64 = buf_size / sizeof(uint64_t);

	while (s64 > 0) {
		*p64 = (uint64_t)rand();
		p64 += (CL_SIZE / sizeof(uint64_t));
		s64 -= (CL_SIZE / sizeof(uint64_t));
	}

	/* Flush the memory before using to avoid "cache hot pages" effect */
	// if (memflush)
	// 	mem_flush(buf, buf_size); // don't flush PM

	*pm_fd = fd;
	return buf;
}

void free_devdax_buffer(unsigned char *buf, size_t buf_size, int fd)
{
	munmap(buf, ALLOC_HUGE_PAGE_SIZE);
	close(fd);
}

unsigned char *alloc_pm_buffer(size_t buf_size, int memflush, int *pm_fd)
{
	void *buf = NULL;
	uint64_t *p64;
	size_t s64;
	// int ret;
	static int count = 0;
	char filename[256];

	sprintf(filename, "/home/congyong/fxmark-plain/bin/root/file%d.txt", count++);
	// sprintf(filename, "/home/congyong/fxmark-plain/bin/root/file.txt"); // now it is a fixed file
	// #pragma message "alloc_pm_buffer: filename is fixed now"

	int fd = open(filename, O_CREAT | O_RDWR, S_IRWXU);
	if (fd < 0) {
        printf("OPEN Error %d \n", errno);
		return NULL;
    }

	// Extend file size to buf_size
    off_t result = lseek(fd, buf_size - 1, SEEK_SET);
    if (result == -1) {
        printf("Error extending file size\n");
        return NULL;
    }
    result = write(fd, "", 1);
    if (result != 1) {
        printf("Error extending file size\n");
        return NULL;
    }
#if !FILE_WRITE
	buf = mmap(NULL, buf_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (buf == MAP_FAILED) {
		printf("MMAP Error %d \n", errno);
		return NULL;
	}

	/* Initialize the buffer */
	p64 = buf;
	s64 = buf_size / sizeof(uint64_t);

	while (s64 > 0) {
		*p64 = (uint64_t)rand();
		p64 += (CL_SIZE / sizeof(uint64_t));
		s64 -= (CL_SIZE / sizeof(uint64_t));
	}

	/* Flush the memory before using to avoid "cache hot pages" effect */
	// if (memflush)
	// 	mem_flush(buf, buf_size); // don't flush PM

	*pm_fd = fd;
	return buf;
#else
	*pm_fd = fd;
	return NULL;
#endif
}

void free_pm_buffer(unsigned char *buf, size_t buf_size, int fd)
{
#if !FILE_WRITE
	munmap(buf, buf_size);
#endif
	close(fd);
}

int run_fill_buf(size_t buf_size, int memflush, int op, bool once)
{
	unsigned char *buf;

	buf = alloc_buffer(buf_size, memflush);
	if (!buf)
		return -1;

	if (op == 0)
		fill_cache_read(buf, buf_size, once);
	else
		fill_cache_write(buf, buf_size, once, false);
	free(buf);

	return 0;
}
