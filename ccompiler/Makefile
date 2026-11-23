include $(NITROS9DIR)/rules.mak

# $(call files,patterns): the files matching the shell patterns, as
# $(wildcard) gives, less any name containing a space.  Such names are the
# "name 2.c" copies a synced folder (iCloud Drive, for one) leaves beside the
# real file; make would split one into words that name no file and stop with
# "No rule to make target".
files = $(shell for f in $(1); do \
          case "$$f" in (*' '*) ;; (*) test -e "$$f" && echo "$$f" ;; esac; \
        done)

DSK		= CCompiler.dsk
CMDS		= cc1 cc2 c.prep c.pass1 c.pass2 c.comp c.opt c.asm c_asm c.link make
HEADERS		= $(call files,defs/*.h)
LIBRARIES	= $(call files,lib/*.l lib/*.r)
# rd.c is a host-side maintainer tool (a modern-machine port of rdump.c that
# reads big-endian OS-9 ROF files); it is compiled for this build host and is
# deliberately not installed on the 6809, so keep it out of the sources copied
# onto the disk image.  The disk carries the 6809 rdump.c source instead.
C_SOURCES	= $(filter-out sources/rd.c,$(call files,sources/*.c))
HOSTCC		= cc
HOSTCFLAGS	= -O2 -Wall
ASM_SOURCES	= $(call files,sources/*.a)
SYS_SOURCES	= $(call files,sources/*.sys)

# Help entries for the OS-9 "help" utility, one per compiler command.  They
# are merged (cat) into a single "helpmsg" file that "help" reads from
# /DD/SYS/helpmsg.  cc1 is listed first so it heads the topic list.
HELPFILES	= sys/cc1.hp sys/cc2.hp sys/cprep.hp sys/cpass1.hp \
		sys/cpass2.hp sys/ccomp.hp sys/copt.hp sys/casm.hp sys/clink.hp
HELPMSG		= helpmsg

# Most compiler modules share the C runtime startup, which lives in lib/ and
# is pulled into each with "use lib/cstart.asm" (make keeps its own variant
# via cstart_rev.asm; c.asm is a copy of c_asm).  Validate the lib first, and
# rebuild the sharing modules when cstart.asm changes.
CSTARTMODS	= cc1 cc2 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules that share the full-width runtime multiply from lib/imul.asm
# (all of them carry the same MulFull the C runtime falls into).
IMULMODS	= cc1 cc2 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link make

# Modules that share the word shift runtime from lib/shift.asm.
SHIFTMODS	= cc1 cc2 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link make

# Modules that share the integer divide runtime from lib/divide.asm.
DIVMODS		= c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules that share the string-copy runtime from lib/strcpy.asm.
STRCPYMODS	= cc1 c.prep c.opt c_asm c.link

# Modules that share the string-concatenate runtime from lib/strcat.asm.
STRCATMODS	= cc1 c.prep c.opt c.link

# Modules that share the string-length runtime from lib/strlen.asm.
STRLENMODS	= c.opt c.link

# Modules that share the string-compare runtime from lib/strcmp.asm.
STRCMPMODS	= cc1 c.pass2 c.link

# Modules that use the counted string-copy runtime from lib/strncpy.asm.
STRNCPYMODS	= c.link

# Modules that use the counted string-compare runtime from lib/strncmp.asm.
STRNCMPMODS	= c.link

# Modules that use the counted string-concatenate runtime from lib/strncat.asm.
STRNCATMODS	= c.link

# Modules that use the memory-copy runtime from lib/memcpy.asm.
MEMCPYMODS	= c_asm

# Modules that share the buffered-stream flush runtime from lib/flushbuffer.asm.
# Each supplies its own helper names (FileTell/SeekFile/WriteLnPath/WritePath)
# and flush entry/exit labels via equ aliases after the use.
FLUSHBUFMODS	= cc1 c.pass1 c.pass2 c.comp c.link

# Modules that share the write syscall wrappers from lib/writepath.asm.
# Each supplies its own entry names via aliases (SyscallErr comes from lib).
WRITEPATHMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules that share the syscall error/return tails from lib/syscallerr.asm.
# Each supplies its own tail names and errno cell (Errno) via aliases.
SYSCALLERRMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules that share the open/close/delete path wrappers from lib/.
# Each points its own call name at the canonical entry via an equ alias.
PATHOPSMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules that share the raw/line read wrappers from lib/readpath.asm.
# Each points its own call names at ReadPath/ReadLnPath via equ aliases.
READPATHMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules that share the create-file tail from lib/createtail.asm.  Each
# keeps its own create prologue and falls into the shared CreateOk tail;
# the "already exists" reopen/truncate fallback is identical for all.
CREATETAILMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules sharing the create prologues: A = fixed attribute byte, B =
# attribute computed from the requested mode.  (c.link keeps its own
# exec-preserving prologue and shares neither.)
CREATEHEADAMODS	= cc1 c.prep c_asm
CREATEHEADBMODS	= c.pass1 c.pass2 c.comp c.opt

# Leaf C-runtime wrappers: setstat/access in every module, getstat in
# the six that carry it (c.prep and c_asm use a different getstat form).
SETSTATMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link
GETSTATMODS	= cc1 c.pass1 c.pass2 c.comp c.opt c.link
ACCESSMODS	= cc1 c.prep c.pass1 c.pass2 c.comp c.opt c_asm c.link

# Modules sharing lseek from lib/seek.asm.  Each aliases its own
# long-value staging cells onto HighResultWord/LowResultWord (c.link
# names them so; c.prep and c_asm keep their own variant seek).
SEEKMODS	= cc1 c.pass1 c.pass2 c.comp c.opt c.link

# fclose (cc1/c.link) and fflush (c.opt/c_asm) share a routine each; the
# other modules carry variant forms.  Each aliases its differently-named
# buffer/flush helper.
FCLOSEMODS	= cc1 c.link
FFLUSHMODS	= c.opt c_asm

.PHONY: all banner clean lib

# Make all components
all:	banner lib $(CMDS) rd $(DSK)

banner:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*                    C Compiler                  *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"

lib:
	$(MAKE) -C lib

$(CSTARTMODS): lib/cstart.asm
$(IMULMODS): lib/imul.asm
$(SHIFTMODS): lib/shift.asm
$(DIVMODS): lib/divide.asm
$(STRCPYMODS): lib/strcpy.asm
$(STRCATMODS): lib/strcat.asm
$(STRLENMODS): lib/strlen.asm
$(STRCMPMODS): lib/strcmp.asm
$(STRNCPYMODS): lib/strncpy.asm
$(STRNCMPMODS): lib/strncmp.asm
$(STRNCATMODS): lib/strncat.asm
$(MEMCPYMODS): lib/memcpy.asm
$(FLUSHBUFMODS): lib/flushbuffer.asm
$(WRITEPATHMODS): lib/writepath.asm
$(SYSCALLERRMODS): lib/syscallerr.asm
$(PATHOPSMODS): lib/openpath.asm lib/closepath.asm lib/deletepath.asm
$(READPATHMODS): lib/readpath.asm
$(CREATETAILMODS): lib/createtail.asm
$(CREATEHEADAMODS): lib/createheada.asm
$(CREATEHEADBMODS): lib/createheadb.asm
$(SETSTATMODS): lib/setstat.asm
$(GETSTATMODS): lib/getstat.asm
$(ACCESSMODS): lib/access.asm
$(SEEKMODS): lib/seek.asm
$(FCLOSEMODS): lib/fclose.asm
$(FFLUSHMODS): lib/fflush.asm
make: lib/cstart_rev.asm

# Merge the per-command help entries into one helpmsg file
$(HELPMSG): $(HELPFILES)
	$(MERGE) $(HELPFILES) > $@

# Clean all components
clean:
	$(MAKE) -C lib clean
	$(RM) $(CMDS) rd $(DSK) $(HELPMSG) *.list *.map

c.asm: c_asm
	$(CP) $< $@

# rd is the host build of the ROF dumper (sources/rd.c).  It runs on the build
# machine to inspect .r/.l files and is intentionally not copied to the disk;
# the 6809 carries rdump.c as source instead.
rd: sources/rd.c
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $<

# cc2 is cc1 built for the single-pass c.comp front end (it invokes c.comp
# instead of c.pass1 + c.pass2); selected in cc1.asm with -DCC2=1.
cc2: cc1.asm
	$(AS) $(AFLAGS) -DCC2=1 $< $(ASOUT)$@

$(DSK): Makefile $(CMDS) $(HEADERS) $(LIBRARIES) $(C_SOURCES) \
	$(ASM_SOURCES) $(SYS_SOURCES) $(HELPMSG)
	$(RM) $@
	$(OS9FORMAT_DS40) -q $@ -n"C Compiler"
	$(MAKDIR) $@,CMDS
	$(MAKDIR) $@,LIB
	$(MAKDIR) $@,DEFS
	$(MAKDIR) $@,SYS
	$(MAKDIR) $@,SOURCES
	$(MAKDIR) $@,SOURCES/SYS
	$(OS9COPY) $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(CPL) $(HEADERS) $@,DEFS
	$(OS9COPY) $(LIBRARIES) $@,LIB
	$(CPL) $(HELPMSG) $@,SYS/helpmsg
	$(CPL) $(C_SOURCES) $@,SOURCES
	$(CPL) $(ASM_SOURCES) $(SYS_SOURCES) $@,SOURCES/SYS
