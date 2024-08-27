# SPDX-License-Identifier: GPL-2.0

CFLAGS = -g -Wall -O2 -D_FORTIFY_SOURCE=2 -D_GNU_SOURCE
CFLAGS += $(KHDR_INCLUDES)

LIBDIR ?= /home/congyong/intel-cmt-cat-23.11.1/lib
LDFLAGS += -L$(LIBDIR)
CFLAGS += -I$(LIBDIR)
LDLIBS += -lpqos

TEST_GEN_PROGS := resctrl_tests

include /home/congyong/Linux/tools/testing/selftests/lib.mk

$(OUTPUT)/resctrl_tests: $(wildcard *.[ch])
