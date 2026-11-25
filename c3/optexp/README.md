# c3optx

`c3optx [-2] [input [output]]` runs the C3 assembly peephole optimizer.
Input and output default to standard input and standard output.

## OS-9 Level II mode

Pass `-2` explicitly to enable DCC-style Level II addressing rewrites. This
asserts that **Y is zero at every rewritten instruction**, as in the applicable
OS-9 Level II C memory model. Do not use it for code that keeps a nonzero data
base in Y. **Inline `#asm` blocks pass through the optimizer too and are
bound by this contract.** After an instruction writes Y (including loads,
LEAY, transfers/exchanges, stack restores, RTI, or auto-indexing), the optimizer
conservatively stops these rewrites until the next `psect`. Restoring Y does
not re-enable them. This guard does not prove the contract across arbitrary
control flow; callers must still guarantee Y=0 at every rewritten instruction.

Constant Y-relative memory operands become forced extended addresses:
`lda value,y` becomes `lda >value`. LEAX, LEAU and LEAS become immediate loads
when the following instruction overwrites N, Z and V without reading them:
`leax value,y; lda ,x` becomes `ldx #value; lda ,x`.

The LEA restriction preserves live condition flags; DCC's pattern substitutions
alone do not provide that protection. Accumulator offsets, indirect addressing,
auto-indexing, forced 8-bit offsets and LEAY are left unchanged. Zero-offset
and literal offsets from -16 through 15 retain indexed memory addressing,
which is smaller than forced extended addressing. Symbolic offsets are still
rewritten, so this mode does not guarantee smaller code.

Without `-2`, output is unchanged. This option belongs to **c3optx**, not the C3
driver: the driver's existing `-2` selects the two-pass compiler and does not
forward this optimizer option. Invoke the optimizer explicitly when needed.

## Regression checks

From the repository root:

```sh
make -C c3/build/unix/optx CPPFLAGS=-D_DEFAULT_SOURCE
python3 c3/optexp/tests/level2.py c3/build/unix/optx/c3optx
```

Add `--lwasm /path/to/lwasm --usim /path/to/usim` to assemble and execute both
modes, including checks that N/Z/V flags remain valid across LEA instructions.
