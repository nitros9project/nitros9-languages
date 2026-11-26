#!/bin/sh
# Exercise lazy string-file creation in both host compiler back ends.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/c3-strings.XXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
printf 'char *p = "string-probe"; int main() { return p[0]; }\n' > "$work/probe.c"
cd "$work"
"$root/build/unix/comp/c3comp" < probe.c > mono.asm
"$root/build/unix/comp1/c3comp1" < probe.c > probe.il
"$root/build/unix/comp2/c3comp2" < probe.il > split.asm
for output in mono.asm split.asm; do
    grep -Fq 'fcc "string-probe"' "$output"
done
printf 'Unix string temporary-file checks passed\n'
