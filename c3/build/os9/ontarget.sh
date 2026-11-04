#!/bin/sh
# ontarget.sh - check that the c3 distribution disk self-hosts on NitrOS-9.
#
# Boots NitrOS-9 Level 2 for the Pico-Thing under the usim09pt emulator, with
# the c3 distribution disk's tree laid over a throwaway copy of the boot disk
# (so it is /dd, the layout mkdsk.sh and mklibs expect), then:
#   boot 1: chx /dd/cmds; chd /dd/c3/src; shell <mklibs - build the C libraries
#   boot 2: chd /dd; c3 hello.c; hello                 - compile, link and run
# hello prints a line and exits with status 5, which the shell reports as
# "Error #005".  The check passes when both appear on the console.
#
# Needs:
#   - the c3 disk, from `make -C c3 dsk COCOC=...'
#   - usim09pt, the Pico-Thing build of USim (https://github.com/markrvmurray/usim)
#   - a NitrOS-9 checkout with the Pico-Thing Level 2 recipe built as an IDE
#     image plus its S-record boot ROM:
#       cd $NITROS9DIR/recipes/picothing/l2
#       make DSKIMAGE=NOS9_6809_L2_DEV_picothing_i0.dsk \
#           OS9FORMAT_CMD="os9 format -e -l65536"
#       make rel_picothing.srec
#   - toolshed's os9 on the PATH
#
# Override via the environment:
#   C3DSK     the c3 disk               (default c3/c3.dsk)
#   USIM09PT  the emulator              (default usim09pt on the PATH)
#   NITROS9DIR the NitrOS-9 checkout    (default ../nitros9 beside this repo)
#   BOOTDSK   the boot disk image       (default the recipe's IDE image above)
#   ROM       the boot ROM S-records    (default the recipe's rel_picothing.srec)
#   WORK      scratch directory, kept afterwards for inspection
#             (default a fresh mktemp directory)
#   TIMEOUT   emulator instruction limit per boot (default 6000000000)
#
# Each boot runs until its expected output appears or the emulator stops; the
# console logs are boot1.log and boot2.log in $WORK.
set -e

here=$(cd "$(dirname "$0")" && pwd)		# build/os9
c3=$(cd "$here/../.." && pwd)			# repo c3 root

C3DSK=${C3DSK:-$c3/c3.dsk}
USIM09PT=${USIM09PT:-usim09pt}
NITROS9DIR=${NITROS9DIR:-$(cd "$c3/../../nitros9" 2>/dev/null && pwd)}
RECIPE=$NITROS9DIR/recipes/picothing/l2
BOOTDSK=${BOOTDSK:-$RECIPE/NOS9_6809_L2_DEV_picothing_i0.dsk}
ROM=${ROM:-$RECIPE/rel_picothing.srec}
WORK=${WORK:-$(mktemp -d "${TMPDIR:-/tmp}/c3ontarget.XXXXXX")}
TIMEOUT=${TIMEOUT:-6000000000}

# ---- preflight --------------------------------------------------------------
[ -f "$C3DSK" ] || { echo "ontarget: no $C3DSK - run 'make -C c3 dsk COCOC=...'" >&2; exit 1; }
command -v "$USIM09PT" >/dev/null || { echo "ontarget: $USIM09PT not found - set USIM09PT" >&2; exit 1; }
command -v os9 >/dev/null || { echo "ontarget: toolshed's os9 not on the PATH" >&2; exit 1; }
for f in "$BOOTDSK" "$ROM"; do
	[ -f "$f" ] || { echo "ontarget: missing $f - build the Pico-Thing L2 recipe (see the header)" >&2; exit 1; }
done
mkdir -p "$WORK"
cd "$WORK"
echo "ontarget: working in $WORK"

# ---- the test disk: the boot disk with the c3 tree laid over it --------------
# dsave will not merge into an existing directory, so unpack the c3 disk to the
# host and copy it in: command modules one by one (keeping the boot disk's own),
# the text trees with dsave (already CR line ends, so no -l).
cp "$BOOTDSK" dd.dsk
rm -rf c3tree
mkdir c3tree
os9 dsave -e "$C3DSK," c3tree >/dev/null
for m in c3tree/CMDS/*; do
	b=$(basename "$m")
	os9 copy -r "$m" "dd.dsk,CMDS/$b"
	os9 attr -e -pe "dd.dsk,CMDS/$b" >/dev/null
done
os9 makdir dd.dsk,C3
for d in defs src; do
	os9 makdir "dd.dsk,C3/$d"
	os9 dsave -e -r "c3tree/C3/$d" "dd.dsk,C3/$d" >/dev/null
done
os9 makdir dd.dsk,C3/lib
for m in c3tree/Modules/*; do
	[ -f "$m" ] && os9 copy -r "$m" "dd.dsk,Modules/$(basename "$m")"
done

cat > hello.c <<'EOF'
#include <stdio.h>

int add(int a, int b)
{
	return a + b;
}

int main()
{
	printf("hello from c3, 2+3=%d\n", add(2, 3));
	return add(2, 3);
}
EOF
os9 copy -l hello.c dd.dsk,hello.c

# ---- boot <log> <console input> <pattern> -------------------------------------
# Run the emulator in the background, feeding the console after the login
# prompt is up (an empty user name logs in), and stop it once <pattern> is on
# the console or it ends by itself.  usim09pt never exits before its timeout.
boot() {
	"$USIM09PT" --timeout="$TIMEOUT" --input-first=78000000 --input-step=500000 \
	    --input="$2" -d dd.dsk "$ROM" > "$1" 2>&1 &
	pid=$!
	while kill -0 $pid 2>/dev/null; do
		if tr -d '\000' < "$1" | grep -aqE "$3"; then
			sleep 20			# let the disk writes land
			break
		fi
		sleep 5
	done
	kill $pid 2>/dev/null || true
	wait $pid 2>/dev/null || true
}

cr=$(printf '\r')

echo "ontarget: boot 1 - building the C libraries with mklibs (a few minutes)"
boot boot1.log "$cr$cr${cr}chx /dd/cmds${cr}chd /dd/c3/src${cr}shell <mklibs$cr" \
    'libraries built|POST-MORTEM'
if tr -d '\000' < boot1.log | grep -aqE 'error -|Unconditional Abort'; then
	echo "ontarget: FAIL - rma reported errors building the libraries (boot1.log)" >&2
	exit 1
fi
tr -d '\000' < boot1.log | grep -aq 'libraries built' || {
	echo "ontarget: FAIL - mklibs did not finish (boot1.log)" >&2
	exit 1
}

echo "ontarget: boot 2 - compiling and running hello.c"
boot boot2.log "$cr$cr${cr}chd /dd${cr}c3 hello.c${cr}hello$cr" \
    'Error #005|POST-MORTEM'
if tr -d '\000' < boot2.log | grep -aq 'hello from c3, 2+3=5' &&
   tr -d '\000' < boot2.log | grep -aq 'Error #005'; then
	echo "ontarget: PASS - c3 built its libraries and compiled a working program on NitrOS-9"
else
	echo "ontarget: FAIL - hello did not build or run as expected (boot2.log)" >&2
	exit 1
fi
