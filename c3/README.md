# C-Cubed (c3)

C-Cubed is a C compiler toolchain for the Motorola 6809 and NitrOS-9,
derived from the Microware C compiler. It builds as a host cross compiler
and can cross-build its own tools into OS-9 program modules.

The host pipeline is `c3prep` → `c3comp` → `c3optx` → `c3-as` → `c3-ld`.
The assembler and linker shims use LWTOOLS to produce OS-9 modules. The
compiler also has a two-pass mode using `c3comp1` and `c3comp2`.

## Requirements

- A Unix-like host with a C compiler, Make, a POSIX shell, `awk`, and `sed`.
- Git and Python 3.9 or later for the pinned canonical C library.
- LWTOOLS: `lwasm`, `lwar`, and `lwlink` on `PATH`.
- A NitrOS-9 checkout, with `NITROS9DIR` pointing to its root. The top-level
  Makefile includes `$NITROS9DIR/rules.mak`.
- For distribution disks: ToolShed's `os9` utility and a CoCo C checkout
  containing the Microware r-utils. See [the disk builder](build/os9/mkdsk.sh).

Commands below run from this directory.

## Build

```sh
export NITROS9DIR=/path/to/nitros9
make
```

The build runs in three stages, using the in-tree tools without requiring an
installed c3 toolchain:

| Target | Result |
| --- | --- |
| `make host` | Native host tools under `build/unix/` |
| `make runtime` | Host tools, startup objects, and runtime archives in `lwbackend/` |
| `make rma` | Runtime plus generated canonical RMA source/procedure under `.rma/` |
| `make os9` | Runtime plus OS-9 tools under `build/os9/` |
| `make` | OS-9 build; also creates `c3.dsk` when `COCOC` is set |
| `make clean` | Removes host, runtime, and OS-9 build outputs |

All C3 library builds and target headers come from
[nitros9-c-libs](https://github.com/nitros9project/nitros9-c-libs), pinned in
`nitros9-c-libs.revision`. The build fetches a clean checkout into
`lwbackend/nitros9-c-libs/`, compiles its canonical sources with C3, and generates
headers under `.libc/include/` (`defs` points there). No C library or integer/long
helpers are built from local library copies; those copies have been removed.
`lwbackend/libc3lw.a` contains only compiler-owned floating-point primitives; startup is compiler-owned as well.
`lwbackend/LIBC.json` records the canonical commit, source hashes, compiler hashes,
and archive hash. To use an existing clean checkout at that exact revision:

```sh
NITROS9_C_LIBS_DIR=/path/to/nitros9-c-libs make runtime
sh scripts/check-shared-library.sh
```

`make os9` also compiles the target compiler tools against these headers and
library. Each stage is checked separately; diagnostics cannot become a seemingly
valid empty object. The compiler tools use canonical time/file APIs and the
existing findstr substring primitive. This is a cross-build check, not proof
that the entire compiler self-hosts on an OS-9 machine.

The working optimizer is `c3optx`, built from `optexp/`. The older `opt/`
optimizer has missing sources and is excluded from the default build.

## Install the host cross compiler

A per-user install avoids needing administrator privileges:

```sh
make install PREFIX="$HOME/.local"
```

Ensure this setting is in your shell startup file (`~/.zshrc` for zsh):

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Programs, assembler/linker shims, and runtime files go in `$PREFIX/bin`.
Generated canonical target headers and their `LIBC.json` provenance go in
`$PREFIX/share/toolshed/defs`, including nested `sys/` headers. The installed `c3`
driver is rebuilt with the matching default header path. After pulling runtime
library changes, rerun `make install` with the same `PREFIX` so installed builds
link the updated `libc3.a`.

`PREFIX` defaults to `/usr/local`, which may require administrator privileges.
For packaging, `DESTDIR` stages the install without changing its compiled-in
destination:

```sh
make install PREFIX=/usr/local DESTDIR=/tmp/c3-package
```

The host executables are native programs; their compiled output is for
NitrOS-9, so it must run on a compatible target or emulator.

## Compile a program

After installing:

```sh
cat > hello.c <<'EOF'
#include <stdio.h>

int main(void)
{
    puts("Hello from c3!");
    return 0;
}
EOF

c3 hello.c -f=hello
```

This produces an OS-9 module named `hello`. When copying it onto an OS-9
disk, set its execute attributes; copying alone may leave it unexecutable.

Common options:

| Option | Purpose |
| --- | --- |
| `-a` | Generate assembly without assembling or linking |
| `-r` | Compile and assemble to relocatable `.r` objects |
| `-f=name` | Set the output filename |
| `-v=dir` | Add a preprocessor include directory |
| `-dNAME` | Define a preprocessor symbol |
| `-2` | Use the two-pass compiler |
| `-o` | Skip the optimizer |
| `-i` | Show the commands being executed |
| `-q` | Suppress stage names |

Run `c3` without arguments for the full option list. The host defaults to
the single-pass compiler; OS-9 defaults to the two-pass compiler.

To use the cross compiler directly from the source tree:

```sh
make runtime
export C3BASE="$PWD"
export PATH="$PWD/build/unix/exec:$PWD/build/unix/prep:$PWD/build/unix/comp:$PWD/build/unix/comp1:$PWD/build/unix/comp2:$PWD/build/unix/optx:$PWD/lwbackend:$PATH"
c3 hello.c -f=hello
```

`C3BASE` selects the directory containing `defs/`; unset it to use the
installed default. `C3_OPT`, `C3_ASM`, `C3_LINK`, `C3_COMP1`, and `C3_COMP2`
override stage commands. `C3LW_HOME` overrides where the assembler/linker
shims find their backend and runtime files.

### Floating point

Floating-point programs must opt into the MC6839 startup support:

```sh
c3 calc.c -l=fp.l -f=calc
```

The target needs the `FPO9` module resident or available as
`/DD/Modules/FPO9`. Without the floating-point library option, links use
the no-op startup object. See [the backend documentation](lwbackend/README.md)
for details and the in-tree `c3lw -f` alternative.

## Distribution disk and target checks

```sh
make dsk COCOC=/path/to/CoCoC
# Optionally include the MC6839 floating-point module:
make dsk COCOC=/path/to/CoCoC NFP09=/path/to/nfp09
```

`c3.dsk` contains the target tools, headers, sources, and library-build
procedure. `make ontarget COCOC=/path/to/CoCoC` checks library building and
program compilation on NitrOS-9 using `usim09pt` and a Pico-Thing Level 2
boot disk. See [ontarget.sh](build/os9/ontarget.sh) for setup requirements.

Host driver regression checks, with the freshly built tools on `PATH`:

```sh
sh lwbackend/tests/exitstatus.sh
sh lwbackend/tests/longpath.sh
sh lwbackend/tests/structdims.sh
```

The `structdims.sh` check exercises single-pass, two-pass, and experimental
(`c3compx`) compilation. The experimental check covers the known-structure
array case; that compiler cannot yet size arrays of pointers to incomplete tags.
It is only a reliable regression check for uninitialized dimension pointers
when the compiler is built with pattern-initialized automatic variables. A pass
from a normal build does **not** prove this bug is absent. With a host compiler
supporting `-ftrivial-auto-var-init=pattern`, clean and rebuild the relevant
stages first (from the `c3` directory):

```sh
for stage in comp comp1 comp2 compx; do
    make -C build/unix/$stage clean
    make -C build/unix/$stage CC="cc -ftrivial-auto-var-init=pattern" CPPFLAGS=-D_DEFAULT_SOURCE
done
sh lwbackend/tests/structdims.sh
```

The experimental `c3compx` copy shares the fix; `compexpansi` is kept in step
but is not currently built.

Target initialization and floating-point tests are documented in
[lwbackend/tests/README.md](lwbackend/tests/README.md). The two-pass backend
is still under development; not every program accepted by the single-pass
compiler works in two-pass mode.

## Source layout

| Directory | Contents |
| --- | --- |
| `exec/`, `prep/`, `comp/` | Driver, preprocessor, and compiler |
| `optexp/` | Working peephole optimizer |
| `build/unix/`, `build/os9/` | Host and OS-9 build rules and outputs |
| `lwbackend/` | LWTOOLS translation, linking, and runtime builders |
| `defs/` | Symlink to generated canonical target headers |
| `.libc/`, `.rma/` | Ignored generated canonical library outputs |
| `make/`, `lorder/`, `lsplit/` | Supporting build and library utilities |
| `test/`, `docs/` | Library test sources and reference documentation |

## RMA distribution

The RMA/rlink disk uses the same `nitros9-c-libs.revision`, generated headers,
and native ABI as the LWTOOLS build. There are no local C library or header
copies. `make rma` exports the canonical archive's exact member list as RMA
source, restores RMA initialized-data sections/relocations, and generates the
on-target `mklibs` procedure. It does not add runtime wrappers.

The disk builder stages those generated units under `C3/src/rma`, the exact
pinned canonical source under `C3/src/nitros9-c-libs`, and compiler sources under
`C3/src`. On OS-9, `shell <mklibs` assembles the prepared units and builds
`C3/lib/clib.l`; it requires RMA/rlink but no Python or Git. Preparing new library
sources requires the host build. Startup (`lwbackend/cstart.a`) and FP primitives
remain compiler-owned. `LIBC.json` on the disk records the canonical revision.

The canonical dependency also supplies full floating stdio, scanf/atof and math,
CGFX, terminal parameter expansion/ttytype lookup, environment files, legacy OS-9
calls, register-ABI assembler utilities, and debug tracing. The assembly bodies
remain in nitros9-c-libs. See [the companion port](https://github.com/nitros9project/nitros9-c-libs/pull/41)
and its migration manifest for source provenance and baseline-incomplete files.

Host and installed builds include `libc3f.a`, `libcgfx.a`, `libtermcap.a`,
`libalib.a`, and `libdbg.a` beside the compact `libc3.a`. Select them with
`-l=fp.l`/`-l=clibf.l`, `-l=cgfx.l`, `-l=termcap.l`, `-l=alib.l`, or `-l=dbg.l`.
Floating execution requires FPO9. The default printf float stub remains compact.
`alib` uses assembly register contracts, not C argument conventions.

On-target `mklibs` builds `clib.l`, `clibf.l`, `clibt.l`, `cgfx.l`, `termcap.l`,
`alib.l`, `dbg.l`, `fp.l`, and startup/system support. Use `clibf.l` for complete
floating stdio; `fp.l` also retains the historical `pffinit()` link anchor.
The original assembler-utility source is assembled directly to retain its
register ABI and dollar-symbol spellings. Other RMA units derive from the exact
canonical archive members, including direct-page storage and macro selection.
No compiler-local library source is restored.

RMA checks, after `make dsk COCOC=/path/to/CoCoC`:

```sh
python3 -m unittest discover -s scripts/tests
make rma
python3 scripts/check-rma-library.py --rma-dir .rma
BOOTDSK=/path/to/boot.dsk ROM=/path/to/rel_picothing.srec \
  USIM09PT=/path/to/usim09pt make ontarget COCOC=/path/to/CoCoC
```

The native kernel check validates every ROF member and runs the canonical ABI
probe with both optimizer settings, adding initialized data/code pointer and BSS
checks. `ontarget` also compiles and executes a hello program with the on-target
compiler. It changes only a scratch copy of the supplied boot image. Results,
console output, and RMA build logs remain in `$WORK` for inspection.

### Existing target-compiler limitation

The target compiler's `c3comp1` currently crashes while compiling the hello smoke
program (`PC=$004A`, invalid instruction). This was reproduced on a clean build
of main revision `140cb20127cb294373eaedaa05b9ff6a12d995a0`, before the library-copy
removal. Thus `make ontarget` currently fails at its compiler smoke check after
the two RMA library/ABI probes pass. The checker reports that failure.

To validate just the RMA library on a prepared disk:

```sh
python3 scripts/check-rma-runtime.py --disk c3.dsk \
  --boot-disk /path/to/boot.dsk --firmware /path/to/rel_picothing.srec \
  --emulator /path/to/usim09pt --out /tmp/c3-rma-check-new
```

Use a fresh output directory for each run. Add `--self-host` to include the
currently failing target-compiler smoke test. Add `--features` to run all migrated
feature probes at both optimization levels; build the distribution with
`FPO9=/path/to/Float09.bin` first. This test assembles and links on the actual
OS-9 kernel, independently of the host assembler bridge.
