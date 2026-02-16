"""
core/tensors.py
---------------
Pure functions for computing GR tensor quantities from a metric.

All functions operate on SymPy objects and return ImmutableDenseNDimArray
(rank-2 tensors) or sympy expressions (scalars). No physical assumptions
are made — the user supplies the metric and coordinates.

Index conventions (Carroll, Spacetime and Geometry, §3):
  Christoffel:  Γ^σ_μν      stored as  christoffel[σ, μ, ν]
  Riemann:      R^ρ_σμν     stored as  riemann[ρ, σ, μ, ν]
  Ricci:        R_μν        stored as  ricci[μ, ν]
  Einstein:     G_μν        stored as  einstein[μ, ν]

Riemann definition (Carroll eq. 3.113):
  R^ρ_σμν = ∂_μ Γ^ρ_νσ - ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ - Γ^ρ_νλ Γ^λ_μσ

Ricci contraction (first and third index):
  R_μν = R^ρ_μρν

Metric signature: (-,+,+,+) by convention; this is not enforced here.
"""

from __future__ import annotations

from typing import Sequence

from sympy import Expr, Integer, diff, simplify
from sympy import Matrix
from sympy.tensor.array import ImmutableDenseNDimArray


def compute_metric_inverse(metric: Matrix) -> Matrix:
    """
    Return the inverse of the covariant metric tensor g^μν.

    Parameters
    ----------
    metric : sympy.Matrix
        The covariant metric tensor g_μν as an n×n SymPy Matrix.

    Returns
    -------
    sympy.Matrix
        The contravariant metric tensor g^μν.
    """
    return metric.inv()


def compute_christoffel(
    coords: Sequence[Expr],
    metric: Matrix,
    metric_inv: Matrix,
) -> ImmutableDenseNDimArray:
    """
    Compute the Christoffel symbols of the second kind.

    Γ^σ_μν = ½ g^σρ (∂_μ g_νρ + ∂_ν g_μρ - ∂_ρ g_μν)

    Parameters
    ----------
    coords : sequence of sympy.Symbol
        Ordered coordinate symbols, e.g. [t, r, θ, φ].
    metric : sympy.Matrix
        Covariant metric tensor g_μν.
    metric_inv : sympy.Matrix
        Contravariant metric tensor g^μν.

    Returns
    -------
    ImmutableDenseNDimArray, shape (n, n, n)
        Γ^σ_μν indexed as [σ, μ, ν].
    """
    n = len(coords)
    gamma = [[[Integer(0)] * n for _ in range(n)] for _ in range(n)]

    for sigma in range(n):
        for mu in range(n):
            for nu in range(n):
                val: Expr = Integer(0)
                for rho in range(n):
                    # Only sum over non-zero g^σρ to skip unnecessary work
                    if metric_inv[sigma, rho] == 0:
                        continue
                    deriv = (
                        diff(metric[nu, rho], coords[mu])
                        + diff(metric[mu, rho], coords[nu])
                        - diff(metric[mu, nu], coords[rho])
                    )
                    val += metric_inv[sigma, rho] * deriv
                gamma[sigma][mu][nu] = val / 2

    return ImmutableDenseNDimArray(gamma)


def compute_riemann(
    coords: Sequence[Expr],
    christoffel: ImmutableDenseNDimArray,
) -> ImmutableDenseNDimArray:
    """
    Compute the Riemann curvature tensor.

    R^ρ_σμν = ∂_μ Γ^ρ_νσ - ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ - Γ^ρ_νλ Γ^λ_μσ

    Parameters
    ----------
    coords : sequence of sympy.Symbol
        Ordered coordinate symbols.
    christoffel : ImmutableDenseNDimArray, shape (n, n, n)
        Christoffel symbols Γ^σ_μν as computed by compute_christoffel.

    Returns
    -------
    ImmutableDenseNDimArray, shape (n, n, n, n)
        R^ρ_σμν indexed as [ρ, σ, μ, ν].
    """
    n = len(coords)
    R = [[[[Integer(0)] * n for _ in range(n)] for _ in range(n)] for _ in range(n)]

    for rho in range(n):
        for sigma in range(n):
            for mu in range(n):
                for nu in range(n):
                    # ∂_μ Γ^ρ_νσ - ∂_ν Γ^ρ_μσ
                    term1 = diff(christoffel[rho, nu, sigma], coords[mu])
                    term2 = diff(christoffel[rho, mu, sigma], coords[nu])

                    # Γ^ρ_μλ Γ^λ_νσ - Γ^ρ_νλ Γ^λ_μσ
                    term3: Expr = Integer(0)
                    term4: Expr = Integer(0)
                    for lam in range(n):
                        term3 += christoffel[rho, mu, lam] * christoffel[lam, nu, sigma]
                        term4 += christoffel[rho, nu, lam] * christoffel[lam, mu, sigma]

                    R[rho][sigma][mu][nu] = term1 - term2 + term3 - term4

    return ImmutableDenseNDimArray(R)


def compute_ricci(riemann: ImmutableDenseNDimArray) -> ImmutableDenseNDimArray:
    """
    Compute the Ricci tensor by contracting the first and third indices of Riemann.

    R_μν = R^ρ_μρν

    Parameters
    ----------
    riemann : ImmutableDenseNDimArray, shape (n, n, n, n)
        Riemann tensor R^ρ_σμν indexed as [ρ, σ, μ, ν].

    Returns
    -------
    ImmutableDenseNDimArray, shape (n, n)
        Ricci tensor R_μν indexed as [μ, ν].
    """
    n = riemann.shape[0]
    ricci = [[Integer(0)] * n for _ in range(n)]

    for mu in range(n):
        for nu in range(n):
            ricci[mu][nu] = sum(
                riemann[rho, mu, rho, nu] for rho in range(n)
            )

    return ImmutableDenseNDimArray(ricci)


def compute_ricci_scalar(
    metric_inv: Matrix,
    ricci: ImmutableDenseNDimArray,
) -> Expr:
    """
    Compute the Ricci scalar by contracting the Ricci tensor with the inverse metric.

    R = g^μν R_μν

    Parameters
    ----------
    metric_inv : sympy.Matrix
        Contravariant metric tensor g^μν.
    ricci : ImmutableDenseNDimArray, shape (n, n)
        Ricci tensor R_μν.

    Returns
    -------
    sympy.Expr
        The Ricci scalar R.
    """
    n = ricci.shape[0]
    return sum(
        metric_inv[mu, nu] * ricci[mu, nu]
        for mu in range(n)
        for nu in range(n)
    )


def compute_einstein(
    metric: Matrix,
    ricci: ImmutableDenseNDimArray,
    ricci_scalar: Expr,
) -> ImmutableDenseNDimArray:
    """
    Compute the Einstein tensor.

    G_μν = R_μν - ½ R g_μν

    Parameters
    ----------
    metric : sympy.Matrix
        Covariant metric tensor g_μν.
    ricci : ImmutableDenseNDimArray, shape (n, n)
        Ricci tensor R_μν.
    ricci_scalar : sympy.Expr
        Ricci scalar R.

    Returns
    -------
    ImmutableDenseNDimArray, shape (n, n)
        Einstein tensor G_μν indexed as [μ, ν].
    """
    n = metric.shape[0]
    G = [[Integer(0)] * n for _ in range(n)]

    for mu in range(n):
        for nu in range(n):
            G[mu][nu] = ricci[mu, nu] - (ricci_scalar * metric[mu, nu]) / 2

    return ImmutableDenseNDimArray(G)


def simplify_array(arr: ImmutableDenseNDimArray) -> ImmutableDenseNDimArray:
    """
    Apply sympy.simplify to every component of a tensor array.

    This can be slow for large tensors. Consider using trigsimp or
    radsimp for specific metric types if performance is a concern.

    Parameters
    ----------
    arr : ImmutableDenseNDimArray
        Input tensor.

    Returns
    -------
    ImmutableDenseNDimArray
        Tensor with each component simplified.
    """
    return ImmutableDenseNDimArray([simplify(c) for c in arr]).reshape(*arr.shape)
