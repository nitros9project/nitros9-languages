CFLAGS	= -s -DASMOPT -D_OS9
RDIR	= rels
RFILES	= prof.r pwent.r getopt.r adump.r defdrive.r popen.r \
 asctime.r ctime.r systime.r time.r localtime.r mktime.r isleap.r timevars.r
DFILES	= dbg.r getsp.r

cstuff.l: $(RFILES)
	-del cstuff.l
	cd rels;merge $(RFILES) >-../cstuff.l

dbg.l: $(DFILES) /dd/defs/dbg.h
	-del dbg.l
	merge rels/dbg.r rels/getsp.r >-dbg.l
#	copy -r dbg.l /dd/lib/dbg.l

clean:
	-del cstuff.l dbg.l RELs/*.r

# cc1 leaves the .r in the current directory, so move it into $(RDIR).
.c.r:
	$(CC) $(CFLAGS) -r $<
	-del $(RDIR/)$@
	copy $@ $(RDIR/)$@
	del $@

.a.r:
	$(RMA) $(RFLAGS) $< -o=$(RDIR/)$@
