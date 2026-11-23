# basic09-l2: a Basic09 editor, debugger and runtime for NitrOS-9 Level 2
# on the Wildbits computers (README.md).  It is a fork of
# ../../basic09/microware and does not change Basic09 or RunB.
#
# Each module is built here, in this directory, so that a recipe can ask
# for one: $(MAKE) -C $(LANGUAGES)/wildbits/basic09-l2 l2b09run

ifndef NITROS9DIR
NITROS9DIR := $(abspath ../../../nitros9)
endif
export NITROS9DIR

include $(NITROS9DIR)/rules.mak

# $(call files,patterns): the files matching the shell patterns, as
# $(wildcard) gives, less any name containing a space.  Such names are the
# "name 2.c" copies a synced folder (iCloud Drive, for one) leaves beside the
# real file; make would split one into words that name no file and stop with
# "No rule to make target".
files = $(shell for f in $(1); do \
          case "$$f" in (*' '*) ;; (*) test -e "$$f" && echo "$$f" ;; esac; \
        done)

PYTHON	?= python3

# The Basic09 source (forked from basic09/microware) and its build script
SRCDIR	= src
SCRIPT	= $(SRCDIR)/build-modular-basic09.py
SRCS	= $(addprefix $(SRCDIR)/,comand.asm compil.asm binder.asm stmts.asm \
	  exprsn.asm cnvio.asm defs b09defs b09type jmpdefs linkage editor \
	  pack mem)
DEPS	= Makefile $(SCRIPT) $(SRCS)
B09DEFS	= -DCOMMUNITY=1 -DLevel=2

# The editor and the help browser are 6809 only, and an undefined symbol
# is an error in them: no --6309 and no undefextern, unlike $(AS)
EDAS	= lwasm --no-warn=ifp1 --format=os9 \
	  --pragma=pcaspcr,nosymbolcase,condundefzero,dollarnotlocal,noforwardrefmax \
	  --includedir=$(DEFSDIR)
EDSRC	= $(call files,editor/*.asm)
HVSRC	= help/l2b09help.asm editor/term.asm editor/keys.asm

# A module over three 8K blocks needs a fourth slot, and l2b09run with far
# arrays then has no slot left for its data window
MAXSIZE	= 24576
SIZECHK	= @[ $$(wc -c < $@) -le $(MAXSIZE) ] || \
	  echo "WARNING: $@ is over $(MAXSIZE) bytes"

MODS	= l2b09run l2b09cc l2b09ovl runb-l2 basic09-l2 l2b09help farmem
ALLOBJS	= $(MODS) basic09-l2.hlp

.NOTPARALLEL:

.PHONY: all banner clean showobjs

all:	banner $(ALLOBJS)

banner:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*              basic09-l2 (Wildbits)             *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"

# The runtime: interpreter, commands and debugger, without the compiler
l2b09run: $(DEPS)
	$(PYTHON) $(SCRIPT) basic09 $@ $(B09DEFS) -DL2B09RT=1
	$(SIZECHK)

# The compiler, which l2b09run starts as a separate process
l2b09cc: $(DEPS)
	$(PYTHON) $(SCRIPT) basic09 $@ $(B09DEFS) -DL2B09CC=1
	$(SIZECHK)

# RunB built from this source (module name RunB), with far arrays
runb-l2: $(DEPS)
	$(PYTHON) $(SCRIPT) runb $@ $(B09DEFS)
	$(SIZECHK)

# The commands l2b09run loads when they are typed (PACK)
l2b09ovl: $(SRCDIR)/overlay.asm $(DEPS)
	$(AS) $(AFLAGS) $(B09DEFS) --includedir=$(SRCDIR) $< $(ASOUT)$@

# The editor
basic09-l2: $(EDSRC) defsfile
	$(EDAS) $(AFLAGS) --includedir=. --includedir=editor editor/basic09-l2.asm $(ASOUT)$@
	$(SIZECHK)

# The help browser: the editor's screen and key code; its size does not
# matter as the editor's does, so lwasm picks the branch lengths
l2b09help: $(HVSRC) defsfile
	$(EDAS) --pragma=autobranchlength $(AFLAGS) --includedir=. --includedir=editor \
	    help/l2b09help.asm $(ASOUT)$@

# The help pages; every Basic09 keyword and error must have one
basic09-l2.hlp: $(call files,help/*.txt) help/mkhelp.py $(SRCDIR)/comand.asm
	$(PYTHON) help/mkhelp.py --keytab $(SRCDIR)/comand.asm \
	    --errmsg $(NITROS9DIR)/level1/sys/errmsg -o $@ help

# Far memory for Basic09 programs (RUN farmem(...))
farmem: modules/farmem.asm defsfile
	$(AS) $(AFLAGS) --includedir=. $< $(ASOUT)$@

clean:
	$(RM) $(ALLOBJS) *.list *.map
	$(RM) -r .modular-build

showobjs:
	@$(ECHO) $(ALLOBJS)
