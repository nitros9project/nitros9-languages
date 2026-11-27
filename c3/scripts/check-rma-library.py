#!/usr/bin/env python3
"""Check every exported canonical RMA unit with the LWTOOLS syntax bridge."""
import argparse
import importlib.util
import os
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rma-dir', type=Path, required=True)
    args = parser.parse_args()
    c3 = Path(__file__).resolve().parents[1]
    root = args.rma_dir.resolve()
    manifest = json.loads((root/'LIBC.json').read_text())
    assert manifest['revision'] == (c3/'nitros9-c-libs.revision').read_text().strip()
    assert len(manifest['rma_members']) == manifest.get('rma_total_members',manifest['archive_members'])
    canonical=Path(os.environ.get('NITROS9_C_LIBS_DIR',c3/'lwbackend/nitros9-c-libs'))
    spec=importlib.util.spec_from_file_location('canonical_rma',canonical/'c3/rma_sources.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    with tempfile.TemporaryDirectory(prefix='c3-rma-check-') as temporary:
        work = Path(temporary)
        for member in manifest['rma_members']:
            name = member['file']
            source = root/(name+'.a')
            asm = work/(name+'.s')
            asm.write_text(native.assembly(source,c3))
            subprocess.run(['lwasm', '--format=obj', '--pragma=undefextern', '-o', str(work/(name+'.o')), str(asm)], check=True, capture_output=True)
    procedure = (root/'mklibs').read_text().splitlines()
    assert max(map(len, procedure)) <= 128, 'Native shell command is too long'
    print('Canonical RMA bridge: %d members passed' % manifest.get('rma_total_members',manifest['archive_members']))


if __name__ == '__main__':
    main()
