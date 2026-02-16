"""
examples/minkowski.py
---------------------
Milestone 1: Minkowski spacetime validation.

The Minkowski metric in Cartesian coordinates is:

    g_μν = diag(-1, 1, 1, 1)

For flat spacetime all connection coefficients vanish, so every derived
geometric quantity (Riemann, Ricci, Einstein) must be identically zero.

This example:
  1. Constructs the Minkowski spacetime.
  2. Computes every tensor in the standard pipeline.
  3. Asserts that all components vanish — validating the computation.
  4. Prints each result as a LaTeX string.

Expected result: every tensor is the zero tensor.

Run
---
    python -m examples.minkowski
"""

from sympy import symbols, diag, latex, pprint, zeros

from core.spacetime import Spacetime
from core.system import field_equations

# ---------------------------------------------------------------------------
# 1. Define coordinates and metric
# ---------------------------------------------------------------------------

t, x, y, z = symbols("t x y z")
coords = [t, x, y, z]

# Minkowski metric: diag(-1, 1, 1, 1)  — flat spacetime, Cartesian coordinates
metric = diag(-1, 1, 1, 1)

print("=" * 60)
print("Minkowski spacetime  (Milestone 1)")
print("=" * 60)
print()
print("Coordinates :", [str(c) for c in coords])
print("Metric g_μν :")
pprint(metric)
print()
print(f"LaTeX: g_{{\\mu\\nu}} = {latex(metric)}")
print()

# ---------------------------------------------------------------------------
# 2. Build the Spacetime and compute tensors
# ---------------------------------------------------------------------------

st = Spacetime(coords, metric)

print("Computing Christoffel symbols Γ^σ_μν ...")
gamma = st.christoffel()

print("Computing Riemann tensor R^ρ_σμν ...")
R = st.riemann()

print("Computing Ricci tensor R_μν ...")
Ric = st.ricci()

print("Computing Ricci scalar R ...")
R_sc = st.ricci_scalar()

print("Computing Einstein tensor G_μν ...")
G = st.einstein()
print()

# ---------------------------------------------------------------------------
# 3. Display non-zero components (should be none)
# ---------------------------------------------------------------------------

n = st.n

print("-" * 60)
print("Non-zero Christoffel components:")
found = False
for s in range(n):
    for m in range(n):
        for v in range(n):
            val = gamma[s, m, v]
            if val != 0:
                print(f"  Γ^{s}_{m}{v} = {val}")
                found = True
if not found:
    print("  None  ✓")
print()

print("Non-zero Riemann components:")
found = False
for r_ in range(n):
    for s in range(n):
        for m in range(n):
            for v in range(n):
                val = R[r_, s, m, v]
                if val != 0:
                    print(f"  R^{r_}_{s}{m}{v} = {val}")
                    found = True
if not found:
    print("  None  ✓")
print()

print(f"Ricci scalar R = {R_sc}")
print()

print("Non-zero Einstein components:")
found = False
for m in range(n):
    for v in range(m, n):
        val = G[m, v]
        if val != 0:
            print(f"  G_{m}{v} = {val}")
            found = True
if not found:
    print("  None  ✓")
print()

# ---------------------------------------------------------------------------
# 4. Extract vacuum field equations  G_μν = 0
# ---------------------------------------------------------------------------

eqs = field_equations(G, condition=0)
print("-" * 60)
print(f"Vacuum field equations G_μν = 0:  {len(eqs)} non-trivial equation(s)")
if eqs:
    for eq in eqs:
        print(f"  {eq}")
else:
    print("  System is trivially satisfied — consistent with flat spacetime.  ✓")
print()

# ---------------------------------------------------------------------------
# 5. Programmatic assertions (used by tests/test_tensors.py)
# ---------------------------------------------------------------------------

zero_matrix = zeros(n)

assert all(gamma[s, m, v] == 0 for s in range(n) for m in range(n) for v in range(n)), \
    "Christoffel symbols should all vanish for Minkowski metric."

assert all(R[r_, s, m, v] == 0
           for r_ in range(n) for s in range(n)
           for m in range(n) for v in range(n)), \
    "Riemann tensor should vanish for Minkowski metric."

assert R_sc == 0, "Ricci scalar should vanish for Minkowski metric."
assert len(eqs) == 0, "Vacuum field equations should be trivially satisfied."

print("All assertions passed.  Milestone 1 complete.")
