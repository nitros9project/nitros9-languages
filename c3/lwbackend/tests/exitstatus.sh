#!/bin/sh
# exitstatus.sh - the c3 driver must exit non-zero when a stage fails, or make
# carries on with no output file.  Runs the c3 on the PATH.
set -u
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
cd "$dir" || exit 2
fails=0

check() {	# check <description> <expected: ok|fail> <command...>
	what=$1; want=$2; shift 2
	if "$@" >/dev/null 2>&1; then got=ok; else got=fail; fi
	if [ "$got" = "$want" ]; then
		echo "ok   $what"
	else
		echo "FAIL $what: wanted $want, got $got"
		fails=$((fails + 1))
	fi
}

printf 'f( { return 1 }\n' > badcomp.c
printf 'main() { nosuch(); }\n' > badlink.c
printf 'main() { exit(0); }\n' > good.c

check "compile error"    fail c3 -q -r badcomp.c
check "undefined symbol" fail c3 -q badlink.c -f=badlink
check "good program"     ok   c3 -q good.c -f=good
[ "$fails" -eq 0 ]
