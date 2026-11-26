#!/bin/sh
# Build libc from its one canonical source, pinned in nitros9-c-libs.revision.
set -eu
. "$(dirname "$0")/shared-lib.sh"
# The canonical builder queries make for module names. Suppress recursive
# directory banners inherited from a parent GNU make invocation.
MAKEFLAGS=--no-print-directory python3 "$lib_source/c3/build.py" --c3 "$c3" --out "$c3/.libc"
cp "$c3/.libc/libc3.a" "$here/libc3.a"
python3 - "$c3/.libc/BUILD.json" "$here/LIBC.json" "$lib_revision" <<'META'
import json,sys
from pathlib import Path
metadata=json.loads(Path(sys.argv[1]).read_text())
metadata.update(url='https://github.com/nitros9project/nitros9-c-libs.git',revision=sys.argv[3])
Path(sys.argv[2]).write_text(json.dumps(metadata,indent=2)+'\n')
META
printf 'Built canonical nitros9-c-libs at %s\n' "$lib_revision"
