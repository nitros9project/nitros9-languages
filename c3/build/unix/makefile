# NOTE: "opt" (the original optimiser) is intentionally excluded from the
# default build.  Its source directory is incomplete: inst.c -- which defines
# the instruction-list routines (remove, insins, insref, newins, insinit, ...)
# -- is absent from the tree, so opt cannot link (its own makefile already
# comments inst.o out of OBJS).  It also #includes the non-existent
# ../rma/ctype.h.  The complete, working optimiser is "optx" (built from the
# optexp/ sources), which is included below.  To work on opt, build it directly
# with "make -C build/unix/opt" once inst.c has been restored.
dirs	= exec prep comp comp1 comp2 compx optx lorder lsplit make

# This is the c3-only BUILD tree (all / clean).  Installation is owned by
# c3/Makefile, which installs the host tools along with the lwasm/lwlink back
# end and its runtime (to $(PREFIX)/bin) and the preprocessor headers (to
# $(PREFIX)/share/toolshed/defs), with DESTDIR staging.  Keeping one installer
# avoids the two diverging.

# Make all components
all:
	@echo "**************************************************"
	@echo "*                                                *"
	@echo "*               MW C Compiler                    *"
	@echo "*                                                *"
	@echo "**************************************************"
	@set -e; for dir in $(dirs); do $(MAKE) -C $$dir; done

# Clean all components
clean:
	@set -e; for dir in $(dirs); do $(MAKE) -C $$dir clean; done

# Installation lives in c3/Makefile (see note above).
install dist package uninstall:
	@echo "c3 is installed by c3/Makefile, not here."
	@echo "Run:  make -C ../.. install      (honours PREFIX and DESTDIR)"
	@false
