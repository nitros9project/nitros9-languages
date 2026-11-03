RFILES1 = lib.c/cstuff.l lib.a/main.l
RFILE_F	= fmath/cfloats.l
RFILE_T	= tmath/trans.l
RFILES2	= imath/math.l sys.a/syslib.l
MAKEFLAGS	= CC=cc1 RMA=c.asm
LIB	= /dd/lib

dummy: #dummy1
	-makdir lib.c/rels
	-makdir imath/rels
	-makdir tmath/rels
	-makdir sys.a/rels
	chd lib.c;kmake $(MAKEFLAGS)
	chd lib.c;kmake $(MAKEFLAGS) dbg.l
	chd lib.a;kmake $(MAKEFLAGS)
	chd fmath;kmake $(MAKEFLAGS)
	chd tmath;kmake $(MAKEFLAGS)
	chd imath;kmake $(MAKEFLAGS)
	chd sys.a;kmake $(MAKEFLAGS)
	chd sys.a;kmake $(MAKEFLAGS) cstart.r
	kmake $(MAKEFLAGS) clib.l
	kmake $(MAKEFLAGS) clibt.l

clean:
	cd lib.c; kmake $(MAKEFLAGS) clean
	cd lib.a; kmake $(MAKEFLAGS) clean
	cd fmath; kmake $(MAKEFLAGS) clean
	cd imath; kmake $(MAKEFLAGS) clean
	cd tmath; kmake $(MAKEFLAGS) clean
	cd sys.a; kmake $(MAKEFLAGS) clean
	-del clib.l
	-del clibt.l

clib.l: $(RFILES1) $(RFILE_F) $(RFILES2)
	-del clib.l
	merge $(RFILES1) $(RFILE_F) $(RFILES2) >clib.l
#	cp clib.l /dd/m6809/lib

clibt.l: $(RFILES1) $(RFILE_T) $(RFILES2)
	-del clibt.l
	merge $(RFILES1) $(RFILE_T) $(RFILES2) >clibt.l
#	cp clibt.l /dd/m6809/lib

install: clib.l clibt.l
	copy -rw=$(LIB) clib.l clibt.l
