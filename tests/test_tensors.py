"""
tests/test_tensors.py
---------------------
Tests for the core tensor computation pipeline.

These tests validate correctness by checking known analytic results:
  - Minkowski: all derived tensors are identically zero.
  - 2-sphere:  scalar curvature K = 2/r² (matches Jannik 2023, docs/references.md).
  - Schwarzschild: G_μν vanishes when the known solution is substituted.

Run with:
    pytest tests/test_tensors.py -v
"""

import pytest
from sympy import (
    Function,
    Integer,
    Symbol,
    diag,
    simplify,
    sin,
    symbols,
    trigsimp,
)
from sympy.tensor.array import ImmutableDenseNDimArray

from core.constraints import apply_constraints, constrain_tensor
from core.spacetime import Spacetime
from core.system import field_equations, independent_equations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _all_indices(arr: ImmutableDenseNDimArray):
    """Yield every multi-index tuple for a tensor of any rank."""
    from itertools import product
    return product(*[range(d) for d in arr.shape])


def is_zero_array(arr: ImmutableDenseNDimArray) -> bool:
    """Return True if every scalar component of arr is exactly zero."""
    return all(arr[idx] == 0 for idx in _all_indices(arr))


def is_zero_array_simplified(arr: ImmutableDenseNDimArray) -> bool:
    """Return True if every component simplifies to zero."""
    return all(simplify(arr[idx]) == 0 for idx in _all_indices(arr))


# ---------------------------------------------------------------------------
# Minkowski spacetime
# ---------------------------------------------------------------------------

class TestMinkowski:
    """All curvature tensors must vanish for flat Cartesian Minkowski."""

    @pytest.fixture(scope="class")
    def minkowski(self):
        t, x, y, z = symbols("t x y z")
        metric = diag(-1, 1, 1, 1)
        return Spacetime([t, x, y, z], metric)

    def test_christoffel_vanishes(self, minkowski):
        gamma = minkowski.christoffel()
        assert is_zero_array(gamma), "All Christoffel symbols should be zero."

    def test_riemann_vanishes(self, minkowski):
        R = minkowski.riemann()
        assert is_zero_array(R), "Riemann tensor should be zero."

    def test_ricci_vanishes(self, minkowski):
        Ric = minkowski.ricci()
        assert is_zero_array(Ric), "Ricci tensor should be zero."

    def test_ricci_scalar_vanishes(self, minkowski):
        assert minkowski.ricci_scalar() == 0, "Ricci scalar should be zero."

    def test_einstein_vanishes(self, minkowski):
        G = minkowski.einstein()
        assert is_zero_array(G), "Einstein tensor should be zero."

    def test_no_field_equations(self, minkowski):
        eqs = field_equations(minkowski.einstein(), condition=0)
        assert eqs == [], "Vacuum field equations should be trivially satisfied."


# ---------------------------------------------------------------------------
# 2-sphere  (reference: Jannik 2023, docs/references.md)
# ---------------------------------------------------------------------------

class TestTwoSphere:
    """
    The round 2-sphere of radius r has scalar curvature K = 2/r².

    This tests the pipeline against the result derived in:
    Jannik (2023), 'Curvature and Derivative on Riemannian Manifolds
    with SymPy Tensor', https://jd11111.github.io/2023/06/28/RieGeoTens.html
    """

    @pytest.fixture(scope="class")
    def two_sphere(self):
        theta, phi = symbols("theta phi", real=True, positive=True)
        r = Symbol("r", positive=True)
        # Metric of S² with radius r: ds² = r² dθ² + r² sin²θ dφ²
        metric = diag(r**2, r**2 * sin(theta) ** 2)
        return Spacetime([theta, phi], metric)

    def test_ricci_scalar(self, two_sphere):
        R_sc = two_sphere.ricci_scalar(simplified=True)
        r = Symbol("r", positive=True)
        # K = 2/r²
        assert simplify(R_sc - 2 / r**2) == 0, (
            f"Ricci scalar for 2-sphere should be 2/r²; got {R_sc}"
        )


# ---------------------------------------------------------------------------
# Schwarzschild spacetime
# ---------------------------------------------------------------------------

class TestSchwarzschild:
    """
    The Schwarzschild solution satisfies the vacuum EFE G_μν = 0.

    Ansatz: ds² = -A(r)dt² + B(r)dr² + r²dΩ²
    Solution: A(r) = 1 - 2M/r,  B(r) = 1/(1 - 2M/r)
    """

    @pytest.fixture(scope="class")
    def schwarzschild_st(self):
        t, r, theta, phi = symbols("t r theta phi", real=True)
        A = Function("A")(r)
        B = Function("B")(r)
        metric = diag(-A, B, r**2, r**2 * sin(theta) ** 2)
        return Spacetime([t, r, theta, phi], metric)

    @pytest.fixture(scope="class")
    def schwarzschild_eqs(self, schwarzschild_st):
        G = schwarzschild_st.einstein()
        return field_equations(G, condition=0, symmetry="symmetric")

    def test_field_equations_exist(self, schwarzschild_eqs):
        """Ansatz should produce at least one non-trivial equation."""
        assert len(schwarzschild_eqs) > 0, (
            "Expected non-trivial vacuum field equations from the ansatz."
        )

    def test_solution_satisfies_equations(self, schwarzschild_st, schwarzschild_eqs):
        """Substituting the Schwarzschild solution should leave no residual."""
        r = symbols("r")
        M = Symbol("M", positive=True)
        A = Function("A")(r)
        B = Function("B")(r)

        subs = {A: 1 - 2 * M / r, B: 1 / (1 - 2 * M / r)}
        remaining = independent_equations(schwarzschild_eqs, substitutions=subs)

        # Any remaining equations should simplify to 0 = 0
        truly_nonzero = [
            eq for eq in remaining
            if trigsimp(simplify(eq.lhs - eq.rhs)) != 0
        ]
        assert truly_nonzero == [], (
            f"Schwarzschild solution left {len(truly_nonzero)} unsatisfied "
            f"equation(s): {truly_nonzero}"
        )

    def test_einstein_tensor_vanishes_on_solution(self, schwarzschild_st):
        """G_μν should vanish component-wise for the Schwarzschild solution."""
        r = symbols("r")
        M = Symbol("M", positive=True)
        A = Function("A")(r)
        B = Function("B")(r)

        from sympy import Eq as SymEq
        solution = [
            SymEq(A, 1 - 2 * M / r),
            SymEq(B, 1 / (1 - 2 * M / r)),
        ]

        G = schwarzschild_st.einstein()
        G_sub = constrain_tensor(G, solution)

        for mu in range(4):
            for nu in range(4):
                val = trigsimp(simplify(G_sub[mu, nu]))
                assert val == 0, (
                    f"G[{mu},{nu}] = {val} after substituting Schwarzschild solution."
                )
