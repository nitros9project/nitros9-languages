# NitrOS-9 Languages

This repository contains programming languages, compilers, and related tools
for [NitrOS-9](https://github.com/nitros9project/nitros9).

## Contents

- `basic09` — Microware BASIC09 and RunB sources, utilities, and samples
- `bf` — Brainf*ck interpreter and sample programs
- `ccompiler` — Microware C compiler, libraries, headers, and sources, and
  the source of Carl Kreider's compatible C library, KLibc (`ccompiler/klibc`)
- `c3` — C-Cubed, a portable C compiler derived from the Microware one; it
  runs on the build host as a cross compiler and on NitrOS-9 itself
- `pascal` — archival Pascal materials

The Microware source in `basic09/microware` is the authoritative source for
the BASIC09 and RunB modules. Generated or separately disassembled versions
are not maintained as competing sources.

## Building

A neighboring NitrOS-9 checkout is used by default:

```sh
make
```

Set `NITROS9DIR` when the NitrOS-9 checkout is elsewhere:

```sh
make NITROS9DIR=/path/to/nitros9
```

The default target builds BASIC09, Brainf*ck, the C compiler, and c3,
including their disk images. The BASIC09 disk is based on the CoCo 3 floppy
recipe in the NitrOS-9 checkout. Use `make clean` to remove generated modules
and disk images.

c3 also needs a host C compiler. It is built first as host executables,
then used to cross-build itself to OS-9 modules. Its disk image also needs
the Microware assembler and linker from a
[CoCo C](https://github.com/DrPitre/CoCoC) checkout. Without one, the c3
tools are still built but the disk is skipped:

```sh
make COCOC=/path/to/CoCoC
```

`make -C c3 ontarget COCOC=/path/to/CoCoC` checks that the disk self-hosts:
it boots NitrOS-9 under the `usim09pt` emulator, builds c3's C libraries on
the target, and compiles and runs a program there. `c3/build/os9/ontarget.sh`
lists what it needs.

The Pascal material is retained for reference and is not part of the
aggregate build.

## Source and licensing

These packages were migrated from the NitrOS-9 `3rdparty/packages` tree.
They retain their original source notices, documentation, and licensing
terms. No repository-wide license is asserted over packages that do not
already include one.
