#!/bin/sh
# Resolve the canonical libc checkout. Sourced by the runtime build scripts.
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
c3=$(CDPATH= cd -- "$here/.." && pwd)
lib_revision=$(cat "$c3/nitros9-c-libs.revision")
lib_source=${NITROS9_C_LIBS_DIR:-$here/nitros9-c-libs}
if [ -z "${NITROS9_C_LIBS_DIR:-}" ]; then
    if [ ! -e "$lib_source/.git" ]; then
        mkdir -p "$lib_source"
        git -C "$lib_source" init >&2
        git -C "$lib_source" remote add origin https://github.com/nitros9project/nitros9-c-libs.git
    fi
    [ -z "$(git -C "$lib_source" status --porcelain --untracked-files=no)" ] || {
        echo 'Canonical libc checkout has local changes' >&2; exit 1;
    }
    if ! git -C "$lib_source" cat-file -e "$lib_revision^{commit}" 2>/dev/null; then
        git -C "$lib_source" fetch --depth 1 origin "$lib_revision" >&2
    fi
    git -C "$lib_source" checkout --detach "$lib_revision" >&2
fi
[ "$(git -C "$lib_source" rev-parse HEAD)" = "$lib_revision" ] || {
    echo "Canonical libc revision mismatch; expected $lib_revision" >&2; exit 1;
}
[ -z "$(git -C "$lib_source" status --porcelain --untracked-files=no)" ] || {
    echo 'Canonical libc checkout has local changes' >&2; exit 1;
}
lib_source=$(CDPATH= cd -- "$lib_source" && pwd)
