#!/bin/sh
# longpath.sh - the c3 driver must handle long paths: C3BASE, -f=, -t= and
# source files in deep directories compile, and a name too long for its buffer
# stops with an error rather than a crash.  Runs the c3 on the PATH, and
# needs a C3BASE (or the installed one) with defs/ in it.
set -u
base=${C3BASE:-/usr/local/share/toolshed}
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
cd "$dir" || exit 2
fails=0

check() {	# check <description> <expected: ok|fail> <command...>
	what=$1; want=$2; shift 2
	"$@" >out 2>&1
	st=$?
	if [ $st -eq 0 ]; then got=ok
	elif [ $st -gt 128 ]; then got="crash (status $st)"
	else got=fail; fi
	if [ "$got" = "$want" ]; then
		echo "ok   $what"
	else
		echo "FAIL $what: wanted $want, got $got"
		fails=$((fails + 1))
	fi
}

# a directory path of about 300 characters, past the old 128-byte buffers
deep=$dir
i=0
while [ $i -lt 12 ]; do
	deep=$deep/abcdefghijklmnopqrstuvw
	i=$((i + 1))
done
mkdir -p "$deep"
ln -s "$base/defs" "$deep/defs"
printf 'main() { exit(0); }\n' > "$deep/good.c"
printf 'main() { exit(0); }\n' > good.c

check "long C3BASE"          ok   env C3BASE="$deep" c3 -q good.c -f=good1
check "long -f= path"        ok   c3 -q good.c -f="$deep/good2"
check "long -t= directory"   ok   c3 -q good.c -t="$deep" -f=good3
check "long source path"     ok   c3 -q "$deep/good.c" -f=good4

# a name longer than any path the host allows is refused, not overflowed
huge=$(printf '%05000d' 0)
check "C3BASE too long"      fail env C3BASE="/$huge" c3 -q good.c -f=good5
check "-f= name too long"    fail c3 -q good.c -f="$huge"
[ "$fails" -eq 0 ]
