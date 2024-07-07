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

#define DEBUG 0
static struct kmem_cache *page_node_cache;
static struct queue *frequent, *recent;

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
    kmem_cache_destroy(page_node_cache);
    kfree(frequent);
    kfree(recent);

    // pr_info("page_node_cache destroyed\n");
    return 0;
}

// static int enqueue(struct queue *q, u64 xmem, size_t count) {
//     int evicted = 0;

//     if (q->size >= q->limit) {
// #if !NO_EVICT
//         struct page_node *old_node = list_first_entry(&q->head, struct page_node, list);
//         hash_del(&old_node->hash);
//         list_del(&old_node->list);
//         pmfs_flush_buffer(old_node->xmem, old_node->count, false);
//         kmem_cache_free(page_node_cache, old_node);
//         q->size--;
// #endif
//         evicted = 1;
//         // pr_info("Queue=%p is full, remove the oldest xmem=%llu\n", q, old_node->inode_number, old_node->file_index);
//     }
// #if NO_EVICT
//     if (evicted) return evicted;
// #endif

//     struct page_node *new_node = kmem_cache_alloc(page_node_cache, GFP_KERNEL);
//     if (!new_node) {
//         pr_err("Failed to allocate memory for new_node\n");
//         return -ENOMEM;
//     }
//     new_node->xmem = xmem;
//     new_node->count = count;
//     // xmem = ((u64)inode_number << 32) | file_index;
//     hash_add(q->hash_table, &new_node->hash, xmem);
//     list_add_tail(&new_node->list, &q->head);
//     q->size++;
//     // pr_info("Insert xmem=%llu into queue=%p, size=%d\n", xmem, q, q->size);

//     return evicted;
// }

// static int dequeue(struct queue *q, u64 xmem) { // TODO: make it thread-safe
//     struct page_node *node;
//     struct hlist_node *tmp;
//     // u64 xmem = ((u64)inode_number << 32) | file_index; // 注意必须能编译通过才能parradm
//     hash_for_each_possible_safe(q->hash_table, node, tmp, hash, xmem) { // TODO: hash_for_each_possible_safe, 需要修改参数
//         if (node->xmem == xmem) { // TODO: 使用list_move_tail
//             hash_del(&node->hash); // 可能不需要hash？hash可以快速找到xmem对应的page_node，或者说不需要list？我们需要list来找到最老的node // TODO: 这几句删掉就可以了
//             list_del(&node->list);
//             kmem_cache_free(page_node_cache, node); // FIXME: crash, 可能需要上锁，或者直接移动到另一队列
//             q->size--;
//             // pr_info("xmem=%llu found in queue=%p, removing\n", xmem, q);
//             return 1;
//         }
//     }
//     // pr_info("xmem=%llu not found in queue=%p\n", xmem, q);
//     return 0;
// }

// 0, enter recent, no evict
// 1, enter recent, evict
// 2, recent->frequent, no evict
// 3, recent->frequent, evict
// 4, frequent->frequent, no evict

// int pmfs_page_hotness(u64 xmem, size_t count) {
//     // TODO: 现在的不支持多线程读写的区间重叠，拆分为每个页面
//     // TODO: 写入可能跨冷热

//     static int hotness_cnt[5] = {0, 0, 0, 0, 0};
//     int evicted = 0, ret = 0;
//     // u64 i = xmem;
//     // while (i < xmem + count) {
//     //     u64 page_start = i & PAGE_MASK;       
//     // }

//     down_write(&my_rwsem);

//     if (dequeue(frequent, xmem)) {
//         evicted = enqueue(frequent, xmem, count);
//         ret = evicted ? 4 : 3;
//     } else if (dequeue(recent, xmem)) {
//         evicted = enqueue(frequent, xmem, count);
//         ret = evicted ? 2 : 1;
// #if NO_EVICT
//         if (ret == 2) ret = 0;
// #endif
//     } else {
//         evicted = enqueue(recent, xmem, count);
//         // pr_info("First access xmem=%llu, insert into recent\n", xmem);
//         ret = 0;
//     }

//     // hotness_cnt[ret]++;
//     // if (hotness_cnt[0] + hotness_cnt[1] + hotness_cnt[2] + hotness_cnt[3] + hotness_cnt[4] >= 100000) {
//     //     // pmfs_dbg("hotness 0: %d, hotness 1: %d, hotness 2: %d, hotness 3: %d, hotness 4: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
//     //     pmfs_dbg("enter recent: %d, recent->frequent no evict: %d, recent->frequent evict: %d, frequent->frequent no evict: %d, frequent->frequent evict: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
//     //     hotness_cnt[0] = 0;
//     //     hotness_cnt[1] = 0;
//     //     hotness_cnt[2] = 0;
//     //     hotness_cnt[3] = 0;
//     //     hotness_cnt[4] = 0;
//     // }
//     up_write(&my_rwsem);
//     return ret;
// }

int pmfs_page_hotness(u64 xmem, size_t count) { // TODO: iterover over pages, add them as separate page_node, but how can we return hotness?
    struct page_node *node;
    struct hlist_node *tmp;
    int result = 0;
#if DEBUG
    static int hotness_cnt[5] = {0, 0, 0, 0, 0};
#endif
// #if ITER_OVER_PAGES
//     u64 xmem_bak = xmem;
//     size_t count_bak = count;
//     xmem = xmem & PAGE_MASK;
//     count = PAGE_SIZE;

//     while (xmem < xmem_bak + count_bak) {
// #endif

    down_write(&my_rwsem);
    hash_for_each_possible_safe(frequent->hash_table, node, tmp, hash, xmem) {
        if (node->xmem == xmem) {
            list_move(&node->list, &frequent->head);
            result = 4; // frequent->frequent
            goto ret;
        }
    }
    hash_for_each_possible_safe(recent->hash_table, node, tmp, hash, xmem) {
        if (node->xmem == xmem) {
            list_move(&node->list, &frequent->head);
            recent->size--;
            hash_del(&node->hash);
            frequent->size++;
            hash_add(frequent->hash_table, &node->hash, xmem);

            if (frequent->size > frequent->limit) {
                struct page_node *old_node = list_last_entry(&frequent->head, struct page_node, list);
                hash_del(&old_node->hash);
                list_del(&old_node->list);
                pmfs_flush_buffer(old_node->xmem, old_node->count, false);
                kmem_cache_free(page_node_cache, old_node);
                frequent->size--;
                result = 3; // recent->frequent evict
                goto ret;
            }
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
    hash_add(recent->hash_table, &new_node->hash, xmem);
    list_add(&new_node->list, &recent->head);
    recent->size++;
    if (recent->size > recent->limit) {
        struct page_node *old_node = list_last_entry(&recent->head, struct page_node, list);
        hash_del(&old_node->hash);
        list_del(&old_node->list);
        kmem_cache_free(page_node_cache, old_node);
        recent->size--;
        result = 0; // 1; FIXME: now it's counted as enter recent no evict but actually it's evicted. This is because we regard hotness=0 as cold data.
    }
ret:
    up_write(&my_rwsem);
#if DEBUG
    hotness_cnt[result]++;
    if (hotness_cnt[0] + hotness_cnt[1] + hotness_cnt[2] + hotness_cnt[3] + hotness_cnt[4] >= 100000) {
        // pmfs_dbg("hotness 0: %d, hotness 1: %d, hotness 2: %d, hotness 3: %d, hotness 4: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
        pmfs_dbg("enter recent no evict: %d, enter recent evict: %d, recent->frequent no evict: %d, recent->frequent evict: %d, frequent->frequent: %d\n", hotness_cnt[0], hotness_cnt[1], hotness_cnt[2], hotness_cnt[3], hotness_cnt[4]);
        hotness_cnt[0] = 0;
        hotness_cnt[1] = 0;
        hotness_cnt[2] = 0;
        hotness_cnt[3] = 0;
        hotness_cnt[4] = 0;
    }
#endif
    return result;
}


