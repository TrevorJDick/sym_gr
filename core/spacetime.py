"""
core/spacetime.py
-----------------
The Spacetime class: the primary entry point for all tensor computations.

A Spacetime is defined by a set of coordinates and a covariant metric tensor.
All derived quantities (Christoffel symbols, Riemann tensor, etc.) are computed
lazily on first access and cached.

Example
-------
>>> from sympy import symbols, Function, sin, diag
>>> from core.spacetime import Spacetime
>>>
>>> t, r, theta, phi = symbols('t r theta phi')
>>> A, B = Function('A')(r), Function('B')(r)
>>> metric = diag(-A, B, r**2, r**2 * sin(theta)**2)
>>> st = Spacetime([t, r, theta, phi], metric)
>>> st.einstein()
"""

from __future__ import annotations

from typing import Sequence

from sympy import Expr, Matrix
from sympy.tensor.array import ImmutableDenseNDimArray

from .tensors import (
    compute_christoffel,
    compute_einstein,
    compute_metric_inverse,
    compute_ricci,
    compute_ricci_scalar,
    compute_riemann,
    simplify_array,
)


class Spacetime:
    """
    A pseudo-Riemannian spacetime defined by coordinates and a metric.

    Parameters
    ----------
    coords : sequence of sympy.Expr
        Ordered coordinate symbols, e.g. ``[t, r, theta, phi]``.
        Must match the dimension of the metric matrix.
    metric : sympy.Matrix or array-like
        The covariant metric tensor g_μν as an n×n SymPy Matrix.
        Off-diagonal entries should be set to zero explicitly for
        diagonal metrics rather than left out.

    Notes
    -----
    All tensor results are returned unsimplified by default to keep the
    pipeline transparent. Call ``simplify_array()`` from ``core.tensors``
    or use the ``simplified=True`` parameter where available.
    """

    def __init__(
        self,
        coords: Sequence[Expr],
        metric: Matrix,
    ) -> None:
        self.coords = list(coords)
        self.metric = Matrix(metric) if not isinstance(metric, Matrix) else metric

        if self.metric.shape != (len(coords), len(coords)):
            raise ValueError(
                f"Metric shape {self.metric.shape} does not match "
                f"number of coordinates ({len(coords)})."
            )

        # Cached results — computed on first access
        self._metric_inv: Matrix | None = None
        self._christoffel: ImmutableDenseNDimArray | None = None
        self._riemann: ImmutableDenseNDimArray | None = None
        self._ricci: ImmutableDenseNDimArray | None = None
        self._ricci_scalar: Expr | None = None
        self._einstein: ImmutableDenseNDimArray | None = None

    @property
    def n(self) -> int:
        """Spacetime dimension."""
        return len(self.coords)

    # ------------------------------------------------------------------
    # Derived tensors
    # ------------------------------------------------------------------

    def metric_inverse(self) -> Matrix:
        """
        Contravariant metric tensor g^μν.

        Returns
        -------
        sympy.Matrix, shape (n, n)
        """
        if self._metric_inv is None:
            self._metric_inv = compute_metric_inverse(self.metric)
        return self._metric_inv

    def christoffel(self, simplified: bool = False) -> ImmutableDenseNDimArray:
        """
        Christoffel symbols of the second kind Γ^σ_μν.

        Index order: [σ, μ, ν]

        Parameters
        ----------
        simplified : bool
            If True, apply sympy.simplify to every component.
            Can be slow for large symbolic metrics.

        Returns
        -------
        ImmutableDenseNDimArray, shape (n, n, n)
        """
        if self._christoffel is None:
            self._christoffel = compute_christoffel(
                self.coords, self.metric, self.metric_inverse()
            )
        result = self._christoffel
        return simplify_array(result) if simplified else result

    def riemann(self, simplified: bool = False) -> ImmutableDenseNDimArray:
        """
        Riemann curvature tensor R^ρ_σμν.

        Index order: [ρ, σ, μ, ν]

        Uses the Carroll convention:
        R^ρ_σμν = ∂_μ Γ^ρ_νσ - ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ - Γ^ρ_νλ Γ^λ_μσ

        Parameters
        ----------
        simplified : bool
            If True, apply sympy.simplify to every component.

        Returns
        -------
        ImmutableDenseNDimArray, shape (n, n, n, n)
        """
        if self._riemann is None:
            self._riemann = compute_riemann(self.coords, self.christoffel())
        result = self._riemann
        return simplify_array(result) if simplified else result

    def ricci(self, simplified: bool = False) -> ImmutableDenseNDimArray:
        """
        Ricci tensor R_μν = R^ρ_μρν.

        Index order: [μ, ν]

        Parameters
        ----------
        simplified : bool
            If True, apply sympy.simplify to every component.

        Returns
        -------
        ImmutableDenseNDimArray, shape (n, n)
        """
        if self._ricci is None:
            self._ricci = compute_ricci(self.riemann())
        result = self._ricci
        return simplify_array(result) if simplified else result

    def ricci_scalar(self, simplified: bool = False) -> Expr:
        """
        Ricci scalar R = g^μν R_μν.

        Parameters
        ----------
        simplified : bool
            If True, apply sympy.simplify to the result.

        Returns
        -------
        sympy.Expr
        """
        if self._ricci_scalar is None:
            self._ricci_scalar = compute_ricci_scalar(
                self.metric_inverse(), self.ricci()
            )
        result = self._ricci_scalar
        from sympy import simplify as sp_simplify
        return sp_simplify(result) if simplified else result

    def einstein(self, simplified: bool = False) -> ImmutableDenseNDimArray:
        """
        Einstein tensor G_μν = R_μν - ½ R g_μν.

        Index order: [μ, ν]

        Parameters
        ----------
        simplified : bool
            If True, apply sympy.simplify to every component.

        Returns
        -------
        ImmutableDenseNDimArray, shape (n, n)
        """
        if self._einstein is None:
            self._einstein = compute_einstein(
                self.metric, self.ricci(), self.ricci_scalar()
            )
        result = self._einstein
        return simplify_array(result) if simplified else result

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        coords_str = ", ".join(str(c) for c in self.coords)
        return f"Spacetime(coords=[{coords_str}], metric={self.metric})"
