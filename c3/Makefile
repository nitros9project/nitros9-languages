include $(NITROS9DIR)/rules.mak

# c3 (C-Cubed) builds in three stages, each feeding the next:
#   host    - the compiler as host executables (build/unix), the cross compiler
#   runtime - crt0, the helper library and the C library (lwbackend), built
#             with the host compiler, lwasm and lwar
#   os9     - the compiler cross-built to OS-9 modules (build/os9), so it can
#             run on NitrOS-9 and rebuild itself there
# Everything uses the in-tree tools; nothing needs to be installed first.

HOSTDIR		= $(CURDIR)/build/unix
OS9DIR		= $(CURDIR)/build/os9
LWDIR		= $(CURDIR)/lwbackend

# Install location, shared with ToolShed's c3 install so the two agree:
# programs and the lwbackend runtime in $(PREFIX)/bin, headers in
# $(C3BASE)/defs.  DESTDIR is an optional staging root for packaging.
PREFIX		?= /usr/local
C3BASE		= $(PREFIX)/share/toolshed
BINDIR		= $(DESTDIR)$(PREFIX)/bin
C3DEFSDIR	= $(DESTDIR)$(C3BASE)/defs
INSTALL		?= install

# The host driver looks for its headers under $(C3BASE_DEFAULT)/defs when
# $C3BASE is unset; build it to find the installed ones.
HOSTFLAGS	= C3BASE_DEFAULT=$(C3BASE) CPPFLAGS="$(CPPFLAGS) -D_DEFAULT_SOURCE"
# Point the cross-build at the host stages and runtime built here, instead of
# an installed toolchain on the PATH.
OS9FLAGS	= C3BASE=$(CURDIR) C3LIBDIR=$(LWDIR) \
		  PREP=$(HOSTDIR)/prep/c3prep COMP=$(HOSTDIR)/comp/c3comp \
		  OPTX=$(HOSTDIR)/optx/c3optx

# The distribution disk needs the Microware r-utils (rma rlink mold rdump)
# from a CoCo C checkout, which is not part of this repository.  Without
# COCOC the tools are still built, but the disk is skipped.  NFP09 (an nfp09
# checkout) optionally supplies the MC6839 floating-point module.
DSK		= c3.dsk
COCOC		?=
NFP09		?=

.PHONY: all banner host runtime os9 dsk ontarget install clean

# Make all components
all:	banner os9
ifneq ($(COCOC),)
all:	$(DSK)
else
all:
	@$(ECHO) "c3: COCOC not set, skipping $(DSK) (see c3/Makefile)"
endif

banner:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*                  C-Cubed (c3)                  *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"

host:
	$(MAKE) -C $(HOSTDIR) all $(HOSTFLAGS)

runtime: host
	cd $(LWDIR) && sh buildrt.sh && sh buildlibc.sh

os9: runtime
	$(MAKE) -C $(OS9DIR) all $(OS9FLAGS)

dsk:	$(DSK)

$(DSK): os9
	DSK="$(CURDIR)/$@" DSKNAME="C3" COCOC="$(COCOC)" NFP09="$(NFP09)" \
	    sh $(OS9DIR)/mkdsk.sh

# Check the disk self-hosts: boot NitrOS-9 under usim09pt, build the C
# libraries on the target, then compile and run a program there.  See
# build/os9/ontarget.sh for what it needs (usim09pt and a built Pico-Thing
# Level 2 boot disk in the NitrOS-9 checkout).
ontarget: $(DSK)
	C3DSK="$(CURDIR)/$(DSK)" NITROS9DIR="$(NITROS9DIR)" sh $(OS9DIR)/ontarget.sh

# Install the host cross compiler.  The driver is re-linked first so its
# compiled-in header path matches this PREFIX, whatever it was built with.
# c3comp is the single-pass compiler (the driver's default); c3comp1 and
# c3comp2 are the two-pass front and back ends it uses for "c3 -2".  c3-as
# and c3-ld are the lwasm/lwlink shims the driver calls, and they find the
# runtime beside themselves.
install: runtime
	$(RM) $(HOSTDIR)/exec/c3.o $(HOSTDIR)/exec/c3
	$(MAKE) -C $(HOSTDIR)/exec $(HOSTFLAGS)
	$(INSTALL) -d $(BINDIR) $(C3DEFSDIR)
	$(INSTALL) $(HOSTDIR)/exec/c3 $(HOSTDIR)/prep/c3prep \
	    $(HOSTDIR)/comp/c3comp $(HOSTDIR)/comp1/c3comp1 \
	    $(HOSTDIR)/comp2/c3comp2 $(HOSTDIR)/optx/c3optx \
	    $(HOSTDIR)/lorder/lorder $(HOSTDIR)/lsplit/lsplit \
	    $(LWDIR)/c3-as $(LWDIR)/c3-ld $(LWDIR)/c3lw $(BINDIR)
	$(INSTALL) -m 0644 $(LWDIR)/c3lw.awk $(LWDIR)/os9c3.ld \
	    $(LWDIR)/crt0.o $(LWDIR)/fpdummy.o $(LWDIR)/fpinit.o \
	    $(LWDIR)/libc3.a $(LWDIR)/libc3lw.a $(BINDIR)
	cp -R .libc/include/. $(C3DEFSDIR)/
	$(INSTALL) -m 0644 $(LWDIR)/LIBC.json $(C3DEFSDIR)/LIBC.json

# Clean all components
clean:
	$(MAKE) -C $(HOSTDIR) clean
	$(MAKE) -C $(OS9DIR) clean
	$(RM) -r $(LWDIR)/obj $(CURDIR)/.libc
	$(RM) $(LWDIR)/crt0.o $(LWDIR)/fpdummy.o $(LWDIR)/fpinit.o \
	    $(LWDIR)/libc3.a $(LWDIR)/libc3lw.a $(DSK)
