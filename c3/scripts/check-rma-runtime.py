#!/usr/bin/env python3
"""Assemble and execute the canonical RMA library on a supplied OS-9 kernel."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disk', type=Path, required=True, help='C3 distribution disk')
    parser.add_argument('--boot-disk', type=Path, required=True)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--emulator', default='usim09pt')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--wall-seconds', type=int, default=180)
    parser.add_argument('--self-host', action='store_true', help='Also compile and run hello using the target compiler')
    args = parser.parse_args()
    c3 = Path(__file__).resolve().parents[1]
    source = Path(os.environ.get('NITROS9_C_LIBS_DIR', str(c3/'lwbackend/nitros9-c-libs')))
    pin = (c3/'nitros9-c-libs.revision').read_text().strip()
    assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == pin
    work = args.out.resolve()
    work.mkdir(parents=True, exist_ok=True)
    disk = work/'test.dsk'
    shutil.copyfile(args.boot_disk, disk)

    def run(command, **kwargs):
        result = subprocess.run([str(x) for x in command], capture_output=True, timeout=60, **kwargs)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors='replace')+result.stdout.decode(errors='replace'))
        return result.stdout

    def os9(*args):
        return run(['os9', *args])

    def guest(name):
        return str(disk)+','+name

    tree = work/'distribution'
    if tree.exists():
        raise ValueError('Use a fresh --out directory for each kernel check')
    tree.mkdir()
    os9('dsave', '-e', str(args.disk.resolve())+',', tree)
    os9('makdir', guest('C3'))
    for p in sorted((tree/'C3').rglob('*')):
        relative = 'C3/'+str(p.relative_to(tree/'C3'))
        if p.is_dir():
            os9('makdir', guest(relative))
        else:
            os9('copy', '-r', p, guest(relative))
    for p in (tree/'CMDS').iterdir():
        os9('copy', '-r', p, guest('CMDS/'+p.name))
        os9('attr', '-q', '-e', '-pe', '-pr', guest('CMDS/'+p.name))

    spec = importlib.util.spec_from_file_location('canonical_sources', source/'c3/native_sources.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    text = native.c_view((source/'c3/tests/native.c').read_text())
    text = text.replace('int main(void)', '''static char initarr[]="data";
static char *initptr=initarr;
static char *textptr="code";
static int initnum[3]={7,8,9};
static int blank;
int main(void)''')
    text = text.replace('    CHECK(strlen("abc") == 3);', '''    CHECK(strcmp(initptr,"data") == 0 && strcmp(textptr,"code") == 0);
    CHECK(initnum[1] == 8 && blank == 0);
    CHECK(strlen("abc") == 3);''')
    test = work/'native.c'
    test.write_text(text)
    preprocessed = run([c3/'build/unix/prep/c3prep', '-DOS9', '-v='+str(c3/'defs'), test], cwd=work)
    assembly = run([c3/'build/unix/comp/c3comp', '-s'], input=preprocessed)
    if b'****' in preprocessed+assembly:
        raise RuntimeError((preprocessed+assembly).decode(errors='replace'))
    for name, optimize in [('nb0', False), ('nb2', True)]:
        content = run([c3/'build/unix/optx/c3optx'], input=assembly) if optimize else assembly
        target = work/(name+'.a')
        target.write_bytes(content)
        os9('copy', '-r', '-l', target, guest('C3/src/rma/'+target.name))
    lines = ['chx /dd/cmds', 'chd /dd/c3/src', 'shell <mklibs >rma-build.log',
             'echo RMALIBBUILT', 'chd /dd/c3/src/rma']
    for name in ('nb0', 'nb2'):
        # Microware rlink expects a relative output name in the execution
        # directory. An absolute -o pathname can hang that historical binary.
        lines += ['rma '+name+'.a -o='+name+'.r',
                  'rlink /dd/c3/lib/cstart.r '+name+'.r -o='+name+' -l=/dd/c3/lib/clib.l',
                  name+' >'+name+'.out >>'+name+'.err']
    if args.self_host:
        hello = work/'hello.c'
        hello.write_text('#include <stdio.h>\nmain() { printf("C3 TARGET PASS\\r"); return 0; }\n')
        os9('copy', '-r', '-l', hello, guest('hello.c'))
        lines += ['c3 -q /dd/hello.c -f=hello', 'hello >hello.out']
    lines.append('echo RMACHECKDONE')
    startup = work/'startup'
    startup.write_bytes(('\r'.join(lines)+'\r').encode())
    os9('copy', '-r', startup, guest('startup'))
    os9('attr', '-q', '-npe', '-npw', '-pr', '-ne', '-w', '-r', guest('startup'))
    (work/'state.fram').unlink(missing_ok=True)
    console = work/'console.log'
    with console.open('wb') as log:
        process = subprocess.Popen([args.emulator, '--timeout=12000000000', '-f', str(work/'state.fram'),
                                    '-d', str(disk), str(args.firmware.resolve())], cwd=work,
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic()+args.wall_seconds
        try:
            while process.poll() is None and time.monotonic() < deadline:
                output = console.read_bytes().replace(b'\r', b'')
                if b'RMACHECKDONE\n' in output or b'linker fatal' in output:
                    break
                time.sleep(.2)
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
    output = console.read_bytes().replace(b'\r', b'')
    if b'RMACHECKDONE\n' not in output:
        raise RuntimeError('RMA kernel check did not complete; see '+str(console))
    os9('copy', '-r', guest('C3/src/rma-build.log'), work/'rma-build.log')
    build_log = (work/'rma-build.log').read_text()
    if '*** error' in build_log or re.search(rb'(?i)linker fatal|error #', output):
        raise RuntimeError('RMA build/link error; see '+str(work))
    manifest = json.loads((tree/'C3/src/rma/LIBC.json').read_text())
    for member in manifest['rma_members']:
        target = work/(member['file']+'.r')
        os9('copy', '-r', guest('C3/src/rma/'+target.name), target)
        header = target.read_bytes()[:7]
        if header[:4] != bytes.fromhex('62cd2387') or header[6] != 0:
            raise RuntimeError('Invalid canonical ROF member '+member['file'])
    results = {'library_revision':pin, 'rma_members':len(manifest['rma_members']), 'programs':[]}
    for name in ('nb0', 'nb2'):
        actual = {}
        for extension in ('out', 'err'):
            target = work/(name+'.'+extension)
            os9('copy', '-r', guest('C3/src/rma/'+target.name), target)
            actual[extension] = target.read_bytes().decode()
        if actual != {'out':'OS9TEXT PASS\r', 'err':'OS9TEXT STDERR\r'}:
            raise RuntimeError(name+' failed: '+repr(actual))
        results['programs'].append({'name':name, 'status':'PASS'})
    if args.self_host:
        os9('copy', '-r', guest('C3/src/rma/hello.out'), work/'hello.out')
        if (work/'hello.out').read_bytes() != b'C3 TARGET PASS\r':
            raise RuntimeError('Target compiler smoke test failed')
        results['self_host'] = 'PASS'
    (work/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(results))


if __name__ == '__main__':
    main()
