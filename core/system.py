"""
core/system.py
--------------
Extract a system of independent equations from a tensor.

Given a tensor (e.g. the Einstein tensor G_μν) and a target value (e.g. 0),
these functions enumerate the non-trivial independent component equations,
accounting for symmetry.
"""

from __future__ import annotations

from typing import Literal, Sequence

from sympy import Eq, Expr, Integer
from sympy.tensor.array import ImmutableDenseNDimArray

from .constraints import _function_subs


def field_equations(
    tensor: ImmutableDenseNDimArray,
    condition: Expr | int = 0,
    symmetry: Literal["symmetric", "antisymmetric", "none"] = "symmetric",
) -> list[Eq]:
    """
    Extract independent component equations from a rank-2 tensor.

    For a symmetric tensor (e.g. G_μν, R_μν) only the upper triangle
    μ ≤ ν is returned, since G_μν = G_νμ.

    Parameters
    ----------
    tensor : ImmutableDenseNDimArray, shape (n, n)
        The tensor whose components are set equal to *condition*.
    condition : sympy.Expr or int, default 0
        The right-hand side. Typically 0 for vacuum equations.
    symmetry : {"symmetric", "antisymmetric", "none"}
        Controls which index pairs are returned:
        - "symmetric"     → only μ ≤ ν
        - "antisymmetric" → only μ < ν  (diagonal is trivially zero)
        - "none"          → all n² components

    Returns
    -------
    list of sympy.Eq
        Non-trivial independent component equations. Equations of the
        form ``0 = 0`` are dropped automatically.
    """
    if tensor.rank() != 2:
        raise ValueError(
            f"field_equations expects a rank-2 tensor; got rank {tensor.rank()}."
        )

    n = tensor.shape[0]
    eqs: list[Eq] = []
    rhs = Integer(condition) if isinstance(condition, int) else condition

    for mu in range(n):
        if symmetry == "symmetric":
            nu_range = range(mu, n)
        elif symmetry == "antisymmetric":
            nu_range = range(mu + 1, n)
        else:
            nu_range = range(n)

        for nu in nu_range:
            comp = tensor[mu, nu]
            # Drop trivial 0 = 0
            if comp == rhs:
                continue
            eqs.append(Eq(comp, rhs))

    return eqs


def independent_equations(
    equations: list[Eq],
    substitutions: dict | None = None,
) -> list[Eq]:
    """
    Apply optional substitutions and remove equations that become trivial.

    This is useful after applying symmetry conditions or known metric
    components to reduce the system.

    Parameters
    ----------
    equations : list of sympy.Eq
        Input system of equations.
    substitutions : dict, optional
        SymPy substitution dictionary applied to every equation before
        filtering. E.g. ``{A(r): 1 - 2*M/r}`` to check a known solution.

    Returns
    -------
    list of sympy.Eq
        Equations remaining after substitution and trivial-equation removal.
    """
    result: list[Eq] = []
    for eq in equations:
        lhs = eq.lhs
        rhs = eq.rhs
        if substitutions:
            lhs = _function_subs(lhs, substitutions)
            rhs = _function_subs(rhs, substitutions)
        if lhs != rhs:
            result.append(Eq(lhs, rhs))
    return result
