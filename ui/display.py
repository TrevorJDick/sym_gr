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


def _lhs_rank3(coords: list, sigma: int, mu: int, nu: int) -> str:
    """
    LHS label for a Christoffel symbol.

    Off-diagonal (μ ≠ ν): ``Γ^σ_μν = Γ^σ_νμ`` to show lower-index symmetry.
    Diagonal (μ = ν): ``Γ^σ_μμ``.
    """
    sig = _coord_label(coords[sigma])
    m   = _coord_label(coords[mu])
    nv  = _coord_label(coords[nu])
    base = rf"\Gamma^{{{sig}}}_{{{m} {nv}}}"
    if mu == nu:
        return base
    sym = rf"\Gamma^{{{sig}}}_{{{nv} {m}}}"
    return rf"{base} = {sym}"


def _lhs_rank4(coords: list, rho: int, sigma: int, mu: int, nu: int) -> str:
    """
    LHS label for a Riemann tensor component.

    Off-diagonal (μ ≠ ν): ``R^ρ_σμν = -R^ρ_σνμ`` to show last-index antisymmetry.
    Diagonal (μ = ν): ``R^ρ_σμμ`` (structurally zero).
    """
    r  = _coord_label(coords[rho])
    s  = _coord_label(coords[sigma])
    m  = _coord_label(coords[mu])
    nv = _coord_label(coords[nu])
    base = rf"R^{{{r}}}_{{{s} {m} {nv}}}"
    if mu == nu:
        return base
    anti = rf"R^{{{r}}}_{{{s} {nv} {m}}}"
    return rf"{base} = -{anti}"


def _lhs_rank2(name: str, coords: list, mu: int, nu: int) -> str:
    """
    LHS label for a rank-2 symmetric tensor component.

    Off-diagonal (μ ≠ ν): ``name_μν = name_νμ`` to show symmetry.
    Diagonal (μ = ν): ``name_μμ``.
    """
    m  = _coord_label(coords[mu])
    nv = _coord_label(coords[nu])
    base = rf"{name}_{{{m} {nv}}}"
    if mu == nu:
        return base
    sym = rf"{name}_{{{nv} {m}}}"
    return rf"{base} = {sym}"


def display_metric_preview(metric, coords: list) -> None:
    """Render the metric matrix as LaTeX."""
    from sympy import Matrix
    m = Matrix(metric) if not isinstance(metric, Matrix) else metric
    st.latex(latex(m))


def display_rank3_nonzero(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display non-zero Christoffel symbol components.

    Groups by upper index σ. Off-diagonal pairs (μ < ν) are shown as
    ``Γ^σ_μν = Γ^σ_νμ = value`` to make the lower-index symmetry explicit.
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
                lhs = _lhs_rank3(coords, sigma, mu, nu)
                group_lines.append(rf"{lhs} = {latex(val)}")

        if group_lines:
            st.latex(r" \\ ".join(group_lines))

    if not any_nonzero:
        st.info("All Christoffel symbols are zero.")


def display_rank3_all(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display ALL Christoffel components (μ ≤ ν), including zeros.

    Zero entries are shown dimmed. Off-diagonal pairs show the symmetry:
    ``Γ^σ_μν = Γ^σ_νμ = value``.
    """
    n = tensor.shape[0]
    for sigma in range(n):
        lines: list[tuple[str, bool]] = []
        for mu in range(n):
            for nu in range(mu, n):
                val = tensor[sigma, mu, nu]
                lhs = _lhs_rank3(coords, sigma, mu, nu)
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


def display_rank4_nonzero(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display non-zero Riemann tensor components.

    Groups by (ρ, σ). Each off-diagonal pair (μ < ν) is shown as
    ``R^ρ_σμν = -R^ρ_σνμ = value`` to make the last-index antisymmetry explicit.
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
                    lhs = _lhs_rank4(coords, rho, sigma, mu, nu)
                    group_lines.append(rf"{lhs} = {latex(val)}")

            if group_lines:
                st.latex(r" \\ ".join(group_lines))

    if not any_nonzero:
        st.info("All Riemann components are zero.")


def display_rank4_all(tensor: ImmutableDenseNDimArray, coords: list) -> None:
    """
    Display ALL Riemann components (μ ≤ ν), including zeros.

    Off-diagonal pairs show antisymmetry: ``R^ρ_σμν = -R^ρ_σνμ = value``.
    Diagonal entries (μ = ν, structurally zero) are included in the dimmed block.
    """
    n = tensor.shape[0]
    for rho in range(n):
        for sigma in range(n):
            nonzero_lines: list[str] = []
            zero_lines: list[str] = []
            for mu in range(n):
                for nu in range(mu, n):          # include diagonal (always zero)
                    val = tensor[rho, sigma, mu, nu]
                    lhs = _lhs_rank4(coords, rho, sigma, mu, nu)
                    entry = rf"{lhs} = {latex(val)}"
                    if val == 0:
                        zero_lines.append(entry)
                    else:
                        nonzero_lines.append(entry)

            if nonzero_lines or zero_lines:
                if nonzero_lines:
                    st.latex(r" \\ ".join(nonzero_lines))
                if zero_lines:
                    st.markdown(
                        '<span style="opacity:0.4;">'
                        + r" $\quad$ ".join(f"${l}$" for l in zero_lines)
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
            if symmetry:
                lhs = _lhs_rank2(name, coords, mu, nu)
            else:
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


def display_rank3_antisym_nonzero(
    tensor: ImmutableDenseNDimArray,
    coords: list,
    tensor_symbol: str = "T",
) -> None:
    """
    Display non-zero components of a rank-3 tensor antisymmetric in its
    last two indices (e.g. the torsion tensor T^σ_μν).

    Groups by upper index σ.  For each pair (μ < ν) shows:
        tensor_symbol^σ_μν = −tensor_symbol^σ_νμ = value

    Parameters
    ----------
    tensor_symbol : str
        LaTeX symbol for the tensor, e.g. ``"T"`` or ``"K"``.
    """
    n = tensor.shape[0]
    any_nonzero = False

    for sigma in range(n):
        group_lines: list[str] = []
        for mu in range(n):
            for nu in range(mu + 1, n):
                val = tensor[sigma, mu, nu]
                if val == 0:
                    continue
                any_nonzero = True
                s = _coord_label(coords[sigma])
                m = _coord_label(coords[mu])
                nv = _coord_label(coords[nu])
                lhs = (
                    rf"{tensor_symbol}^{{{s}}}_{{{m} {nv}}} = "
                    rf"-{tensor_symbol}^{{{s}}}_{{{nv} {m}}}"
                )
                group_lines.append(rf"{lhs} = {latex(val)}")

        if group_lines:
            st.latex(r" \\ ".join(group_lines))

    if not any_nonzero:
        st.info(f"All {tensor_symbol}^σ_μν components are zero.")


def display_rank3_general_nonzero(
    tensor: ImmutableDenseNDimArray,
    coords: list,
    tensor_symbol: str = r"\Gamma",
) -> None:
    """
    Display non-zero components of a general rank-3 tensor Γ^σ_μν with
    no assumed symmetry in the lower indices.

    Groups by upper index σ.

    Parameters
    ----------
    tensor_symbol : str
        LaTeX symbol for the tensor, default ``\\Gamma``.
    """
    n = tensor.shape[0]
    any_nonzero = False

    for sigma in range(n):
        group_lines: list[str] = []
        for mu in range(n):
            for nu in range(n):
                val = tensor[sigma, mu, nu]
                if val == 0:
                    continue
                any_nonzero = True
                s = _coord_label(coords[sigma])
                m = _coord_label(coords[mu])
                nv = _coord_label(coords[nu])
                lhs = rf"{tensor_symbol}^{{{s}}}_{{{m} {nv}}}"
                group_lines.append(rf"{lhs} = {latex(val)}")

        if group_lines:
            st.latex(r" \\ ".join(group_lines))

    if not any_nonzero:
        st.info(f"All {tensor_symbol}^σ_μν components are zero.")


def display_scalar(expr, name: str) -> None:
    """Render a scalar quantity as ``name = value``."""
    st.latex(rf"{name} = {latex(expr)}")


def display_equations_labeled(
    eqs: list,
    labels: list,
    coords: list,
    start_index: int = 1,
) -> None:
    """
    Render a numbered list of equations as LaTeX with (μ, ν) index labels.

    Parameters
    ----------
    eqs : list of sympy.Eq
    labels : list of (int, int)
        The (mu, nu) tensor-index pair for each equation.
    coords : list
        Coordinate symbols.
    start_index : int
        Number of the first equation.
    """
    if not eqs:
        st.success("All equations are satisfied (0 remaining).")
        return

    for i, (eq, (mu, nu)) in enumerate(zip(eqs, labels), start=start_index):
        mu_label = latex(coords[mu])
        nu_label = latex(coords[nu])
        lhs_str = latex(eq.lhs)
        rhs_str = latex(eq.rhs)
        st.latex(
            rf"({i})\;[\mu={mu_label},\,\nu={nu_label}]\quad {lhs_str} = {rhs_str}"
        )


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
