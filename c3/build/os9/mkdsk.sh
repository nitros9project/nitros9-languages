#!/bin/sh
# mkdsk.sh - build a complete c3-on-NitrOS-9 distribution disk image.
#
# Lays out, on one OS-9 image (the driver looks for C3/ on /dd, /h0, /d0, /j0):
#   CMDS/    the cross-built c3 tools  +  the Microware r-utils (rma rlink mold
#            rdump) that the on-target driver shells out to (ASMBNAME=rma,
#            LINKNAME=rlink); every module gets the OS-9 execute attribute.
#   C3/defs/ generated canonical nitros9-c-libs headers.
#   C3/lib/  empty; populated on first boot by `C3/src/mklibs` (build-on-target).
#   C3/src/  compiler + pinned canonical sources, generated RMA, and mklibs.
# defs, lib and src live under C3/ so that c3 can share a disk with the
# Microware C compiler, whose DEFS/ and LIB/ hold files of the same names.
#
# Text trees (defs, src) are copied with `os9 dsave -l` so the host's LF line
# endings become OS-9 CR; command modules are copied binary.
#
# Run from build/os9 (the makefile does `cd $(dir)` for the per-tool builds,
# but invokes this from build/os9 itself).  Override via the environment:
#   DSK     output image           (default c3tools.dsk, in build/os9)
#   DSKNAME OS-9 volume name        (default C3TOOLS)
#   LSECTORS flat OS-9 logical sectors (256B each; default 16384 = 4MB)
#   COCOC   CoCo C checkout (https://github.com/DrPitre/CoCoC.git); required,
#           supplies the r-utils rma rlink mold rdump in $COCOC/Cmds
#   NFP09   nfp09 checkout (https://github.com/markrvmurray/nfp09.git); supplies
#           the MC6839 FP module as $NFP09/ROM/Float09.bin
#   FPO9    the MC6839 FP module itself (default $NFP09/ROM/Float09.bin)
set -e

here=$(cd "$(dirname "$0")" && pwd)		# build/os9
c3=$(cd "$here/../.." && pwd)			# repo c3 root

DSK=${DSK:-$here/c3tools.dsk}
DSKNAME=${DSKNAME:-C3TOOLS}
LSECTORS=${LSECTORS:-16384}			# flat OS-9 logical sectors (256B); 4MB
FPO9=${FPO9:-${NFP09:+$NFP09/ROM/Float09.bin}}

# c3 command modules (built by the per-tool makefiles) -> CMDS
C3MODS="$here/exec/c3 $here/prep/c3prep $here/comp1/c3comp1 $here/comp2/c3comp2 \
        $here/optx/c3optx $here/lorder/lorder $here/lsplit/lsplit $here/make/make"
# Microware assembler / linker / librarian / ROF dumper -> CMDS
RUTILS="rma rlink mold rdump"

# ---- preflight --------------------------------------------------------------
for m in $C3MODS; do
	[ -f "$m" ] || { echo "mkdsk: missing $m - run 'make' first" >&2; exit 1; }
done
[ -n "$COCOC" ] || {
	echo "mkdsk: set COCOC to a CoCo C checkout" \
	     "(https://github.com/DrPitre/CoCoC.git; it ships rma/rlink/mold/rdump)" >&2
	exit 1
}
missing=
for u in $RUTILS; do
	[ -f "$COCOC/Cmds/$u" ] || missing="$missing $u"
done
[ -z "$missing" ] || {
	echo "mkdsk: r-utils not found in $COCOC/Cmds:$missing" >&2
	echo "mkdsk: set COCOC to a CoCo C checkout" \
	     "(https://github.com/DrPitre/CoCoC.git; it ships rma/rlink/mold/rdump)" >&2
	exit 1
}

# ---- format -----------------------------------------------------------------
echo "mkdsk: formatting $DSK ($LSECTORS logical sectors)"
rm -f "$DSK"
os9 format "$DSK" -e -l"$LSECTORS" -q -n"$DSKNAME"

# ---- CMDS: command modules (binary) + execute attribute ---------------------
echo "mkdsk: CMDS"
os9 makdir "$DSK,CMDS"
for m in $C3MODS; do
	b=$(basename "$m")
	os9 copy -r "$m" "$DSK,CMDS/$b"
	os9 attr -e -pe "$DSK,CMDS/$b"
done
for u in $RUTILS; do
	os9 copy -r "$COCOC/Cmds/$u" "$DSK,CMDS/$u"
	os9 attr -e -pe "$DSK,CMDS/$u"
done

# ---- stage the text trees (defs, src) into a temp, then dsave with -l --------
stage=$here/.diststage
rm -rf "$stage"

# Every distribution uses the pinned canonical headers and generated RMA units.
python3 "$c3/scripts/rma-library.py" --c3 "$c3" --out "$stage/src/rma"
mkdir -p "$stage/defs"
cp -R "$c3/.libc/include/." "$stage/defs/"
cp "$c3/include/rof.h" "$stage/defs/"
cp "$stage/src/rma/mklibs" "$stage/src/mklibs"
cp "$c3/lwbackend/LIBC.json" "$stage/defs/LIBC.json"

# Compiler sources and the exact canonical library source for inspection and
# regeneration on a host. The target only needs RMA; no Python is required there.
for d in prep comp optexp exec; do
    mkdir -p "$stage/src/$d"
    cp "$c3/$d"/*.c "$stage/src/$d/"
    cp "$c3/$d"/*.h "$stage/src/$d/" 2>/dev/null || true
done
lib_source=${NITROS9_C_LIBS_DIR:-$c3/lwbackend/nitros9-c-libs}
[ "$(git -C "$lib_source" rev-parse HEAD)" = "$(cat "$c3/nitros9-c-libs.revision")" ] || {
    echo 'mkdsk: canonical source revision mismatch; rebuild runtime' >&2; exit 1;
}
mkdir -p "$stage/src/nitros9-c-libs"
for d in lib include c3; do
    # git archive excludes generated build outputs and records only the pin.
    git -C "$lib_source" archive HEAD "$d" | tar -xf - -C "$stage/src/nitros9-c-libs"
done
cp "$c3/nitros9-c-libs.revision" "$stage/src/nitros9-c-libs/REVISION"

echo "mkdsk: C3/defs/ + C3/src/ (text, LF->CR)"
os9 makdir "$DSK,C3"
os9 dsave -l -e "$stage" "$DSK,C3"

# ---- lib: empty, filled in on-target by C3/src/mklibs -----------------------
os9 makdir "$DSK,C3/lib"

# ---- Modules: the MC6839 FP package, where the driver's F$Link/F$Load find it
os9 makdir "$DSK,Modules"
if [ -f "$FPO9" ]; then
	os9 copy -r "$FPO9" "$DSK,Modules/FPO9"
	echo "mkdsk: installed FPO9 (MC6839) -> Modules/"
else
	echo "mkdsk: WARNING: MC6839 module ${FPO9:-(NFP09 unset)} not found - set NFP09" \
	     "to an nfp09 checkout, or install FPO9 into Modules/ for FP" >&2
fi

rm -rf "$stage"
echo "mkdsk: done -> $DSK"
echo "  CMDS:    c3 c3prep c3comp1 c3comp2 c3optx lorder lsplit make + $RUTILS"
echo "  C3/defs: canonical nitros9-c-libs headers"
echo "  C3/src:  compiler + canonical library sources, generated RMA, mklibs"
echo "  C3/lib:  (build on-target:  chx /dd/cmds; chd /dd/c3/src; shell <mklibs)"
echo "  Modules: FPO9 (MC6839 floating point)"
