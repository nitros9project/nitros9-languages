/*
 * regcompare - a compare whose right side is already in a register.  After
 * "p != q", D still holds p, so the second test used to reach the compare
 * with D as its operand and stop with a false "dereference" error.
 *
 * Expected output:  001 01 001 01 01 1
 */
#include <stdio.h>

struct s {int a; char b[1];};
struct s g, h;
struct s *q;
int gi, *qi;

t1(p) struct s *p; { if (p != q && p != &g) return 1; return 0; }
t2(p) struct s *p; { if (p != q || p != &g) return 1; return 0; }
t3(p) struct s *p; { if (p != q && &g != p) return 1; return 0; }
t4(p) int *p; { if (p != qi && p != &gi) return 1; return 0; }
t5(p) struct s *p; { while (p != q && p != &g) return 1; return 0; }
t6(p) struct s *p; { if (p == q || p < &g) return 1; return 0; }

main()
{
	q = &h;
	qi = 0;
	printf("%d%d%d ", t1(&h), t1(&g), t1(q + 1));
	q = &g;
	printf("%d%d ", t2(&g), t2(&h));
	q = &h;
	printf("%d%d%d ", t3(&h), t3(&g), t3(q + 1));
	printf("%d%d ", t4(&gi), t4(qi + 1));
	printf("%d%d ", t5(&g), t5(q + 1));
	printf("%d\n", t6(q));
	exit(0);
}
