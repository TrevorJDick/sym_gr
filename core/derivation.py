"""
core/derivation.py
------------------
Step-by-step derivation data for tensor computations.

Computes the same quantities as core/tensors.py but stores every
intermediate partial derivative and ρ-summation term so the UI can
render a full step-by-step derivation — including the terms that
vanish, and why they vanish.

No Streamlit dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from sympy import Expr, Integer, diff
from sympy import Matrix
from sympy.tensor.array import ImmutableDenseNDimArray


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RhoTerm:
    """One ρ-summation term in the Christoffel formula for a single (σ,μ,ν)."""
    rho: int
    g_inv: Expr       # g^σρ
    d1: Expr          # ∂_μ g_νρ
    d2: Expr          # ∂_ν g_μρ
    d3: Expr          # ∂_ρ g_μν
    bracket: Expr     # d1 + d2 - d3
    contribution: Expr  # g^σρ * bracket / 2

    @property
    def is_zero(self) -> bool:
        return self.contribution == Integer(0)

    @property
    def g_inv_zero(self) -> bool:
        return self.g_inv == Integer(0)

    @property
    def bracket_zero(self) -> bool:
        return self.bracket == Integer(0)

    def zero_reasons(self, coords) -> list[str]:
        """
        Return list of LaTeX strings explaining why this term is zero.
        Each string is a short equation like r'g^{t r} = 0'.
        """
        from sympy import latex
        reasons: list[str] = []
        sig_tex = latex(coords[self.rho])  # reused below — note: caller provides parent sigma
        if self.g_inv_zero:
            return [rf"g^{{\sigma {latex(coords[self.rho])}}} = 0"]
        if self.d1 == Integer(0):
            reasons.append(rf"\partial_\mu g_{{\nu {latex(coords[self.rho])}}} = 0")
        if self.d2 == Integer(0):
            reasons.append(rf"\partial_\nu g_{{\mu {latex(coords[self.rho])}}} = 0")
        if self.d3 == Integer(0):
            reasons.append(rf"\partial_{latex(coords[self.rho])} g_{{\mu\nu}} = 0")
        if not reasons:
            reasons.append(r"\text{bracket} = 0")
        return reasons


@dataclass
class ChristoffelStep:
    """Full derivation record for one Christoffel component Γ^σ_μν."""
    sigma: int
    mu: int
    nu: int
    value: Expr                  # final computed value
    rho_terms: list[RhoTerm]     # one term per ρ index

    @property
    def is_zero(self) -> bool:
        return self.value == Integer(0)

    @property
    def nonzero_rho_count(self) -> int:
        return sum(1 for t in self.rho_terms if not t.is_zero)


@dataclass
class RiemannStep:
    """Full derivation record for one Riemann component R^ρ_σμν."""
    rho: int
    sigma: int
    mu: int
    nu: int
    value: Expr
    # Four named terms
    term1: Expr   # ∂_μ Γ^ρ_νσ
    term2: Expr   # ∂_ν Γ^ρ_μσ
    term3: Expr   # Σ_λ Γ^ρ_μλ Γ^λ_νσ
    term4: Expr   # Σ_λ Γ^ρ_νλ Γ^λ_μσ

    @property
    def is_zero(self) -> bool:
        return self.value == Integer(0)


# ---------------------------------------------------------------------------
# Computation functions
# ---------------------------------------------------------------------------

def christoffel_steps(
    coords: Sequence[Expr],
    metric: Matrix,
    metric_inv: Matrix,
) -> dict[tuple[int, int, int], ChristoffelStep]:
    """
    Compute all Christoffel symbols with full intermediate data.

    Γ^σ_μν = ½ g^σρ (∂_μ g_νρ + ∂_ν g_μρ - ∂_ρ g_μν)

    Returns
    -------
    dict mapping (σ, μ, ν) → ChristoffelStep
        All n³ combinations are included (not just μ ≤ ν).
    """
    n = len(coords)

    # Pre-compute all metric partial derivatives:  partials[alpha, mu, nu] = ∂_alpha g_mu_nu
    partials: dict[tuple[int, int, int], Expr] = {}
    for alpha in range(n):
        for mu in range(n):
            for nu in range(n):
                partials[(alpha, mu, nu)] = diff(metric[mu, nu], coords[alpha])

    steps: dict[tuple[int, int, int], ChristoffelStep] = {}

    for sigma in range(n):
        for mu in range(n):
            for nu in range(n):
                total: Expr = Integer(0)
                rho_terms: list[RhoTerm] = []

                for rho in range(n):
                    g_inv_val = metric_inv[sigma, rho]
                    d1 = partials[(mu, nu, rho)]   # ∂_μ g_νρ
                    d2 = partials[(nu, mu, rho)]   # ∂_ν g_μρ
                    d3 = partials[(rho, mu, nu)]   # ∂_ρ g_μν
                    bracket = d1 + d2 - d3
                    contribution = g_inv_val * bracket / 2
                    total = total + contribution

                    rho_terms.append(RhoTerm(
                        rho=rho,
                        g_inv=g_inv_val,
                        d1=d1,
                        d2=d2,
                        d3=d3,
                        bracket=bracket,
                        contribution=contribution,
                    ))

                steps[(sigma, mu, nu)] = ChristoffelStep(
                    sigma=sigma,
                    mu=mu,
                    nu=nu,
                    value=total,
                    rho_terms=rho_terms,
                )

    return steps


def riemann_steps(
    coords: Sequence[Expr],
    christoffel: ImmutableDenseNDimArray,
) -> dict[tuple[int, int, int, int], RiemannStep]:
    """
    Compute Riemann tensor components with named intermediate terms.

    R^ρ_σμν = ∂_μ Γ^ρ_νσ - ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ - Γ^ρ_νλ Γ^λ_μσ

    Returns
    -------
    dict mapping (ρ, σ, μ, ν) → RiemannStep
    """
    n = len(coords)
    steps: dict[tuple[int, int, int, int], RiemannStep] = {}

    for rho in range(n):
        for sigma in range(n):
            for mu in range(n):
                for nu in range(n):
                    t1 = diff(christoffel[rho, nu, sigma], coords[mu])
                    t2 = diff(christoffel[rho, mu, sigma], coords[nu])
                    t3: Expr = Integer(0)
                    t4: Expr = Integer(0)
                    for lam in range(n):
                        t3 = t3 + christoffel[rho, mu, lam] * christoffel[lam, nu, sigma]
                        t4 = t4 + christoffel[rho, nu, lam] * christoffel[lam, mu, sigma]

                    value = t1 - t2 + t3 - t4
                    steps[(rho, sigma, mu, nu)] = RiemannStep(
                        rho=rho, sigma=sigma, mu=mu, nu=nu,
                        value=value,
                        term1=t1, term2=t2, term3=t3, term4=t4,
                    )

    return steps
