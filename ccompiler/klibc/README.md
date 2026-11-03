# KLibc

Carl Kreider's standard C library for OS-9/6809, with later fixes and
enhancements. It is an independent replacement for the Microware C library
(`../lib/clib.l`), not its source. It uses the same calling convention, so
programs compiled with the Microware compiler link against either.

KLibc is a superset of the Microware library. It adds, among other things,
`patmatch`, `strucmp`, `strnucmp`, the `_gs_*`/`_ss_*` GetStat/SetStat
wrappers, `getopt`, `popen` and time conversion. Programs written against
it, such as Kreider's `ar` archiver, do not link against the Microware
library.

## Origin

Imported from `Source/Libs/KLibc` in
[CoCo C](https://github.com/DrPitre/CoCoC) at commit `c2102e1`
(2024-11-11). CoCo C also ships the library prebuilt as `Lib/clib.l`
(with `clibt.l`, the variant built with the transcendental maths package,
and `cstart.r`).

Changes from the CoCo C tree, so that it builds with the Microware
compiler (`cc1`) rather than CoCo C's `dcc`:

- The top `Makefile` passes `CC=cc1`, calls `kmake` for each part, defines
  `LIB` and creates the `rels` directories, which git does not keep.
- `lib.a` and `lib.c` compile with `cc1 -r`, which always writes the `.r`
  to the current directory, and move it into `RELs`. `lib.a`, `lib.c`,
  `imath`, `tmath` and `sys.a` have an `.a.r` rule that assembles into
  `RELs`.
- `lib.c/Makefile` defines `_OS9`, which CoCo C's `sys/machtype.h` sets, as
  `localtime.c` is otherwise empty, and names `time.r` where it had `time.c`.
- `defs/stdio.a` no longer selects sections with `ifge LWASM`. The Microware
  assemblers take that as true, so without this its fields came out as data
  offsets instead of constants. `cmoc.make` relied on it.
- `lib.a/iob_data.a` is in RMA syntax, where it had `lwasm`'s, as in c3's copy.
- `lib.a/ldexp.c` and `frexp.c` avoid `unsigned char`, which `cc1` lacks, and
  `ldexp.c` avoids `float.h`, whose long names collide in `c.prep`, which reads
  only 8 characters of a name.
- The `tmath` sources that need `mdefs.a` now `use` it, as c3's copies do, and
  `mdefs.a` and `dser.a` use RMA's `csect` and `rmb 0`, where they had `lwasm`'s
  forms.
- `sys.a/signal.a`, `chown.a` and `chmod.a` define the symbols they need again,
  which CoCo C's tree comments out.
- The assembler sources use the names the Microware tools produce, such as
  `errno`, `_iob` and `_mtop`, where they had the extra `_` of CoCo C's CMOC
  build, and `imath/clcommon.a` leaves `_flacc` to `cstart.a`, which also
  defines it.
- `defs` gains `float.h`, `stddef.h` and `password.h` from CoCo C's `Defs`,
  which the C sources include, and a `time.h` in K&R C for `cc1`, in place of
  CoCo C's, which uses function prototypes.

`lib.a/RELS` holds five relocatable objects (`scanf_c`, `qsort_c`,
`pffinit_c`, `l3tol_c` and `ltol3_c`) whose source is not in this tree;
the build merges them in as they are. c3's library (`../../c3/lib/lib.a`)
has source for all five: `qsort.c` and `pffinit.c` in C, and `scanf.a`,
`l3tol.a` and `ltol3.a` in assembler converted to c3's calling convention.
The `.old` and `.bak` files are earlier versions kept by the original tree.

## Layout

| Directory | Contents |
|-----------|----------|
| `lib.a`   | Strings, standard I/O, memory, character classes, GetStat/SetStat |
| `lib.c`   | Library routines written in C (time, `getopt`, `popen`, password file) |
| `sys.a`   | System-call wrappers and the C startup, `cstart.a` |
| `imath`   | Integer and long arithmetic runtime |
| `fmath`   | Floating-point runtime |
| `tmath`   | Transcendental functions (`clibt.l` only) |
| `defs`    | KLibc's extra headers |

## Building

The makefiles are for OS-9 and need Tim Kientzle's make (source in
`../make_src`), installed as `kmake` with its rules in
`/dd/sys/make.default`; the Tandy make that the C compiler installs as
`make` cannot read them. `cc1` has no include-directory option, so copy
`defs/*.h` into `/dd/defs` first. Only `time.h` has the name of a Microware
header, and it is a superset of that one, so it replaces it. Then, in this
directory:

    kmake

builds each part, then `clib.l` and `clibt.l` here and
`sys.a/rels/cstart.r`. `cc1` always links Microware's `cstart.r` and `clib.l`,
so link a program against KLibc with `rlink`, using KLibc's `cstart.r` and
`sys.l` for the OS-9 symbols (from CoCo C's `Lib`, and in `/dd/lib` on the
Pico-Thing mega images). `c.link` cannot read that `sys.l`, and `rlink` cuts a
`-l` path at 15 characters. Call `pflinit()` for `printf`'s `%ld`, as with the
Microware library.

    cc1 -r prog.c
    rlink <path>/sys.a/rels/cstart.r prog.r -l=<path>/clib.l -l=/dd/lib/sys.l -o=prog

The `GNUmakefile`s and `cmoc.make` are CoCo
C's cross builds and are not maintained here.
