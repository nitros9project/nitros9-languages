ifndef NITROS9DIR
NITROS9DIR := $(abspath ../nitros9)
endif

NITROS9_LANGUAGES_DIR := $(CURDIR)

export NITROS9DIR
export NITROS9_LANGUAGES_DIR

include $(NITROS9DIR)/rules.mak

dirs = basic09 bf ccompiler

all:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) &&) :

clean:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) clean &&) :

.PHONY: all clean
