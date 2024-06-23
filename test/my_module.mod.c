#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x30520a2b, "module_layout" },
	{ 0x37a0cba, "kfree" },
	{ 0xd5ac1d1b, "kmem_cache_destroy" },
	{ 0xc5850110, "printk" },
	{ 0x69b31010, "kmem_cache_free" },
	{ 0x9f6d2732, "kmem_cache_alloc" },
	{ 0xfb578fc5, "memset" },
	{ 0xb8b9f817, "kmalloc_order_trace" },
	{ 0xaabef526, "kmem_cache_create" },
	{ 0xbdfb6dbb, "__fentry__" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "922F18A8529D45C2AF104FD");
