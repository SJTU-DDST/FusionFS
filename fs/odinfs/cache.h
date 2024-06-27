#ifndef __CACHE_H_
#define __CACHE_H_

#include <linux/list.h>
#include <linux/slab.h>
#include <linux/hashtable.h>

#include "pmfs.h"
#include "pmfs_config.h"

#define AM_LIMIT (5 * 896) // TODO: 写请求可能包含多页
#define A1OUT_LIMIT (5 * 896) // 这个调小可以减少抖动？TODO: 驱逐时flush

struct page_node {
    u64 xmem;
    size_t count;
    struct hlist_node hash;
    struct list_head list;
};

struct queue {
    DECLARE_HASHTABLE(hash_table, 16);
    struct list_head head;
    int size;
    int limit;
};

// struct kmem_cache *page_node_cache;
// struct queue *am, *a1out;

int init_page_node_cache(void);
int destroy_page_node_cache(void);
// struct queue *create_queue(int limit);
// void enqueue(struct queue *q, int inode_number, int file_index);
// int dequeue(struct queue *q, int inode_number, int file_index);
int pmfs_page_hotness(u64 xmem, size_t count);

#endif /* __CACHE_H_ */