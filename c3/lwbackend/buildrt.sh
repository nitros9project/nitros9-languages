#!/bin/sh
# Only compiler-owned startup/FP primitives live here. Integer/long helpers
# and the C library come from nitros9-c-libs via buildlibc.sh.
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
out="$here/obj"
mkdir -p "$out"
lwasm --format=obj -o "$here/crt0.o" "$here/crt0.s"
for name in fpwrap fpdummy fpinit; do
    sed -f "$here/os9defs.sed" "$here/$name.a" > "$out/$name.rma"
    awk -f "$here/c3lw.awk" "$out/$name.rma" > "$out/$name.s"
    lwasm --format=obj -o "$out/$name.o" "$out/$name.s"
done
cp "$out/fpdummy.o" "$here/fpdummy.o"
cp "$out/fpinit.o" "$here/fpinit.o"
rm -f "$here/libc3lw.a"
lwar -c "$here/libc3lw.a" "$out/fpwrap.o"
