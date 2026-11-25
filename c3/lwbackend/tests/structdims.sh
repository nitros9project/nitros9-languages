#!/bin/sh
# Compile with the freshly built c3 on PATH; no assembler/runtime is needed.
# To expose uninitialized dimension pointers deterministically, clean and rebuild comp, comp1, comp2 and compx
# with CC="cc -ftrivial-auto-var-init=pattern" before running this check.
set -eu
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
cd "$dir"
cat > structdims.c <<'EOF'
struct node {
    unsigned value;
    struct node *next;
};
unsigned known(seed)
unsigned seed;
{
    struct node nodes[32], *p;
    nodes[seed & 31].value = seed;
    p = &nodes[seed & 31];
    return p->value;
}
unsigned forward()
{
    struct pending *items[4];
    items[0] = 0;
    return sizeof(items);
}
typedef unsigned row[4];
unsigned dimensions(seed)
unsigned seed;
{
    row values[2];
    values[1][3] = seed;
    return values[1][3];
}
EOF
for mode in single two-pass; do
    rm -f structdims.a
    if [ "$mode" = single ]; then
        c3 -a structdims.c
    else
        c3 -2 -a structdims.c
    fi
    [ -s structdims.a ]
    echo "ok   $mode: known/forward structure dimensions and array typedef"
done

# c3compx cannot size arrays of pointers to incomplete tags. Exercise the
# known-structure early return separately without that unrelated limitation.
sed '/^unsigned forward()/,$d; /struct node \*next;/d' structdims.c > structexp.c
if ! c3 -k=c3compx -a structexp.c > experimental.log 2>&1; then
    cat experimental.log
    exit 1
fi
[ -s structexp.a ]
echo 'ok   experimental: known structure dimensions'
