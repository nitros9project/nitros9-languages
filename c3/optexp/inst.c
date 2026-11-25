#include "op.h"
#include <string.h>

DIRECT int      inscount;
int             insmax = MAXINS;
DIRECT chain    ilist;
DIRECT int      lbf,
                lbdone;
static DIRECT instruction *freeins;
static DIRECT int insused;

/* branch mnemonics */
char           *bratab[] = {
	"ra", "sr",
	"eq", "ne",
	"lt", "ge",
	"le", "gt",
	"lo", "hs",
	"ls", "hi",
	"pl", "mi",
	"cc", "cs",
	"vc", "vs",
};

#define NUMBRA ((sizeof bratab) / (sizeof (char *)))

char **srchmnem(char *mnemp, char **tblbeg, char **tblend)
{
	register char **nxtmnem;

	for (nxtmnem = tblbeg; nxtmnem < tblend; ++nxtmnem)
		if (strcmp(mnemp, *nxtmnem) == 0)
		{
			return nxtmnem;
		}
	return NULL;
}

void insinit(void)
{
	ilist.succ = ilist.pred = &ilist;
	inscount = 0;
	insused = 0;
	freeins = NULL;
}

instruction *insins(instruction *ins, char *mnem, char *args, label **l)
{
	register instruction *i;
	register label *lp;
	char           *mnemp,
	               *argp,
	              **mnemtp;
	int             argl;

	i = newins();

#ifdef DEBUG
	debug("insins: ");
	for (lp = (l ? *l : NULL); lp; lp = lp->nextl)
		debug("%s%s", lp->lname, lp->nextl ? "/" : "");
	debug(" %s %s\n", mnem, args);
#endif

	if ((i->llist = (l ? *l : NULL)) != 0)
	{
		for (lp = *l; lp; lp = lp->nextl)
			lp->dest = i;
		*l = NULL;
	}
	strcpy(i->mnem, mnem);
	if (*(argp = args))
		while (*++argp);
	argl = argp - args;

	i->succ = ins;
	i->pred = ins->pred;
#if 0
	((instruction *) ins->pred)->succ = i;
#else
	ins->pred->succ = i;
#endif
	ins->pred = i;
	++inscount;

	switch (*(mnemp = i->mnem))
	{
	case 'l':
		if (*++mnemp != 'b')
			break;
	case 'b':
		if ((mnemtp = srchmnem(mnemp + 1, bratab, bratab + NUMBRA)) != 0)
		{
			i->itype |= (BRANCH | LONG | (mnemtp - bratab));
			strcpy(i->mnem, *mnemtp);
			parse(LABEL, args, args, &argl);
			lp = findlabel(args);
			if (mnemtp == bratab)
			{
				if (lp && lp->dest)
					movlab(i, lp->dest);
				if (i->llist == NULL
				    && (chain *)i->pred != &ilist
#if 0
				    && (((instruction *) i->pred)->itype & CODEBRK))
#else
				    && (i->pred->itype & CODEBRK))
#endif
				{
					remins(i);
					++opsdone;
					return NULL;
				}
				i->itype |= CODEBRK;
			}
			++lbf;
			if (lp == NULL)
				lp = inslabel(args);
			i->itype |= DESTPTR;
			insref(i, i->alt.lab = lp);
		}
		break;
	case 'p':
		if (strcmp(mnemp, "puls") == 0
		    && strcmp(args + argl - 3, ",pc") == 0)
			i->itype |= CODEBRK;
		break;
	case 'r':
		if (strcmp(mnemp, "rts") == 0)
			i->itype |= CODEBRK;
		break;
	}
	if (!(i->itype & BRANCH))
		strcpy(i->alt.args = newarg(argl), args);
#ifdef DEBUG
	debug("inscount = %d, inserted: ", inscount);
	prtins(i);
#endif
	return i;
}

instruction    *newins(void)
{
	register instruction *i;

	if ((i = freeins) == NULL)
	{
		if (++insused > insmax + 3)
			error("run out of instructions", NULL, NULL, NULL);
		i = (instruction *)grab(sizeof(*i));
	}
	else
	{
		freeins = i->succ;
		i->itype = 0;
		i->alt.args = 0;
	}
	return i;
}

void insref(instruction *ip, label *lp)
{
	register chain *rlp;

	rlp = newchain();
	rlp->pred = (chain *)ip;
	rlp->succ = lp->rlist;
	lp->rlist = rlp;
}

void movlab(instruction *i1, instruction *i2)
{
	register label *l,
	               *lastl;

	if (i1 != i2 && (l = i1->llist))
	{
		do
		{
			lastl = l;
			l->dest = i2;
		} while ((l = l->nextl) != 0);
		lastl->nextl = i2->llist;
		i2->llist = i1->llist;
		i1->llist = NULL;
	}
}

/* Level II mode is an explicit promise that Y is zero.  Rewrite only
 * constant indexed addressing, never accumulator, indirect or auto-indexed
 * operands.  Run at emission so ordinary peepholes see their usual input.
 */
static int listed(char *name, char *list)
{
	char key[MNEMSIZE + 3];
	strcpy(key, " ");
	strcat(key, name);
	strcat(key, " ");
	return strstr(list, key) != NULL;
}

static int level2_y_written;

void level2reset(void)
{
	level2_y_written = 0;
}

/* Inline assembly shares this instruction stream.  Once Y may have changed,
 * keep its addressing intact for the rest of this program section. */
static int writes_y(char *mnem, char *args)
{
	char *p;

	if (listed(mnem, " ldy leay rti "))
		return 1;
	if (strstr(args, ",y+") || strstr(args, ",-y") || strstr(args, ",--y"))
		return 1;
	if (listed(mnem, " puls pulu "))
	{
		for (p = args; *p && *p != ' ' && *p != '\t'; ++p)
			if (*p == 'y' && (p == args || p[-1] == ',') &&
			    (!p[1] || p[1] == ',' || p[1] == ' ' || p[1] == '\t'))
				return 1;
	}
	if (listed(mnem, " tfr exg "))
	{
		p = strchr(args, ',');
		if (p && p[1] == 'y' && (!p[2] || p[2] == ' ' || p[2] == '\t'))
			return 1;
		if (!strcmp(mnem, "exg") && args[0] == 'y' && args[1] == ',')
			return 1;
	}
	return 0;
}

/* Recognize only literal five-bit offsets; do not evaluate expressions. */
static int small_offset(char *p, char *end)
{
	int negative = 0, base = 10, value = 0, digit;

	if (p == end)
		return 1;
	if (*p == '+' || *p == '-')
		negative = (*p++ == '-');
	if (p < end && *p == '$')
	{
		base = 16;
		++p;
	}
	if (p == end)
		return 0;
	while (p < end)
	{
		if (*p >= '0' && *p <= '9') digit = *p - '0';
		else if (*p >= 'a' && *p <= 'f') digit = *p - 'a' + 10;
		else if (*p >= 'A' && *p <= 'F') digit = *p - 'A' + 10;
		else return 0;
		if (digit >= base)
			return 0;
		value = value * base + digit;
		if (value > (negative ? 16 : 15))
			return 0;
		++p;
	}
	return 1;
}

static void level2(instruction *i, char *mnem, char *args)
{
	char *comma, *offset, *tail, *p;
	char result[ARGSIZE + 1];
	instruction *next;
	int lea;

	if (level2_y_written)
		return;
	comma = strchr(args, ',');
	if (!comma || comma[1] != 'y')
		return;
	tail = comma + 2;
	if (*tail && *tail != ' ' && *tail != '\t')
		return;
	offset = args;
	if (*offset == '>')
		++offset;
	/* Accept the expression alphabet emitted by c3; reject indexing syntax. */
	for (p = offset; p < comma; ++p)
		if (!((*p >= 'a' && *p <= 'z') || (*p >= 'A' && *p <= 'Z') ||
			  (*p >= '0' && *p <= '9') || strchr("_$+*/().-", *p)))
			return;
	if (comma - offset == 1 && strchr("aAbBdD", *offset))
		return;
	/* Zero and signed five-bit offsets are already smaller than extended
	 * memory addressing.  LEA-to-immediate retains its own flag check below. */
	lea = listed(mnem, " leax leas leau ");
	if (!lea && small_offset(offset, comma))
		return;
	if (lea)
	{
		next = (instruction *)i->succ;
		/* LD changes N/Z/V, whereas LEA preserves some or all of them.
		 * Only substitute if the next instruction overwrites all three
		 * before observing them.  Never look past a branch or call.
		 * The successor remains in the peephole window after this emission:
		 * future rules must preserve that flag overwrite.  Today's STD/LDD
		 * merge leaves a store, so it continues to overwrite N/Z/V. */
		if ((chain *)next == &ilist || (next->itype & BRANCH) ||
			!listed(next->mnem,
				" lda ldb ldd ldx ldy ldu lds sta stb std stx sty stu sts "
				" cmpa cmpb cmpd cmpx cmpy cmpu cmps "))
			return;
	}
	else if (!listed(mnem,
		" lda ldb ldd ldx ldy ldu lds sta stb std stx sty stu sts "
		" adda addb addd adca adcb suba subb subd sbca sbcb "
		" cmpa cmpb cmpd cmpx cmpy cmpu cmps anda andb ora orb eora eorb "
		" bita bitb neg com lsr ror asr asl lsl rol dec inc tst clr jmp jsr "))
		return;
	result[0] = lea ? '#' : '>';
	if (comma == offset)
	{
		result[1] = '0';
		result[2] = 0;
	}
	else
	{
		memcpy(result + 1, offset, comma - offset);
		result[1 + (comma - offset)] = 0;
	}
	strcat(result, tail);
	strcpy(args, result);
	if (lea)
	{
		mnem[2] = mnem[3];
		mnem[3] = 0;
		mnem[1] = 'd';
	}
}

void rminst(void)
{
	char mnem[MNEMSIZE + 1], args[ARGSIZE + 1];
	register instruction *i;
	label          *l;

	if ((chain *)(i = (instruction *)ilist.succ) == &ilist)
		error("removing too many instructions", NULL, NULL, NULL);

	if ((i->itype & LONGBRA) == LONGBRA)
		fix(i, FORWARD);
	if ((l = i->llist) != 0)
		fix(i, BACK);
	while (l)
	{
		fprintf(outf, "%s", l->lname);
		if (l->lflags & GLOBAL)
			putc(':', outf);
		if ((l = l->nextl) != 0)
			putc('\n', outf);
	}

	putc(' ', outf);
	if (i->itype & BRANCH)
	{
		fprintf(outf, "%sb%s %s", (i->itype & LONG ? "l" : ""), i->mnem,
		    (i->itype & DESTPTR ? i->alt.lab->lname : i->alt.args));
	}
	else
	{
		strcpy(mnem, i->mnem);
		strcpy(args, i->alt.args);
		if (level2flag)
		{
			level2(i, mnem, args);
			if (writes_y(i->mnem, i->alt.args))
				level2_y_written = 1;
		}
		fprintf(outf, "%s", mnem);
		if (args[0])
			fprintf(outf, " %s", args);
	}
	putc('\n', outf);
	remins(i);
}

void fix(instruction *i, int direction)
{
	register instruction *ip = i;
	instruction    *dp;
	label          *lp;
	int             c;

	if (direction == FORWARD)
	{
		lp = (ip->itype & DESTPTR ? ip->alt.lab : findlabel(ip->alt.args));
		if (lp && (dp = lp->dest))
		{
			for (c = BRALIM;
			   c && (ip = (instruction *) (ip->succ)) != (instruction *)&ilist;
			     --c)
			{
				if (dp == ip)
				{
#ifdef DEBUG
					debug("fix: ");
					prtins(i);
#endif
					ip->itype |= BLOCKDUP;
					i->itype &= ~LONG;
					++lbdone;
					return;
				}
			}
		}
	}
	else
	{
		for (c = BRALIM;
		     c && (chain *)(ip = ip->succ) != &ilist;
		     --c)
		{
			if ((ip->itype & LONGBRA) == LONGBRA)
			{
				lp = (ip->itype & DESTPTR) ? ip->alt.lab
					: findlabel(ip->alt.args);
				if (lp && i == lp->dest)
				{
#ifdef DEBUG
					debug("fix: ");
					prtins(ip);
#endif
					ip->itype &= ~LONG;
					++lbdone;
					return;
				}
			}
		}
	}
}

void remins(register instruction *i)
{
	register label *l;

#ifdef DEBUG
	debug("remins: ");
	prtins(i);
#endif
	if (i->itype & BRANCH)
	{
		remref(i, i->alt.lab);
	}
	else
		freearg((chain *)i->alt.args);
	for (l = i->llist; l; l = l->nextl)
	{			/* return labels */
		l->dest = NULL;
		freelabel(l);
	}
	/* remove instruction from the list */
	((instruction *) (i->pred))->succ = i->succ;
	((instruction *) (i->succ))->pred = i->pred;

	i->succ = freeins;
	freeins = i;

	--inscount;
}

void remref(instruction *ip, label *lp)
{
	chain          *rlp,
	               *lastrlp;

	if (lp)
	{
		lastrlp = (chain *) & lp->rlist;
		for (; (rlp = lastrlp->succ) != NULL; lastrlp = rlp)
			if (rlp->pred == (chain *)ip)
			{
				lastrlp->succ = rlp->succ;
				freelabel(lp);
				freechain(rlp);
				break;
			}
	}
}

static DIRECT chain *_cfree = NULL;

chain          *newchain(void)
{
	register chain *cp;

	if ((cp = _cfree) != NULL)
		_cfree = cp->succ;
	else
		cp = (chain *)grab(sizeof(chain));
	cp->succ = cp->pred = NULL;
	return cp;
}

void freechain(register chain *p)
{
	p->succ = _cfree;
	_cfree = p;
}

static DIRECT chain *safree = NULL,
               *lafree = NULL;

char           *newarg(int siz)
{
	register chain *ap;

	if (siz < 16)
		if ((ap = safree) != NULL)
			safree = ap->succ;
		else
			ap = (chain *)grab(16);
	else if ((ap = lafree) != NULL)
		lafree = ap->succ;
	else
		ap = (chain *)grab(ARGSIZE + 1);
	ap->succ = NULL;
	return (char *)ap;
}

void freearg(chain *p)
{
	register char  *sp;

	if ((sp = (char *)p) != NULL)
	{
		while (*sp)
			++sp;
		if (sp - (char *) p < 16)
		{
			p->succ = safree;
			safree = p;
		}
		else
		{
			p->succ = lafree;
			lafree = p;
		}
	}
}
