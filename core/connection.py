"""
core/connection.py
------------------
Affine connection for a spacetime manifold.

Three construction modes let researchers explore beyond the standard
Levi-Civita connection:

  1. levi_civita   — torsion-free, metric-compatible (default behaviour)
  2. torsion       — LC connection + contorsion built from a user-supplied
                     torsion tensor T^σ_μν
  3. full          — all Γ^σ_μν specified directly; no symmetry assumed

The Riemann / Ricci / Einstein pipeline (core/tensors.py) only needs the
connection coefficients array, so all three modes feed seamlessly into the
existing computation.

Index conventions (Carroll):
  Connection coefficients  Γ^σ_μν   stored as  [σ, μ, ν]
  Torsion tensor           T^σ_μν   stored as  [σ, μ, ν]  (antisym in μ, ν)
  Contorsion tensor        K^σ_μν   stored as  [σ, μ, ν]
"""

from __future__ import annotations

from typing import Sequence

from sympy import Expr, Integer, Matrix
from sympy.tensor.array import ImmutableDenseNDimArray

from .tensors import compute_christoffel


class Connection:
    """
    An affine connection on a spacetime manifold.

    Stores the full set of connection coefficients Γ^σ_μν as an (n, n, n)
    ImmutableDenseNDimArray.  For the Levi-Civita connection the coefficients
    are the standard Christoffel symbols; for torsion / full mode they may be
    asymmetric in the lower indices.

    Use the class-method constructors rather than ``__init__`` directly.

    Parameters
    ----------
    coefficients : ImmutableDenseNDimArray, shape (n, n, n)
        Γ^σ_μν indexed [σ, μ, ν].
    mode : {'levi_civita', 'torsion', 'full'}
        Records how the connection was built.
    torsion_input : ImmutableDenseNDimArray or None
        User-supplied T^σ_μν (only set for mode='torsion').
    """

    def __init__(
        self,
        coefficients: ImmutableDenseNDimArray,
        mode: str = "levi_civita",
        torsion_input: ImmutableDenseNDimArray | None = None,
    ) -> None:
        self._coefficients = coefficients
        self.mode = mode
        self._torsion_input = torsion_input

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def levi_civita(
        cls,
        coords: Sequence[Expr],
        metric: Matrix,
        metric_inv: Matrix,
    ) -> "Connection":
        """Standard torsion-free metric-compatible (Levi-Civita) connection."""
        gamma = compute_christoffel(coords, metric, metric_inv)
        return cls(gamma, mode="levi_civita")

    @classmethod
    def from_metric_and_torsion(
        cls,
        coords: Sequence[Expr],
        metric: Matrix,
        metric_inv: Matrix,
        torsion: ImmutableDenseNDimArray,
    ) -> "Connection":
        """
        Build a metric-compatible connection with torsion.

        Γ^σ_μν = {^σ_μν} + K^σ_μν

        where {^σ_μν} are the LC Christoffel symbols and K^σ_μν is the
        contorsion derived from the user-supplied torsion tensor.

        Parameters
        ----------
        torsion : ImmutableDenseNDimArray, shape (n, n, n)
            T^σ_μν indexed [σ, μ, ν].  Must be antisymmetric in the last
            two indices (T^σ_μν = -T^σ_νμ).
        """
        n = len(coords)
        lc = compute_christoffel(coords, metric, metric_inv)
        K = _compute_contorsion(metric, metric_inv, torsion, n)
        coeffs = [
            [
                [lc[s, mu, nu] + K[s, mu, nu] for nu in range(n)]
                for mu in range(n)
            ]
            for s in range(n)
        ]
        return cls(
            ImmutableDenseNDimArray(coeffs),
            mode="torsion",
            torsion_input=torsion,
        )

    @classmethod
    def from_coefficients(
        cls,
        coefficients: ImmutableDenseNDimArray,
    ) -> "Connection":
        """
        Directly specified connection coefficients — no symmetry assumed.

        This is the most general mode: the researcher supplies all n³
        entries of Γ^σ_μν freely.
        """
        return cls(coefficients, mode="full")

    # ------------------------------------------------------------------
    # Derived quantities
    # ------------------------------------------------------------------

    @property
    def coefficients(self) -> ImmutableDenseNDimArray:
        """Full Γ^σ_μν, shape (n, n, n), indexed [σ, μ, ν]."""
        return self._coefficients

    def torsion(self) -> ImmutableDenseNDimArray:
        """
        Torsion tensor T^σ_μν = Γ^σ_μν − Γ^σ_νμ, shape (n, n, n).

        For 'levi_civita' mode this is identically zero.
        For 'torsion' mode returns the user-supplied tensor directly.
        For 'full' mode computes the antisymmetric part of the coefficients.
        """
        if self.mode == "torsion" and self._torsion_input is not None:
            return self._torsion_input
        n = self._coefficients.shape[0]
        T = [
            [
                [
                    self._coefficients[s, mu, nu] - self._coefficients[s, nu, mu]
                    for nu in range(n)
                ]
                for mu in range(n)
            ]
            for s in range(n)
        ]
        return ImmutableDenseNDimArray(T)

    def contorsion(
        self,
        metric: Matrix,
        metric_inv: Matrix,
    ) -> ImmutableDenseNDimArray:
        """
        Contorsion K^σ_μν = Γ^σ_μν − {^σ_μν}, shape (n, n, n).

        For 'levi_civita' mode returns the zero tensor.
        For other modes computes K from the torsion tensor via index gymnastics.
        """
        n = self._coefficients.shape[0]
        if self.mode == "levi_civita":
            return ImmutableDenseNDimArray(
                [[[Integer(0)] * n for _ in range(n)] for _ in range(n)]
            )
        return _compute_contorsion(metric, metric_inv, self.torsion(), n)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_contorsion(
    metric: Matrix,
    metric_inv: Matrix,
    torsion: ImmutableDenseNDimArray,
    n: int,
) -> ImmutableDenseNDimArray:
    """
    Compute the contorsion tensor K^σ_μν from the torsion tensor T^σ_μν.

    Algorithm
    ---------
    Step 1 — lower the first index of the torsion:
        t_λμν = g_λσ T^σ_μν

    Step 2 — build fully-covariant contorsion (antisymmetric in λ, μ):
        K_λμν = ½ (t_λμν − t_μλν − t_νλμ)

    Step 3 — raise the first index:
        K^σ_μν = g^σλ K_λμν

    This ensures the connection Γ = LC + K remains metric-compatible
    (∇_ρ g_μν = 0).

    Parameters
    ----------
    torsion : ImmutableDenseNDimArray, shape (n, n, n)
        T^σ_μν indexed [σ, μ, ν], antisymmetric in the last two indices.
    """
    # Step 1: t_λμν = g_λσ T^σ_μν
    t_low = [
        [
            [
                sum(metric[lam, s] * torsion[s, mu, nu] for s in range(n))
                for nu in range(n)
            ]
            for mu in range(n)
        ]
        for lam in range(n)
    ]

    # Step 2: K_λμν = ½(t_λμν - t_μλν - t_νλμ)
    K_low = [
        [
            [
                (t_low[lam][mu][nu] - t_low[mu][lam][nu] - t_low[nu][lam][mu]) / 2
                for nu in range(n)
            ]
            for mu in range(n)
        ]
        for lam in range(n)
    ]

    # Step 3: K^σ_μν = g^σλ K_λμν
    K = [
        [
            [
                sum(metric_inv[s, lam] * K_low[lam][mu][nu] for lam in range(n))
                for nu in range(n)
            ]
            for mu in range(n)
        ]
        for s in range(n)
    ]

    return ImmutableDenseNDimArray(K)
