#!/bin/sh
# Compile with the freshly built c3 on PATH; no assembler/runtime is needed.
# To expose uninitialized dimension pointers deterministically, rebuild comp
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
c3 -a structdims.c
[ -s structdims.a ]
echo 'ok   known/forward structure dimensions and array typedef'
