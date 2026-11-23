include $(NITROS9DIR)/rules.mak

# $(call files,patterns): the files matching the shell patterns, as
# $(wildcard) gives, less any name containing a space.  Such names are the
# "name 2.c" copies a synced folder (iCloud Drive, for one) leaves beside the
# real file; make would split one into words that name no file and stop with
# "No rule to make target".
files = $(shell for f in $(1); do \
          case "$$f" in (*' '*) ;; (*) test -e "$$f" && echo "$$f" ;; esac; \
        done)

DSK	= bf.dsk

SOURCEFILES := $(call files,*.bf)
TEXTFILES	= README.md $(SOURCEFILES)
OBJS		= bf
ALLOBJS		= $(OBJS)

.PHONY: all banner clean showobjs showfiles

all:	banner $(ALLOBJS) $(DSK)

banner:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*                    Brainf*ck                   *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"

bf: bf.asm
	$(AS) $(ASOUT)$@ $< $(AFLAGS) -DH6309=1

clean:
	$(RM) $(ALLOBJS) $(DSK) *.list *.map

$(DSK): Makefile $(ALLOBJS) $(TEXTFILES)
	$(RM) $@
	$(OS9FORMAT_SS35) $@ -n"bf"
	$(MAKDIR) $@,CMDS
	$(OS9COPY) $(ALLOBJS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(ALLOBJS),$@,CMDS/$(file))
	$(CPL) $(TEXTFILES) $@,.
	$(OS9ATTR_TEXT) $(foreach file,$(TEXTFILES),$@,$(file))

# Only $(CMDS) are shown here
showobjs:
	@$(ECHO) bf

# Only $(CMDS) are shown here
showfiles:
	@$(ECHO) $(SOURCEFILES)
