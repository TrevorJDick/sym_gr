"""
examples/schwarzschild.py
-------------------------
Milestone 2: Deriving the Schwarzschild metric from vacuum field equations.

Starting point: a static, spherically symmetric metric ansatz in
Schwarzschild-like coordinates (t, r, θ, φ):

    ds² = -A(r) dt² + B(r) dr² + r² dθ² + r² sin²θ dφ²

where A(r) and B(r) are unknown functions of r only.

The vacuum Einstein field equations G_μν = 0 produce a system of ODEs
in A(r) and B(r).  The unique solution (with boundary condition A → 1
as r → ∞, i.e. asymptotic flatness) is:

    A(r) = 1 - 2M/r
    B(r) = (1 - 2M/r)^{-1}

This example:
  1. Constructs the Spacetime from the ansatz.
  2. Computes the Einstein tensor G_μν (simplified).
  3. Extracts the vacuum field equations G_μν = 0.
  4. Displays the ODE system as LaTeX.
  5. Verifies that the Schwarzschild solution satisfies G_μν = 0.

Note on runtime
---------------
The Christoffel and Riemann computations for a 4D metric with symbolic
function-valued components involve many algebraic steps.  Expect this
script to take 30–90 seconds on a typical workstation.  The ``simplified``
flag on each tensor call applies sympy.simplify component-wise, which
produces cleaner output but adds time.

Run
---
    python -m examples.schwarzschild
"""

from sympy import (
    Function,
    Rational,
    Symbol,
    cos,
    latex,
    pprint,
    simplify,
    sin,
    symbols,
    trigsimp,
)
from sympy import diag as sp_diag
from sympy.tensor.array import ImmutableDenseNDimArray

from core.constraints import apply_constraints, constrain_tensor
from core.spacetime import Spacetime
from core.system import field_equations, independent_equations

# ---------------------------------------------------------------------------
# 1. Coordinates and metric ansatz
# ---------------------------------------------------------------------------

t, r, theta, phi = symbols("t r theta phi", real=True)
M = Symbol("M", positive=True)  # mass parameter

A = Function("A")(r)  # g_tt component (sign-flipped, so A > 0)
B = Function("B")(r)  # g_rr component (B > 0)

coords = [t, r, theta, phi]

# Static, spherically symmetric ansatz
metric = sp_diag(-A, B, r**2, r**2 * sin(theta) ** 2)

print("=" * 60)
print("Schwarzschild spacetime  (Milestone 2)")
print("=" * 60)
print()
print("Coordinates    :", [str(c) for c in coords])
print()
print("Metric ansatz g_μν:")
pprint(metric)
print()
print(r"LaTeX:  ds^2 = -A(r)\,dt^2 + B(r)\,dr^2 + r^2\,d\theta^2"
      r" + r^2\sin^2\!\theta\,d\phi^2")
print()

# ---------------------------------------------------------------------------
# 2. Build Spacetime and compute Einstein tensor
# ---------------------------------------------------------------------------

st = Spacetime(coords, metric)

print("Step 1/4  Computing Christoffel symbols Γ^σ_μν ...")
gamma = st.christoffel()

print("Step 2/4  Computing Riemann tensor R^ρ_σμν ...")
R = st.riemann()

print("Step 3/4  Computing Ricci tensor R_μν and Ricci scalar ...")
Ric = st.ricci()
R_sc = st.ricci_scalar()

print("Step 4/4  Computing Einstein tensor G_μν ...")
G = st.einstein()
print()

# ---------------------------------------------------------------------------
# 3. Extract vacuum field equations  G_μν = 0
# ---------------------------------------------------------------------------

print("-" * 60)
print("Vacuum field equations  G_μν = 0")
print("-" * 60)
print()

raw_eqs = field_equations(G, condition=0, symmetry="symmetric")
print(f"Total non-trivial independent equations: {len(raw_eqs)}")
print()

for i, eq in enumerate(raw_eqs):
    simplified_lhs = trigsimp(simplify(eq.lhs))
    print(f"Equation ({i+1}):")
    pprint(simplified_lhs)
    print(f"  LaTeX: {latex(simplified_lhs)} = 0")
    print()

# ---------------------------------------------------------------------------
# 4. Verify the Schwarzschild solution satisfies the field equations
# ---------------------------------------------------------------------------

print("-" * 60)
print("Verification: substitute Schwarzschild solution")
print(f"  A(r) = 1 - 2M/r")
print(f"  B(r) = 1/(1 - 2M/r)")
print("-" * 60)
print()

solution = [
    __import__("sympy").Eq(A, 1 - 2 * M / r),
    __import__("sympy").Eq(B, 1 / (1 - 2 * M / r)),
]

reduced_eqs = independent_equations(raw_eqs, substitutions={A: 1 - 2*M/r, B: 1/(1 - 2*M/r)})

print(f"Non-trivial equations remaining after substitution: {len(reduced_eqs)}")
if reduced_eqs:
    print("Remaining equations (should all simplify to 0 = 0 after trigsimp):")
    for eq in reduced_eqs:
        val = trigsimp(simplify(eq.lhs - eq.rhs))
        print(f"  Residual: {val}")
else:
    print("  All equations satisfied identically.  ✓")
print()

# Also verify directly: substitute into the Einstein tensor itself
G_sub = constrain_tensor(G, solution)
nonzero_in_G = [
    (mu, nu, trigsimp(simplify(G_sub[mu, nu])))
    for mu in range(4)
    for nu in range(mu, 4)
    if trigsimp(simplify(G_sub[mu, nu])) != 0
]

if not nonzero_in_G:
    print("G_μν[Schwarzschild solution] = 0 for all components.  ✓")
    print()
    print("Milestone 2 complete: the vacuum field equations G_μν = 0")
    print("are satisfied by A(r) = 1 - 2M/r, B(r) = (1 - 2M/r)^{-1}.")
else:
    print("Non-zero components found after substitution:")
    for mu, nu, val in nonzero_in_G:
        print(f"  G_{mu}{nu} = {val}")
