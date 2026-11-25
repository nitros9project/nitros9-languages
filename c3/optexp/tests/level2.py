#!/usr/bin/env python3
"""Regression checks; optionally assemble and execute both modes in USIM."""
import argparse
import pathlib
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('optimizer')
parser.add_argument('--lwasm')
parser.add_argument('--usim')
args = parser.parse_args()

def optimize(source, enabled=True):
    return subprocess.run([args.optimizer] + (['-2'] if enabled else []),
                          input=source, text=True, capture_output=True,
                          check=True).stdout

for operand, expected in [('400,y', '>400'), ('>symbol+2,y', '>symbol+2'),
                          ('-200,y', '>-200'),
                          ('$1234,y comment', '>$1234 comment')]:
    source = f'entry lda {operand}\n rts\n'
    assert f'lda {expected}' in optimize(source)
    assert f'lda {operand}' in optimize(source, False)
for operand in ['a,y', 'b,y', 'd,y', '[400,y]', ',y+', ',--y',
                '<400,y', '400,x', '400,u', '400,s']:
    assert f'lda {operand}' in optimize(f' lda {operand}\n rts\n')
for operand in [',y'] + [f'{n},y' for n in range(-16, 16)] + ['$f,y', '-$10,y']:
    assert f'lda {operand}' in optimize(f' lda {operand}\n rts\n')
for operand in ['-17,y', '16,y', '$10,y', '-$11,y']:
    assert f'lda >{operand[:-2]}' in optimize(f' lda {operand}\n rts\n')
for writer in ['ldy 4,s', 'ldy 400,y', 'leay 1,y', 'puls y', 'pulu a,y',
               'tfr d,y', 'exg d,y', 'exg y,x', 'lda ,y+', 'lda ,--y', 'rti']:
    output = optimize(f' {writer}\n lda 400,y\n sta output\n rts\n')
    assert 'lda 400,y' in output, (writer, output)
# The reviewer's inline-assembly example must preserve pointer-relative loads.
assert 'lda 2,y' in optimize(' pshs y\n ldy 4,s\n lda 2,y\n puls y\n rts\n')
# Conservative state lasts through labels and explicit restoration, then resets
# only for a new program section (not a data section).
assert 'lda 400,y' in optimize(' ldy 4,s\n puls y\nnext lda 400,y\n rts\n')
assert 'lda >400' in optimize(' ldy 4,s\n rts\n endsect\n psect next\n lda 400,y\n rts\n')
for reg in ['x', 'u', 's']:
    assert f'ld{reg} #400' in optimize(f' lea{reg} 400,y\n lda ,x\n rts\n')
    # Flags remain live across a call/return, or a conditional branch.
    for following in ['rts', 'jsr external', 'bvs external', 'beq external']:
        assert f'lea{reg} 400,y' in optimize(f' lea{reg} 400,y\n {following}\n rts\n')
assert 'leay 400,y' in optimize(' leay 400,y\n lda ,x\n rts\n')
assert subprocess.run([args.optimizer, '-2junk'], input='', text=True,
                      capture_output=True).returncode != 0
print('PASS: addressing modes, default behavior, option parsing and live flags')

if args.lwasm and args.usim:
    source = '''entry lda value,y
 cmpa #42
 bne failed
 leax value,y
 lda ,x
 cmpa #42
 bne failed
 orcc #$0a
 leax value,y
 bvc failed
 bpl failed
 orcc #$04
 leau value,y
 bne failed
 pshs y
 ldy #value-400
 lda 400,y
 cmpa #42
 bne failed
 puls y
 ldd #0
 rts
failed ldd #1
 rts
'''
    with tempfile.TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        for enabled in [False, True]:
            asm = root / 'test.asm'
            binary = root / 'test.srec'
            asm.write_text(' org $2800\nstart lds #$fe00\n ldy #0\n'
                           ' lbsr entry\n sync\n' + optimize(source, enabled) +
                           'value fcb 42\n end start\n')
            subprocess.run([args.lwasm, '--format=srec', '-o', str(binary), str(asm)], check=True)
            subprocess.run([args.usim, str(binary)], check=True, timeout=10)
    print('PASS: both modes execute correctly in USIM, including live N/Z/V flags')
