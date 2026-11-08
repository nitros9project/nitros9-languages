#include <math.h>

#define DBL_BIAS 128

/* c.prep reads 8 characters of a name, so float.h's DBL_MAX_EXP and
   DBL_MAX_10_EXP are one macro. */
#define MAX_BEXP 127
#define MIN_BEXP (-127)

#ifndef __DCC__
extern double _huge;

#asm
 vsect
_huge fdb 32767,-1,-1,-1 largest possible double
 endsect
#endasm
#endif	/* ! __DCC__ */

#asm
scalbn:
#endasm
double
ldexp (x, exp)
double x;
int exp;
{
	int i, neg;
	register char *cx = &x;

	neg = ((*cx & 0x80));	/* sign bit */
	cx += 7;				/* skip to exponent byte */
	i = (*cx & 0xff) - DBL_BIAS;		/* get the unbiased exponent */
	i += exp;

	if (i < MIN_BEXP) return 0.;
#ifndef __DCC__
	if (i > MAX_BEXP) return neg ? -_huge : _huge;
#else
	if (i > MAX_BEXP) return neg ? -HUGE_VAL : HUGE_VAL;
#endif

	*cx += exp;				/* set the new exponent */
	return x;
}
