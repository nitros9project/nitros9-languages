#!/bin/sh
# Verify the default header/library path, either in-tree or in a staged install.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
if [ "$#" -gt 0 ]; then
    prefix=$1
    export C3BASE="$prefix/share/toolshed" C3LW_HOME="$prefix/bin"
    manifest="$C3BASE/defs/LIBC.json"
    export PATH="$prefix/bin:$PATH"
else
    export C3BASE="$root" C3LW_HOME="$root/lwbackend"
    manifest="$C3LW_HOME/LIBC.json"
    export PATH="$root/build/unix/exec:$root/build/unix/prep:$root/build/unix/comp:$root/build/unix/optx:$root/lwbackend:$PATH"
fi
python3 - "$root/nitros9-c-libs.revision" "$manifest" "$C3LW_HOME/libc3.a" <<'PY'
import hashlib,json,sys,tempfile,subprocess
from pathlib import Path
pin=Path(sys.argv[1]).read_text().strip()
metadata=json.loads(Path(sys.argv[2]).read_text())
assert metadata['revision']==pin, 'canonical source pin mismatch'
for name,variant in metadata.get('variants',{}).items():
    archive=Path(sys.argv[3]).parent/name
    assert variant['library_sha256']==hashlib.sha256(archive.read_bytes()).hexdigest(), 'optional archive mismatch: '+name
assert metadata['library_sha256']==hashlib.sha256(Path(sys.argv[3]).read_bytes()).hexdigest(), 'archive mismatch'
with tempfile.TemporaryDirectory(prefix='c3-shared-') as work:
    directory=Path(work)
    (directory/'probe.c').write_text('''#include <stdio.h>
#include <signal.h>
#include <errno.h>
#define TRUE 1
int main() {
 signal(SIGINT,SIG_IGN);
 if (signal(SIGINT,SIG_DFL) != SIG_IGN) return 1;
 puts("canonical libc"); return E_EOF == 211 ? 0 : 1;
}
''')
    for optimizer in ('off','on'):
        command=['c3','-q','probe.c','-f=probe']
        if optimizer=='off':command.append('-o')
        result=subprocess.run(command,cwd=directory,capture_output=True,text=True,timeout=30)
        if result.returncode or '****' in result.stdout+result.stderr:raise RuntimeError(result.stdout+result.stderr)
        module=(directory/'probe').read_bytes()
        assert module[:2]==b'\x87\xcd' and int.from_bytes(module[2:4],'big')==len(module)
        print('Canonical C3 header/archive check passed ('+optimizer+')')
PY

# Check optional profile selection through the actual driver and installed shim.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT HUP INT TERM
cat >"$work/profile.c" <<'C'
#include <stdio.h>
#include <cgfx.h>
#include <termcap.h>
int main() {
 char buffer[80];
 _cgfx_clear(1);
 tparam("%d",buffer,80,1,2,3,4);
 _trace(0);
 sprintf(buffer,"%f",1.5);
 return 0;
}
C
(cd "$work" && c3 -q profile.c -f=profile -l=clibf.l -l=cgfx.l -l=termcap.l -l=dbg.l)
echo 'Canonical C3 optional profile check passed'
