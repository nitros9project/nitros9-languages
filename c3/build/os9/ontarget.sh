#!/bin/sh
# Assemble the canonical RMA library and run ABI + target-compiler probes.
# Boot media and tools are supplied by the caller; only a scratch disk is changed.
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
c3=$(CDPATH= cd -- "$here/../.." && pwd)
C3DSK=${C3DSK:-$c3/c3.dsk}
USIM09PT=${USIM09PT:-usim09pt}
: "${NITROS9DIR:?Set NITROS9DIR to the NitrOS-9 checkout}"
RECIPE=$NITROS9DIR/recipes/picothing/l2
BOOTDSK=${BOOTDSK:-$RECIPE/NOS9_6809_L2_DEV_picothing_i0.dsk}
ROM=${ROM:-$RECIPE/rel_picothing.srec}
WORK=${WORK:-$(mktemp -d "${TMPDIR:-/tmp}/c3ontarget.XXXXXX")}
WALL_SECONDS=${WALL_SECONDS:-180}
exec python3 "$c3/scripts/check-rma-runtime.py" --disk "$C3DSK" \
    --boot-disk "$BOOTDSK" --firmware "$ROM" --emulator "$USIM09PT" \
    --out "$WORK" --wall-seconds "$WALL_SECONDS" --self-host
