#include "cache.h"

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

static void enqueue(struct queue *q, u64 hash_key) {
    if (q->size >= q->limit) {
        struct page_node *old_node = list_first_entry(&q->head, struct page_node, list);
        hash_del(&old_node->hash);
        list_del(&old_node->list);
        kmem_cache_free(page_node_cache, old_node);
        q->size--;
        // pr_info("Queue=%p is full, remove the oldest hash_key=%llu\n", q, old_node->inode_number, old_node->file_index);
    }

    struct page_node *new_node = kmem_cache_alloc(page_node_cache, GFP_KERNEL);
    if (!new_node) {
        pr_err("Failed to allocate memory for new_node\n");
        return;
    }
    new_node->hash_key = hash_key;
    // hash_key = ((u64)inode_number << 32) | file_index;
    hash_add(q->hash_table, &new_node->hash, hash_key);
    list_add_tail(&new_node->list, &q->head);
    q->size++;
    // // pr_info("Insert hash_key=%llu into queue=%p, size=%d\n", hash_key, q, q->size);
}

static int dequeue(struct queue *q, u64 hash_key) { // TODO: make it thread-safe
    struct page_node *node;
    // u64 hash_key = ((u64)inode_number << 32) | file_index;
    hash_for_each_possible(q->hash_table, node, hash, hash_key) {
        if (node->hash_key == hash_key) {
            hash_del(&node->hash);
            list_del(&node->list);
            kmem_cache_free(page_node_cache, node);
            q->size--;
            // pr_info("hash_key=%llu found in queue=%p, removing\n", hash_key, q);
            return 1;
        }
    }
    // pr_info("hash_key=%llu not found in queue=%p\n", hash_key, q);
    return 0;
}

int pmfs_page_hotness(u64 hash_key) {
    if (dequeue(am, hash_key) || dequeue(a1out, hash_key)) {
        enqueue(am, hash_key);
        // pr_info("Second access hash_key=%llu, insert into am\n", hash_key);
        return 1;
    } else {
        enqueue(a1out, hash_key);
        // pr_info("First access hash_key=%llu, insert into a1out\n", hash_key);
        return 0;
    }
}


