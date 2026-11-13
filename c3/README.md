# C-Cubed (c3)

C-Cubed is a C compiler toolchain for the Motorola 6809 and NitrOS-9,
derived from the Microware C compiler. It builds as a host cross compiler
and can cross-build its own tools into OS-9 program modules.

The host pipeline is `c3prep` → `c3comp` → `c3optx` → `c3-as` → `c3-ld`.
The assembler and linker shims use LWTOOLS to produce OS-9 modules. The
compiler also has a two-pass mode using `c3comp1` and `c3comp2`.

## Requirements

- A Unix-like host with a C compiler, Make, a POSIX shell, `awk`, and `sed`.
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
| `make os9` | Runtime plus OS-9 tools under `build/os9/` |
| `make` | OS-9 build; also creates `c3.dsk` when `COCOC` is set |
| `make clean` | Removes host, runtime, and OS-9 build outputs |

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
Target headers go in `$PREFIX/share/toolshed/defs`. The installed `c3`
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
```

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
| `defs/`, `lib/` | Target headers and C library sources |
| `make/`, `lorder/`, `lsplit/` | Supporting build and library utilities |
| `test/`, `docs/` | Library test sources and reference documentation |
