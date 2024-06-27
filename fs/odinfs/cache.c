#include "cache.h"
#define NO_EVICT 1
#if NO_EVICT
#pragma message "测试禁止驱逐am，来模拟无抖动，无抖动可提升吞吐量，TODO: 按照epoch允许或禁止驱逐，以提升并发"
#endif
static struct kmem_cache *page_node_cache;
static struct queue *am, *a1out;

static struct queue *create_queue(int limit) {
    struct queue *q = kmalloc(sizeof(*q), GFP_KERNEL);
    if (!q)
        return NULL;
    hash_init(q->hash_table);
    INIT_LIST_HEAD(&q->head);
    q->size = 0;
    q->limit = limit;
    return q;
}


int init_page_node_cache(void) {
    page_node_cache = kmem_cache_create("page_node_cache", sizeof(struct page_node), 0, (SLAB_RECLAIM_ACCOUNT | SLAB_MEM_SPREAD), NULL);
    if (page_node_cache == NULL)
        return -ENOMEM;

    am = create_queue(AM_LIMIT);
    if (!am)
        return -ENOMEM;
    a1out = create_queue(A1OUT_LIMIT);
    if (!a1out)
        return -ENOMEM;
    
    // pr_info("page_node_cache initialized, page_node_cache: %p, am: %p, a1out: %p\n", page_node_cache, am, a1out);
    return 0;
}

int destroy_page_node_cache(void) {
    kmem_cache_destroy(page_node_cache);
    kfree(am);
    kfree(a1out);

    // pr_info("page_node_cache destroyed\n");
    return 0;
}

static int enqueue(struct queue *q, u64 xmem, size_t count) {
    int evicted = 0;

    if (q->size >= q->limit) {
#if !NO_EVICT
        struct page_node *old_node = list_first_entry(&q->head, struct page_node, list);
        hash_del(&old_node->hash);
        list_del(&old_node->list);
        pmfs_flush_buffer(old_node->xmem, old_node->count, false);
        kmem_cache_free(page_node_cache, old_node);
        q->size--;
#endif
        evicted = 1;
        // pr_info("Queue=%p is full, remove the oldest xmem=%llu\n", q, old_node->inode_number, old_node->file_index);
    }
#if NO_EVICT
    if (evicted) return evicted;
#endif

    struct page_node *new_node = kmem_cache_alloc(page_node_cache, GFP_KERNEL);
    if (!new_node) {
        pr_err("Failed to allocate memory for new_node\n");
        return -ENOMEM;
    }
    new_node->xmem = xmem;
    new_node->count = count;
    // xmem = ((u64)inode_number << 32) | file_index;
    hash_add(q->hash_table, &new_node->hash, xmem);
    list_add_tail(&new_node->list, &q->head);
    q->size++;
    // pr_info("Insert xmem=%llu into queue=%p, size=%d\n", xmem, q, q->size);

    return evicted;
}

static int dequeue(struct queue *q, u64 xmem) { // TODO: make it thread-safe
    struct page_node *node;
    // u64 xmem = ((u64)inode_number << 32) | file_index;
    hash_for_each_possible(q->hash_table, node, hash, xmem) {
        if (node->xmem == xmem) {
            hash_del(&node->hash);
            list_del(&node->list);
            kmem_cache_free(page_node_cache, node);
            q->size--;
            // pr_info("xmem=%llu found in queue=%p, removing\n", xmem, q);
            return 1;
        }
    }
    // pr_info("xmem=%llu not found in queue=%p\n", xmem, q);
    return 0;
}

// 0, enter a1out, evict or no evict
// 1, a1out->am, no evict
// 2, a1out->am, evict
// 3, am->am, no evict
// 4, am->am, evict

int pmfs_page_hotness(u64 xmem, size_t count) {
    // TODO: 现在的不支持多线程读写的区间重叠，拆分为每个页面
    // TODO: 写入可能跨冷热

    static int hotness_cnt[5] = {0, 0, 0, 0, 0};
    int evicted = 0, ret = 0;
    // u64 i = xmem;
    // while (i < xmem + count) {
    //     u64 page_start = i & PAGE_MASK;       
    // }

    if (dequeue(am, xmem)) {
        evicted = enqueue(am, xmem, count);
        ret = evicted ? 4 : 3;
    } else if (dequeue(a1out, xmem)) {
        evicted = enqueue(am, xmem, count);
        ret = evicted ? 2 : 1;
#if NO_EVICT
        if (ret == 2) ret = 0;
#endif
    } else {
        evicted = enqueue(a1out, xmem, count);
        // pr_info("First access xmem=%llu, insert into a1out\n", xmem);
        ret = 0;
    }
    // hotness_cnt[ret]++;
    // if (hotness_cnt[0] + hotness_cnt[1] + hotness_cnt[2] + hotness_cnt[3] + hotness_cnt[4] >= 100000) {
    //     // pmfs_dbg("hotness 0: %d, hotness 1: %d, hotness 2: %d, hotness 3: %d, hotness 4: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
    //     pmfs_dbg("enter a1out: %d, a1out->am no evict: %d, a1out->am evict: %d, am->am no evict: %d, am->am evict: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
    //     hotness_cnt[0] = 0;
    //     hotness_cnt[1] = 0;
    //     hotness_cnt[2] = 0;
    //     hotness_cnt[3] = 0;
    //     hotness_cnt[4] = 0;
    // }
    return ret;
}


