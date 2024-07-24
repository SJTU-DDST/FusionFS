#ifndef __CACHE_H_
#define __CACHE_H_

#include <linux/list.h>
#include <linux/slab.h>
#include <linux/hashtable.h>

#include "pmfs.h"
#include "pmfs_config.h"
// IMPORTANT: 这个值需要根据CAT分配的缓存调整
#define FREQUENT_LIMIT (6 * 896 * 4096) // TODO: 写请求可能包含多页
#define RECENT_LIMIT (6 * 896 * 4096) // 这个调小可以减少抖动？TODO: 驱逐时flush

#define ACCESS_COUNT 1
#if ACCESS_COUNT
#define PROMOTE_THRESHOLD 16
#endif

#define DEBUG 0
#if DEBUG
#define ACCESS_COUNT 1
#endif

#define PEEK 0
#if PEEK
#define PEEK_THRESHOLD  (100000000)
#define RESET_THRESHOLD (10000000000)
#endif

#define BATCHING 1
#if BATCHING
#define MAX_BATCH_SIZE 128
#endif

struct page_node {
    u64 xmem;
    size_t count;
#if ACCESS_COUNT
    size_t access_count;
#endif
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
// struct queue *frequent, *recent;

int init_page_node_cache(void);
int destroy_page_node_cache(void);
// struct queue *create_queue(int limit);
// void enqueue(struct queue *q, int inode_number, int file_index);
// int dequeue(struct queue *q, int inode_number, int file_index);
int pmfs_get_hotness_single(u64 xmem, size_t count);
int pmfs_peek_hotness(u64 xmem, size_t count);
int pmfs_get_hotness(u64 xmem, size_t count);

#endif /* __CACHE_H_ */