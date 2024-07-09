// #include <linux/spinlock.h>
#include <linux/rwsem.h>

#include "cache.h"
// #define NO_EVICT 1
// #if NO_EVICT
// #pragma message "测试禁止驱逐frequent，来模拟无抖动，无抖动可提升吞吐量，TODO: 按照epoch允许或禁止驱逐，以提升并发"
// #endif

// #define ITER_OVER_PAGES 1
// #if ITER_OVER_PAGES
// #pragma message "Iterating over pages, add them as separate page_node"
// #endif

static struct kmem_cache *page_node_cache;
static struct queue *frequent, *recent;

#if BATCHING
    DEFINE_PER_CPU(u64 *, cpu_xmem_array_ptr);
    DEFINE_PER_CPU(size_t *, cpu_count_array_ptr);
    DEFINE_PER_CPU(size_t, cpu_batch_size);
#endif

// static struct spinlock queue_lock;
static DECLARE_RWSEM(my_rwsem);

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
#if BATCHING
    int cpu;
    for_each_possible_cpu(cpu) {
        per_cpu(cpu_xmem_array_ptr, cpu) = kmalloc(MAX_BATCH_SIZE * sizeof(u64), GFP_KERNEL);
        if (!per_cpu(cpu_xmem_array_ptr, cpu)) {
            pr_err("Failed to allocate memory for cpu_xmem_array_ptr\n");
            return -ENOMEM;
        }
        per_cpu(cpu_count_array_ptr, cpu) = kmalloc(MAX_BATCH_SIZE * sizeof(size_t), GFP_KERNEL);
        if (!per_cpu(cpu_count_array_ptr, cpu)) {
            pr_err("Failed to allocate memory for cpu_count_array_ptr\n");
            return -ENOMEM;
        }
    }
#endif
    page_node_cache = kmem_cache_create("page_node_cache", sizeof(struct page_node), 0, (SLAB_RECLAIM_ACCOUNT | SLAB_MEM_SPREAD), NULL);
    if (page_node_cache == NULL)
        return -ENOMEM;

    frequent = create_queue(FREQUENT_LIMIT);
    if (!frequent)
        return -ENOMEM;
    recent = create_queue(RECENT_LIMIT);
    if (!recent)
        return -ENOMEM;

    init_rwsem(&my_rwsem);
    
    // pr_info("page_node_cache initialized, page_node_cache: %p, frequent: %p, recent: %p\n", page_node_cache, frequent, recent);
    return 0;
}

int destroy_page_node_cache(void) {
#if BATCHING
    int cpu;
    for_each_possible_cpu(cpu) {
        kfree(per_cpu(cpu_xmem_array_ptr, cpu));
        kfree(per_cpu(cpu_count_array_ptr, cpu));
    }
#endif
    // free all page nodes with list_for_each_entry_safe
    struct page_node *node, *tmp;
    list_for_each_entry_safe(node, tmp, &frequent->head, list) {
        hash_del(&node->hash);
        list_del(&node->list);
        kmem_cache_free(page_node_cache, node);
    }
    list_for_each_entry_safe(node, tmp, &recent->head, list) {
        hash_del(&node->hash);
        list_del(&node->list);
        kmem_cache_free(page_node_cache, node);
    }

    kmem_cache_destroy(page_node_cache);
    kfree(frequent);
    kfree(recent);

    // pr_info("page_node_cache destroyed\n");
    return 0;
}

int pmfs_get_hotness_single(u64 xmem, size_t count) { // TODO: iterover over pages, add them as separate page_node, but how can we return hotness?
    struct page_node *node;
    struct hlist_node *tmp;
    int result = 0;
#if DEBUG
    static int hotness_cnt[5] = {0, 0, 0, 0, 0};
    int cold_recent_evict = 0;
#endif
// #if ITER_OVER_PAGES
//     u64 xmem_bak = xmem;
//     size_t count_bak = count;
//     xmem = xmem & PAGE_MASK;
//     count = PAGE_SIZE;

//     while (xmem < xmem_bak + count_bak) {
// #endif
    // if (count == 28672) return 0;

#if PEEK
    static int counter = 0;
    counter++;
    if (counter >= RESET_THRESHOLD)
        counter = 0;
    if (counter >= PEEK_THRESHOLD) {
        result = pmfs_peek_hotness(xmem, count);
        goto ret_peek;
    }
#endif

#if !BATCHING
    down_write(&my_rwsem);
#endif
    hash_for_each_possible_safe(frequent->hash_table, node, tmp, hash, xmem) {
        if (node->xmem == xmem) {
            list_move(&node->list, &frequent->head);
#if DEBUG
            node->access_count++;
#endif
            result = 4; // frequent->frequent
            goto ret;
        }
    }
    hash_for_each_possible_safe(recent->hash_table, node, tmp, hash, xmem) {
        if (node->xmem == xmem) {
            list_move(&node->list, &frequent->head);
            recent->size -= count;
            hash_del(&node->hash);
            frequent->size += count;
            hash_add(frequent->hash_table, &node->hash, xmem);
#if DEBUG
            node->access_count++;
#endif

            while (frequent->size > frequent->limit) {
                struct page_node *old_node = list_last_entry(&frequent->head, struct page_node, list);
                hash_del(&old_node->hash);
                list_del(&old_node->list);
                pmfs_flush_buffer(old_node->xmem, old_node->count, false);
                frequent->size -= old_node->count;
                kmem_cache_free(page_node_cache, old_node);
                result = 3; // recent->frequent evict
                // goto ret;
            }
            if (result == 3) goto ret;
            result = 2; // recent->frequent no evict
            goto ret;
        }
    }
    struct page_node *new_node = kmem_cache_alloc(page_node_cache, GFP_KERNEL);
    if (!new_node) {
        pr_err("Failed to allocate memory for new_node\n");
        up_write(&my_rwsem);
        return -ENOMEM;
    }
    new_node->xmem = xmem;
    new_node->count = count;
#if DEBUG
    new_node->access_count = 1;
#endif
    hash_add(recent->hash_table, &new_node->hash, xmem);
    list_add(&new_node->list, &recent->head);
    recent->size += count;
    while (recent->size > recent->limit) {
        struct page_node *old_node = list_last_entry(&recent->head, struct page_node, list);
        hash_del(&old_node->hash);
        list_del(&old_node->list);
        recent->size -= old_node->count;
        kmem_cache_free(page_node_cache, old_node);
        // result = 0; // 1; FIXME: now it's counted as enter recent no evict but actually it's evicted. This is because we regard hotness=0 as cold data.
#if DEBUG
        cold_recent_evict = 1;
#endif
    }
ret:
#if !BATCHING
    up_write(&my_rwsem);
#endif
ret_peek:
#if DEBUG
    hotness_cnt[cold_recent_evict ? 1 : result]++;
    if (hotness_cnt[0] + hotness_cnt[1] + hotness_cnt[2] + hotness_cnt[3] + hotness_cnt[4] >= 1000000) {
        struct page_node *node;

        pmfs_dbg("cold->recent: %d, cold->recent evict: %d, recent->frequent: %d, recent->frequent evict: %d, frequent->frequent: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
        // print the size of frequent and recent and their limits
        pmfs_dbg("frequent size: %d, limit: %d, recent size: %d, limit: %d\n", frequent->size, frequent->limit, recent->size, recent->limit);
        // print the items in frequent and recent lists
        list_for_each_entry(node, &frequent->head, list) {
            pmfs_dbg("frequent: xmem=%llu, count=%lu, access_count=%lu\n", node->xmem, node->count, node->access_count);
        }
        list_for_each_entry(node, &recent->head, list) {
            pmfs_dbg("recent: xmem=%llu, count=%lu, access_count=%lu\n", node->xmem, node->count, node->access_count);
        }
        hotness_cnt[0] = 0;
        hotness_cnt[1] = 0;
        hotness_cnt[2] = 0;
        hotness_cnt[3] = 0;
        hotness_cnt[4] = 0;
    }
#endif
    return result;
}

int pmfs_peek_hotness(u64 xmem, size_t count) {
    struct page_node *node;
    struct hlist_node *tmp;
    int result = 0;
    down_read(&my_rwsem);
    hash_for_each_possible_safe(frequent->hash_table, node, tmp, hash, xmem) {
        if (node->xmem == xmem) {
            result = 4; // frequent
            goto ret;
        }
    }
    hash_for_each_possible_safe(recent->hash_table, node, tmp, hash, xmem) {
        if (node->xmem == xmem) {
            result = 2; // recent
            goto ret;
        }
    }

ret:
    up_read(&my_rwsem);
    return result;
}

int pmfs_get_hotness(u64 xmem, size_t count) {
#if BATCHING
    int batch_size = this_cpu_read(cpu_batch_size);
    if (count > FREQUENT_LIMIT || count > RECENT_LIMIT) return 0; // too large, ignore
    
    if (batch_size >= MAX_BATCH_SIZE) {
        int i;
        down_write(&my_rwsem);
        for (i = 0; i < batch_size; i++)
            pmfs_get_hotness_single(this_cpu_read(cpu_xmem_array_ptr)[i], this_cpu_read(cpu_count_array_ptr)[i]);
        up_write(&my_rwsem);
        this_cpu_write(cpu_batch_size, 0);
        batch_size = 0;
    }

    this_cpu_read(cpu_xmem_array_ptr)[batch_size] = xmem;
    this_cpu_read(cpu_count_array_ptr)[batch_size] = count;
    this_cpu_inc(cpu_batch_size);

    return pmfs_peek_hotness(xmem, count);
#else
    if (count > FREQUENT_LIMIT || count > RECENT_LIMIT) return 0; // too large, ignore
    return pmfs_get_hotness_single(xmem, count);
#endif
}