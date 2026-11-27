#!/usr/bin/env python3
"""Stage RMA source from the canonical native C3 build, never a second libc."""
import argparse
import ast
import hashlib
import json
import operator
from pathlib import Path
import re
import subprocess

TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])\'|[$%][0-9a-fA-F]+|[A-Za-z_.][\w.]*')


def uncomment(line):
    if line.lstrip().startswith(('*', ';')):
        return ''
    fcc = re.match(r"^(?:\S+\s+)?[ \t]*fcc[ \t]+(.)", line, re.I)
    if fcc:
        end = line.find(fcc[1], fcc.end())
        if end >= 0:
            return line[:end+1]
    # Semicolons in strings are data, not comments.
    return re.split(r';(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', line, 1)[0].rstrip()


def fields(line):
    if not line.strip():
        return '', '', ''
    match = re.match(r'(?:(\S+?)(?::|\s+))?\s*(\S+)?(?:\s+(.*))?$', line)
    if line[0].isspace():
        parts = line.split(None, 1)
        return '', parts[0].lower(), parts[1] if len(parts) > 1 else ''
    if len(line.split()) == 1:
        return line.rstrip(':'), '', ''
    return match[1] or '', (match[2] or '').lower(), match[3] or ''


def expression(value, constants):
    """Evaluate assembler absolute constants without executing source text."""
    value = re.sub(r"\$([0-9a-fA-F]+)", r"0x\1", value)
    value = re.sub(r"%([01]+)", r"0b\1", value)
    value = re.sub(r"(?<![\w)])\^", "~", value)
    value = re.sub(r"'(.)'", lambda m: str(ord(m[1])), value)
    ops = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul,
           ast.Div:operator.floordiv, ast.LShift:operator.lshift,
           ast.RShift:operator.rshift, ast.BitOr:operator.or_, ast.BitAnd:operator.and_,
           ast.BitXor:operator.xor, ast.USub:operator.neg, ast.UAdd:operator.pos,
           ast.Invert:operator.invert}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.Name):
            return constants[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](visit(node.operand))
        raise ValueError('Not an absolute assembler expression')
    return visit(ast.parse(value, mode='eval').body)


def clean_operand(value):
    # Old RMA does not consistently accept tabs before trailing comments.
    quote = None
    for i, c in enumerate(value):
        if c in "\"'":
            quote = None if quote == c else c if quote is None else quote
        elif c.isspace() and quote is None:
            return value[:i]
    return value


def convert(text, name):
    """Undo LWTOOLS data-image packaging; RMA/rlink supplies data relocation."""
    rows = [fields(uncomment(line)) for line in text.splitlines() if uncomment(line)]
    exports = set()
    for label, op, arg in rows:
        if op == 'export':
            exports.add(label or arg.split()[0])
    # c3lw.awk maps an initialized vsect to image + BSS + copy/relocation tables.
    # Put its public symbols back at the image labels, then make that image a
    # normal RMA initialized vsect. The duplicate BSS reservation/tables vanish.
    aliases = {}
    for label, op, arg in rows:
        m = re.fullmatch(r'([\w.]+)\+\(([\w.]+)-([\w.]+)\)', arg)
        if op == 'equ' and m and '.bss.' in m[1]:
            aliases.setdefault(m[2], []).append(label)
    mapped = set(x for names in aliases.values() for x in names)
    defined = {label for label, op, _ in rows if label and op not in ('export', 'external', 'extern', 'import')}
    constants = {}
    for _ in range(len(rows)):
        before = len(constants)
        for label, op, arg in rows:
            if op == 'equ' and label not in mapped:
                try:
                    constants[label] = expression(clean_operand(arg), constants)
                except (KeyError, ValueError, SyntaxError):
                    pass
        if len(constants) == before:
            break
    names = {}
    # RMA has eight-character names. Long cross-member symbols need the same
    # deterministic spelling in every unit; local symbols are unit-specific.
    for label in sorted(defined | exports):
        if label in exports and len(label) <= 8:
            names[label] = label
        else:
            key = label if label in exports else name + ':' + label
            names[label] = 'z' + hashlib.sha256(key.encode()).hexdigest()[:7]
    for label, op, arg in rows:
        if op in ('external', 'extern', 'import'):
            symbol = label or arg.split()[0]
            if len(symbol) > 8:
                names[symbol] = 'z' + hashlib.sha256(symbol.encode()).hexdigest()[:7]
    if len(set(names.values())) != len(names):
        raise ValueError('RMA symbol collision in ' + name)

    def operand(value):
        value = clean_operand(value)
        prefix = "#" if value.startswith("#") else ""
        raw = value[len(prefix):]
        try:
            return prefix + str(expression(raw, constants))
        except (KeyError, ValueError, SyntaxError):
            pass
        # RMA uses one-sided character literals. Numeric values avoid dialect
        # differences for quotes, spaces, and escaped characters.
        def replace(m):
            token = m[0]
            if token.startswith("'"):
                return str(ord(ast.literal_eval(token)))
            return str(constants[token]) if token in constants else names.get(token, token)
        return TOKEN.sub(replace, value)

    macros={label for label,op,_ in rows if op=='macro'}
    output = [' psect ' + name[:8] + ',0,0,0,0,0']
    section = None
    vsect = False
    for label, op, arg in rows:
        if op == 'section':
            if vsect:
                output.append(' endsect')
                vsect = False
            section = arg.split()[0].lower()
            if section in ('bss', 'data', 'directpage'):
                output.append(' vsect dp' if section=='directpage' else ' vsect')
                vsect = True
            elif section not in ('code', 'irec', 'ireloc', 'icreloc'):
                raise ValueError('Unsupported section ' + section)
            continue
        if op in ('endsection', 'endsect'):
            if vsect:
                output.append(' endsect')
                vsect = False
            section = None
            continue
        if op in ('export', 'external', 'extern', 'import'):
            continue
        if section in ('irec', 'ireloc', 'icreloc'):
            continue
        if (op == 'rmb' and '.bss.' in label) or label in mapped:
            continue
        for alias in aliases.get(label, []):
            output.append(names[alias] + (':' if alias in exports else ''))
        prefix = names.get(label, label) + (':' if label in exports else '') if label else ''
        if op == 'zmb':
            # Initialized zero bytes must remain initialized in a vsect.
            count = expression(clean_operand(arg), constants)
            if prefix:
                output.append(prefix)
            for start in range(0, count, 24):
                output.append(' fcb ' + ','.join(['0'] * min(24, count-start)))
            continue
        if op == 'fcc':
            delimiter = arg[0]
            end = arg.find(delimiter, 1)
            if end < 0:
                raise ValueError("Unterminated fcc in " + name)
            value = arg[1:end]
            if prefix:
                output.append(prefix)
            if value:
                output.append(' fcb ' + ','.join(str(ord(c)) for c in value))
            continue
        selected=operand(arg) if arg else ''
        if op in ('anda','andb','ora','orb','eora','eorb','andcc','orcc','lda','ldb','cmpa','cmpb','bita','bitb','adda','addb','suba','subb','adca','adcb','sbca','sbcb') and re.fullmatch(r'#-?\d+',selected):
            selected='#'+str(int(selected[1:])&255)
        opcode=names.get(op,op) if op in macros else op
        output.append(prefix + (' ' + opcode + (' ' + selected if selected else '') if opcode else ''))
    if vsect:
        output.append(' endsect')
    output.append(' endsect')
    return '\n'.join(output) + '\n'


def library_scans(units):
    """Bound one-pass ROF scans for every public entry point, including cycles."""
    all_exports = set().union(*(exports for exports, _ in units))
    maximum = 1
    for exports, _ in units:
        needed, provided, loaded = set(exports), set(), set()
        scans = 0
        while needed - provided:
            scans += 1
            before = len(loaded)
            for i, (symbols, references) in enumerate(units):
                if i not in loaded and symbols & (needed - provided):
                    loaded.add(i)
                    provided.update(symbols)
                    needed.update(references & all_exports)
            if len(loaded) == before:
                raise ValueError('Unresolvable canonical RMA dependency')
        maximum = max(maximum, scans)
    return maximum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c3', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    c3=args.c3.resolve();build=c3/'.libc';out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((c3/'lwbackend/LIBC.json').read_text())
    pin=(c3/'nitros9-c-libs.revision').read_text().strip()
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if manifest['revision']!=pin or manifest['library_sha256']!=digest(build/'libc3.a'):
        raise ValueError('Rebuild the pinned canonical runtime before staging RMA sources')
    profiles={'libc3.a':'clib.l','libc3f.a':'clibf.l','libcgfx.a':'cgfx.l',
              'libtermcap.a':'termcap.l','libalib.a':'alib.l','libdbg.a':'dbg.l'}
    members={};sources=[];units={};staged={}
    for archive in profiles:
        listing=subprocess.check_output(['lwar','-l',str(build/archive)],text=True)
        members[archive]=[Path(line.rsplit(': ',1)[0]).stem for line in listing.splitlines() if line.strip()]
        expected=manifest if archive=='libc3.a' else manifest['variants'][archive]
        if len(members[archive])!=expected['archive_members'] or digest(build/archive)!=expected['library_sha256']:
            raise ValueError('Canonical archive membership/hash mismatch: '+archive)
        for member in members[archive]:
            if member in staged:continue
            filename='l%03d'%len(sources);staged[member]=filename
            text=(build/(member+'.s')).read_text(encoding='latin1')
            exports,references=set(),set()
            for line in text.splitlines():
                label,op,arg=fields(uncomment(line))
                if op=='export':exports.add(label or arg.split()[0])
                elif op in ('extern','external','import'):references.add(label or arg.split()[0])
                else:references.update(TOKEN.findall(arg))
            units[member]=(exports,references)
            (out/(filename+'.a')).write_text(convert(text,filename))
            sources.append({'file':filename,'canonical_member':member})
    # Preserve the register library's historical symbol spellings on native
    # OS-9. These source units already have the required register ABI.
    canonical=Path(__import__('os').environ.get('NITROS9_C_LIBS_DIR',c3/'lwbackend/nitros9-c-libs'))
    for member,filename in staged.items():
        if member.startswith('libalib_'):
            source=canonical/'asm'/(member.removeprefix('libalib_')+'.a')
            text=source.read_bytes().decode('latin1')
            text=re.sub(r'(?mi)^([ \t]*)esect\b',r'\1endsect',text)
            (out/(filename+'.a')).write_bytes(text.encode('latin1'))
    commands=['* Generated from nitros9-c-libs '+pin,'chd /dd/c3/src/rma','shell <cleanup >/nil >>/nil','x']
    for item in sources:commands.append('rma '+item['file']+'.a -o='+item['file']+'.r')
    for name in ('cstart','fpwrap','fpdummy','fpinit','sysstub'):
        commands.append('rma '+name+'.a -o='+name+'.r')
        if name!='sysstub':
            text=subprocess.check_output(['sed','-f',str(c3/'lwbackend/os9defs.sed'),str(c3/'lwbackend'/(name+'.a'))],text=True)
            (out/(name+'.a')).write_text(text)
    (out/'sysstub.a').write_text(' psect sysstub,0,0,0,0,0\n endsect\n')
    generated=[item['file']+'.r' for item in sources]
    generated += [name+'.r' for name in ('cstart','fpwrap','fpdummy','fpinit','sysstub')]
    scans={}
    def merge_tree(objects,prefix):
        level=0
        while len(objects)>8:
            merged=[]
            for i in range(0,len(objects),8):
                name=prefix+str(level)+'%03d.l'%(i//8)
                commands.append('merge '+' '.join(objects[i:i+8])+' >'+name)
                generated.append(name);merged.append(name)
            objects=merged;level+=1
        name=prefix+'full.l';commands.append('merge '+' '.join(objects)+' >'+name);generated.append(name)
        return name
    for i,(archive,target) in enumerate(profiles.items()):
        objects=[staged[m]+'.r' for m in members[archive]]
        selected=[units[m] for m in members[archive]]
        scans[archive]=library_scans(selected)
        if archive in ('libc3.a','libc3f.a'):
            objects += ['fpwrap.r','fpinit.r' if archive=='libc3f.a' else 'fpdummy.r']
        full=merge_tree(objects,chr(ord('a')+i))
        commands.append('merge '+' '.join([full]*scans[archive])+' >/dd/c3/lib/'+target)
        generated.append('/dd/c3/lib/'+target)
    # clibt was the historical transcendental alternative. The canonical
    # native core contains the same math entries, loaded only when referenced.
    commands += ['merge /dd/c3/lib/clib.l >/dd/c3/lib/clibt.l',
                 'merge cstart.r >/dd/c3/lib/cstart.r',
                 'merge fpinit.r '+staged['pffinit']+'.r '+staged['ftoa']+'.r >/dd/c3/lib/fp.l',
                 'merge sysstub.r >/dd/c3/lib/sys.l','echo canonical c3 libraries built']
    generated += ['/dd/c3/lib/'+n for n in ('clibt.l','cstart.r','fp.l','sys.l')]
    if max(map(len,commands))>128:raise ValueError('Native shell command exceeds 128 characters')
    (out/'cleanup').write_text('-x\n'+'\n'.join('del '+name for name in generated)+'\n')
    (out/'mklibs').write_text('\n'.join(commands)+'\n')
    (out/'LIBC.json').write_text(json.dumps(dict(manifest,rma_members=sources,
        rma_total_members=len(sources),rma_library_scans=scans['libc3.a'],rma_profiles=scans,
        rma_exporter_sha256=digest(Path(__file__)),
        rma_sources_sha256={p.name:digest(p) for p in sorted(out.glob('*.a'))}),indent=2)+'\n')


if __name__=='__main__':main()
