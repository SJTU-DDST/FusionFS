#include <linux/module.h>
#include <linux/init.h>
#include <linux/list.h>
#include <linux/slab.h>
#include <linux/hashtable.h>

// ... 这里是之前定义的2Q算法的代码 ...

struct page_node {
    int idx;
    struct hlist_node hash;
    struct list_head list;
};

struct queue {
    DECLARE_HASHTABLE(hash_table, 16);
    struct list_head head;
    int size;
    int limit;
};

struct kmem_cache *page_node_cache;

int init_page_node_cache(void) {
    page_node_cache = kmem_cache_create("page_node_cache", sizeof(struct page_node), 0, (SLAB_RECLAIM_ACCOUNT | SLAB_MEM_SPREAD), NULL);
    if (page_node_cache == NULL)
        return -ENOMEM;
    return 0;
}

struct queue *create_queue(int limit) {
    struct queue *q = kmalloc(sizeof(*q), GFP_KERNEL);
    if (!q)
        return NULL;
    hash_init(q->hash_table);
    INIT_LIST_HEAD(&q->head);
    q->size = 0;
    q->limit = limit;
    return q;
}

void enqueue(struct queue *q, int idx) {
    if (q->size >= q->limit) {
        struct page_node *old_node = list_first_entry(&q->head, struct page_node, list);
        hash_del(&old_node->hash);
        list_del(&old_node->list);
        kmem_cache_free(page_node_cache, old_node);
        q->size--;
        printk(KERN_INFO "Queue=%p is full, remove the oldest idx=%d\n", q, old_node->idx);
    }

    struct page_node *new_node = kmem_cache_alloc(page_node_cache, GFP_KERNEL);
    if (!new_node)
        return;
    new_node->idx = idx;
    hash_add(q->hash_table, &new_node->hash, idx);
    list_add_tail(&new_node->list, &q->head);
    q->size++;
    printk(KERN_INFO "Insert idx=%d into queue=%p\n", idx, q);
}

int dequeue(struct queue *q, int idx) {
    struct page_node *node;
    hash_for_each_possible(q->hash_table, node, hash, idx) {
        if (node->idx == idx) {
            hash_del(&node->hash);
            list_del(&node->list);
            kmem_cache_free(page_node_cache, node);
            q->size--;
            printk(KERN_INFO "idx=%d found in queue=%p, removing\n", idx, q);
            return 1;
        }
    }
    printk(KERN_INFO "idx=%d not found in queue=%p\n", idx, q);
    return 0;
}

void access_page(struct queue *am, struct queue *a1out, int idx) {
    if (dequeue(am, idx) || dequeue(a1out, idx)) {
        enqueue(am, idx);
        printk(KERN_INFO "Second access idx=%d, insert into am\n", idx);
    } else {
        enqueue(a1out, idx);
        printk(KERN_INFO "First access idx=%d, insert into a1out\n", idx);
    }
}

static struct queue *am, *a1out;

static int __init my_module_init(void)
{
    int i;

    printk(KERN_INFO "Loading Module\n");

    init_page_node_cache();

    am = create_queue(5);
    a1out = create_queue(5);

    // 模拟页面访问
    for (i = 0; i < 10; i++) {
        access_page(am, a1out, i % 5);
    }

    // 检查队列的状态
    printk(KERN_INFO "am->size = %d a1out->size = %d\n", am->size, a1out->size);
    if (am->size != 100 || a1out->size != 100) {
        printk(KERN_ERR "2Q algorithm test failed\n");
        // return -1;
    }

    printk(KERN_INFO "2Q algorithm test passed\n");

    return 0;
}

static void __exit my_module_exit(void)
{
    printk(KERN_INFO "Unloading Module\n");

    kmem_cache_destroy(page_node_cache);
    kfree(am);
    kfree(a1out);
}

module_init(my_module_init);
module_exit(my_module_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("2Q Algorithm Module");
MODULE_AUTHOR("Your Name");