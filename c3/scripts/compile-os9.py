#!/usr/bin/env python3
"""Run each cross-build stage separately; never archive compiler diagnostics."""
import argparse
from pathlib import Path
import subprocess
import re

p=argparse.ArgumentParser()
for option in ('prep','comp','optx','filter','assembler','output'):
    p.add_argument('--'+option,required=True)
p.add_argument('source_flags',nargs=argparse.REMAINDER)
a=p.parse_args()
flags=a.source_flags[1:] if a.source_flags[:1]==['--'] else a.source_flags

def stage(command,data=None):
    result=subprocess.run(command,input=data,capture_output=True,timeout=60)
    if result.returncode or re.search(rb'(?m)^.* : line [0-9]+\s+\*{4}|^errors in compilation',result.stdout+result.stderr):
        raise SystemExit(result.stdout.decode(errors='replace')+result.stderr.decode(errors='replace'))
    if result.stderr:print(result.stderr.decode(errors='replace'),end='')
    return result.stdout

rma=stage([a.prep,*flags])
rma=stage([a.comp],rma)
rma=stage([a.optx],rma)
assembly=stage(['awk','-f',a.filter],rma)
target=Path(a.output);temporary=target.with_suffix('.tmp.o')
try:
    stage([a.assembler,'--format=obj','-o',str(temporary),'-'],assembly)
    temporary.replace(target)
finally:
    temporary.unlink(missing_ok=True)
