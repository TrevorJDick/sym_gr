"""
ui/display.py
-------------
Render SymPy objects as LaTeX in a Streamlit app.

No parsing, no core computation calls — pure display utilities.
"""

from __future__ import annotations

from itertools import product as iproduct

import streamlit as st
from sympy import latex, Symbol
from sympy.tensor.array import ImmutableDenseNDimArray


def _coord_label(sym: Symbol) -> str:
    """Return the LaTeX string for a coordinate symbol."""
    return latex(sym)


def display_metric_preview(metric, coords: list) -> None:
    """Render the metric matrix as LaTeX."""
    from sympy import Matrix
    m = Matrix(metric) if not isinstance(metric, Matrix) else metric
    st.latex(latex(m))


def display_rank3_nonzero(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display non-zero Christoffel symbol components.

    Groups by upper index σ; only shows μ ≤ ν (lower symmetry).
    """
    n = tensor.shape[0]
    any_nonzero = False

    for sigma in range(n):
        group_lines: list[str] = []
        for mu in range(n):
            for nu in range(mu, n):
                val = tensor[sigma, mu, nu]
                if val == 0:
                    continue
                any_nonzero = True
                mu_lbl = _coord_label(coords[mu])
                nu_lbl = _coord_label(coords[nu])
                sig_lbl = _coord_label(coords[sigma])
                lhs = rf"\Gamma^{{{sig_lbl}}}_{{{mu_lbl} {nu_lbl}}}"
                group_lines.append(rf"{lhs} = {latex(val)}")

        if group_lines:
            st.latex(r" \\ ".join(group_lines))

    if not any_nonzero:
        st.info("All Christoffel symbols are zero.")


def display_rank3_all(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display ALL Christoffel components (μ ≤ ν), including zeros.

    Zero entries are shown dimmed.
    """
    n = tensor.shape[0]
    for sigma in range(n):
        sig_lbl = _coord_label(coords[sigma])
        lines: list[tuple[str, bool]] = []
        for mu in range(n):
            for nu in range(mu, n):
                val = tensor[sigma, mu, nu]
                mu_lbl = _coord_label(coords[mu])
                nu_lbl = _coord_label(coords[nu])
                lhs = rf"\Gamma^{{{sig_lbl}}}_{{{mu_lbl} {nu_lbl}}}"
                lines.append((rf"{lhs} = {latex(val)}", val == 0))

        if lines:
            # Render nonzero first as normal LaTeX, zeros as a dimmed block
            nonzero = [l for l, z in lines if not z]
            zero    = [l for l, z in lines if z]
            if nonzero:
                st.latex(r" \\ ".join(nonzero))
            if zero:
                st.markdown(
                    '<span style="opacity:0.4;">'
                    + r" $\quad$ ".join(f"${l}$" for l in zero)
                    + "</span>",
                    unsafe_allow_html=True,
                )


def display_rank4_nonzero(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display non-zero Riemann tensor components.

    Groups by (ρ, σ); only shows μ < ν (antisymmetry in last two indices).
    """
    n = tensor.shape[0]
    any_nonzero = False

    for rho in range(n):
        for sigma in range(n):
            group_lines: list[str] = []
            for mu in range(n):
                for nu in range(mu + 1, n):
                    val = tensor[rho, sigma, mu, nu]
                    if val == 0:
                        continue
                    any_nonzero = True
                    rho_lbl = _coord_label(coords[rho])
                    sig_lbl = _coord_label(coords[sigma])
                    mu_lbl = _coord_label(coords[mu])
                    nu_lbl = _coord_label(coords[nu])
                    lhs = rf"R^{{{rho_lbl}}}_{{{sig_lbl} {mu_lbl} {nu_lbl}}}"
                    group_lines.append(rf"{lhs} = {latex(val)}")

            if group_lines:
                st.latex(r" \\ ".join(group_lines))

    if not any_nonzero:
        st.info("All Riemann components are zero.")


def display_rank4_all(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display ALL Riemann components (μ < ν), including zeros.
    """
    n = tensor.shape[0]
    for rho in range(n):
        for sigma in range(n):
            lines: list[tuple[str, bool]] = []
            for mu in range(n):
                for nu in range(mu + 1, n):
                    val = tensor[rho, sigma, mu, nu]
                    rho_lbl = _coord_label(coords[rho])
                    sig_lbl = _coord_label(coords[sigma])
                    mu_lbl  = _coord_label(coords[mu])
                    nu_lbl  = _coord_label(coords[nu])
                    lhs = rf"R^{{{rho_lbl}}}_{{{sig_lbl} {mu_lbl} {nu_lbl}}}"
                    lines.append((rf"{lhs} = {latex(val)}", val == 0))

            if lines:
                nonzero = [l for l, z in lines if not z]
                zero    = [l for l, z in lines if z]
                if nonzero:
                    st.latex(r" \\ ".join(nonzero))
                if zero:
                    st.markdown(
                        '<span style="opacity:0.4;">'
                        + r" $\quad$ ".join(f"${l}$" for l in zero)
                        + "</span>",
                        unsafe_allow_html=True,
                    )


def display_rank2_nonzero(
    tensor: ImmutableDenseNDimArray,
    coords: list,
    name: str,
    symmetry: bool = True,
    show_zeros: bool = False,
) -> None:
    """
    Display components of a rank-2 tensor (Ricci or Einstein).

    Parameters
    ----------
    name : str
        LaTeX base name, e.g. ``"R"`` or ``"G"``.
    symmetry : bool
        If True, only show upper triangle (μ ≤ ν).
    show_zeros : bool
        If True, also show zero components (dimmed).
    """
    n = tensor.shape[0]
    any_nonzero = False
    zero_lines: list[str] = []

    for mu in range(n):
        nu_range = range(mu, n) if symmetry else range(n)
        for nu in nu_range:
            val = tensor[mu, nu]
            mu_lbl = _coord_label(coords[mu])
            nu_lbl = _coord_label(coords[nu])
            lhs = rf"{name}_{{{mu_lbl} {nu_lbl}}}"
            if val == 0:
                zero_lines.append(rf"{lhs} = 0")
                continue
            any_nonzero = True
            st.latex(rf"{lhs} = {latex(val)}")

    if show_zeros and zero_lines:
        st.markdown(
            '<span style="opacity:0.4;">'
            + r" $\quad$ ".join(f"${l}$" for l in zero_lines)
            + "</span>",
            unsafe_allow_html=True,
        )

    if not any_nonzero and not show_zeros:
        st.info("All components are zero.")


def display_scalar(expr, name: str) -> None:
    """Render a scalar quantity as ``name = value``."""
    st.latex(rf"{name} = {latex(expr)}")


def display_equations(eqs: list, start_index: int = 1) -> None:
    """
    Render a numbered list of equations as LaTeX.

    Parameters
    ----------
    eqs : list of sympy.Eq
        Equations to display.
    start_index : int
        Number of the first equation (default 1). Pass a higher value to
        continue numbering from a previous block (e.g. constrained equations
        continuing after field equations).

    Shows a success message if the list is empty (all equations satisfied).
    """
    if not eqs:
        st.success("All equations are satisfied (0 remaining).")
        return

    for i, eq in enumerate(eqs, start=start_index):
        from sympy import Eq
        lhs_str = latex(eq.lhs)
        rhs_str = latex(eq.rhs)
        st.latex(rf"({i})\quad {lhs_str} = {rhs_str}")
