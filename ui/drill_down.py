"""
ui/drill_down.py
----------------
Step-by-step tensor derivation display for the Streamlit UI.

Pattern: compact overview of all components, then a selectbox to pick one
for full step-by-step detail.  No nested expanders (Streamlit forbids them).
"""

from __future__ import annotations

import streamlit as st
from sympy import Integer, latex

from core.derivation import ChristoffelStep, RhoTerm, RiemannStep


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tex(sym) -> str:
    return latex(sym)


def _coord_tex(coords: list, i: int) -> str:
    """Return the LaTeX representation of coordinate i.

    Multi-character LaTeX commands (e.g. ``\\theta``, ``\\phi``) are wrapped
    in braces so that concatenating several coordinates in a subscript group
    does not merge them into an invalid command (e.g. ``\\thetatr``).
    """
    tex = latex(coords[i])
    return f"{{{tex}}}" if "\\" in tex else tex


def _chri_lhs(coords: list, sigma: int, mu: int, nu: int) -> str:
    """
    LaTeX LHS for a Christoffel component in step-by-step overviews.

    Off-diagonal (μ ≠ ν): ``Γ^σ_μν = Γ^σ_νμ`` to show lower-index symmetry.
    """
    sig = _coord_tex(coords, sigma)
    m   = _coord_tex(coords, mu)
    nv  = _coord_tex(coords, nu)
    base = rf"\Gamma^{{{sig}}}_{{{m}{nv}}}"
    if mu == nu:
        return base
    sym = rf"\Gamma^{{{sig}}}_{{{nv}{m}}}"
    return rf"{base} = {sym}"


def _riem_lhs(coords: list, rho: int, sigma: int, mu: int, nu: int) -> str:
    """
    LaTeX LHS for a Riemann component in step-by-step overviews.

    Off-diagonal (μ ≠ ν): ``R^ρ_σμν = -R^ρ_σνμ`` to show antisymmetry.
    """
    r  = _coord_tex(coords, rho)
    s  = _coord_tex(coords, sigma)
    m  = _coord_tex(coords, mu)
    nv = _coord_tex(coords, nu)
    base = rf"R^{{{r}}}_{{{s}{m}{nv}}}"
    if mu == nu:
        return base
    anti = rf"R^{{{r}}}_{{{s}{nv}{m}}}"
    return rf"{base} = -{anti}"


def _chri_label(coords, sigma, mu, nu, value) -> str:
    """Plain-text label for a Christoffel component (selectbox)."""
    return (
        f"Γ^{coords[sigma]}_{{{coords[mu]}{coords[nu]}}}  =  "
        + ("0" if value == Integer(0) else str(value))
    )


def _riem_label(coords, rho, sigma, mu, nu, value) -> str:
    """Plain-text label for a Riemann component (selectbox)."""
    return (
        f"R^{coords[rho]}_{{{coords[sigma]}{coords[mu]}{coords[nu]}}}  =  "
        + ("0" if value == Integer(0) else str(value))
    )


# ---------------------------------------------------------------------------
# Christoffel drill-down
# ---------------------------------------------------------------------------

def _render_christoffel_detail(
    step: ChristoffelStep,
    coords: list,
    show_zero_rho_terms: bool,
) -> None:
    """Render full step-by-step derivation for one Christoffel component."""
    sigma, mu, nu = step.sigma, step.mu, step.nu
    sig_tex = _coord_tex(coords, sigma)
    mu_tex  = _coord_tex(coords, mu)
    nu_tex  = _coord_tex(coords, nu)
    lhs     = rf"\Gamma^{{{sig_tex}}}_{{{mu_tex}{nu_tex}}}"
    val_tex = _tex(step.value)

    # Formula
    st.latex(
        rf"{lhs} = \frac{{1}}{{2}}\, g^{{{sig_tex}\rho}}"
        rf"\Bigl(\partial_{{{mu_tex}}} g_{{{nu_tex}\rho}}"
        rf" + \partial_{{{nu_tex}}} g_{{{mu_tex}\rho}}"
        rf" - \partial_{{\rho}}\, g_{{{mu_tex}{nu_tex}}}\Bigr)"
    )

    st.markdown("**Summation over ρ:**")

    zero_count = 0
    for term in step.rho_terms:
        rho_tex = _coord_tex(coords, term.rho)
        if term.is_zero:
            zero_count += 1
            if not show_zero_rho_terms:
                continue
            # Vanishing term — show reason
            if term.g_inv_zero:
                reason = rf"g^{{{sig_tex}{rho_tex}}} = 0"
            else:
                parts = []
                if term.d1 == Integer(0):
                    parts.append(rf"\partial_{{{mu_tex}}} g_{{{nu_tex}{rho_tex}}} = 0")
                if term.d2 == Integer(0):
                    parts.append(rf"\partial_{{{nu_tex}}} g_{{{mu_tex}{rho_tex}}} = 0")
                if term.d3 == Integer(0):
                    parts.append(rf"\partial_{{{rho_tex}}} g_{{{mu_tex}{nu_tex}}} = 0")
                reason = r",\quad ".join(parts) if parts else r"\text{bracket} = 0"
            st.latex(
                rf"\rho = {rho_tex}:\quad"
                rf"\ g^{{{sig_tex}{rho_tex}}} = {_tex(term.g_inv)}"
                rf"\quad\Rightarrow\quad \text{{contribution}} = 0"
                rf"\quad\bigl({reason}\bigr)"
            )
        else:
            # Full nonzero term
            st.latex(
                rf"\rho = {rho_tex}:\quad"
                rf"\ g^{{{sig_tex}{rho_tex}}} = {_tex(term.g_inv)}"
            )
            st.latex(
                rf"\quad\partial_{{{mu_tex}}} g_{{{nu_tex}{rho_tex}}} = {_tex(term.d1)}"
                rf",\quad"
                rf"\partial_{{{nu_tex}}} g_{{{mu_tex}{rho_tex}}} = {_tex(term.d2)}"
                rf",\quad"
                rf"\partial_{{{rho_tex}}} g_{{{mu_tex}{nu_tex}}} = {_tex(term.d3)}"
            )
            st.latex(
                rf"\quad\Rightarrow\quad"
                rf"\tfrac{{1}}{{2}} \cdot {_tex(term.g_inv)}"
                rf"\cdot\bigl({_tex(term.d1)} + {_tex(term.d2)} - {_tex(term.d3)}\bigr)"
                rf" = {_tex(term.contribution)}"
            )

    if zero_count > 0 and not show_zero_rho_terms:
        st.caption(
            f"{zero_count} vanishing ρ-term(s) hidden — "
            "enable *Show vanishing ρ-terms* above to see them with reasons."
        )

    conclusion_lhs = _chri_lhs(coords, sigma, mu, nu)
    st.divider()
    if step.is_zero:
        st.latex(rf"\therefore\quad {conclusion_lhs} = 0")
        st.caption("All ρ contributions vanish → component is zero.")
    else:
        st.latex(rf"\therefore\quad {conclusion_lhs} = {val_tex}")


def display_christoffel_steps(
    steps: dict,
    coords: list,
    show_zeros: bool = False,
    show_zero_rho_terms: bool = False,
) -> None:
    """
    Render Christoffel symbols with step-by-step derivation.

    Shows a compact overview of all relevant components, then a selectbox
    to pick one for full derivation detail.  Avoids nested expanders.
    """
    n = len(coords)

    # Collect components to show
    items: list[tuple[int, int, int, ChristoffelStep]] = []
    for sigma in range(n):
        for mu in range(n):
            for nu in range(mu, n):
                step = steps[(sigma, mu, nu)]
                if step.is_zero and not show_zeros:
                    continue
                items.append((sigma, mu, nu, step))

    if not items:
        st.success("All Christoffel symbols are zero — spacetime is flat in these coordinates.")
        st.info(
            "To inspect the vanishing derivations, enable both "
            "**Step-by-step** and **Show zero components** above."
        )
        return

    # ── Compact overview
    st.markdown("**Overview:**")
    nonzero_lines = [
        rf"{_chri_lhs(coords, s, m, v)} = {_tex(step.value)}"
        for s, m, v, step in items if not step.is_zero
    ]
    zero_lines = [
        rf"{_chri_lhs(coords, s, m, v)} = 0"
        for s, m, v, step in items if step.is_zero
    ]
    if nonzero_lines:
        st.latex(r" \\ ".join(nonzero_lines))
    if zero_lines:
        st.markdown(
            '<span style="opacity:0.45;">'
            + " &nbsp;&nbsp; ".join(f"${l}$" for l in zero_lines)
            + "</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Component picker
    labels = [_chri_label(coords, s, m, v, step.value) for s, m, v, step in items]
    selected = st.selectbox(
        "Inspect component:",
        options=range(len(items)),
        format_func=lambda i: labels[i],
        key="_chri_detail_select",
    )

    if selected is not None:
        sigma, mu, nu, step = items[selected]
        _render_christoffel_detail(step, coords, show_zero_rho_terms)


# ---------------------------------------------------------------------------
# Riemann drill-down
# ---------------------------------------------------------------------------

def _render_riemann_detail(
    step: RiemannStep,
    coords: list,
) -> None:
    """Render full step-by-step derivation for one Riemann component."""
    rho, sigma, mu, nu = step.rho, step.sigma, step.mu, step.nu
    rho_tex = _coord_tex(coords, rho)
    sig_tex = _coord_tex(coords, sigma)
    mu_tex  = _coord_tex(coords, mu)
    nu_tex  = _coord_tex(coords, nu)
    lhs = rf"R^{{{rho_tex}}}_{{{sig_tex}{mu_tex}{nu_tex}}}"

    st.latex(
        rf"{lhs} = "
        rf"\partial_{{{mu_tex}}}\Gamma^{{{rho_tex}}}_{{{nu_tex}{sig_tex}}}"
        rf" - \partial_{{{nu_tex}}}\Gamma^{{{rho_tex}}}_{{{mu_tex}{sig_tex}}}"
        rf" + \Gamma^{{{rho_tex}}}_{{{mu_tex}\lambda}}\Gamma^\lambda_{{{nu_tex}{sig_tex}}}"
        rf" - \Gamma^{{{rho_tex}}}_{{{nu_tex}\lambda}}\Gamma^\lambda_{{{mu_tex}{sig_tex}}}"
    )

    for label_tex, val in [
        (
            rf"\partial_{{{mu_tex}}}\Gamma^{{{rho_tex}}}_{{{nu_tex}{sig_tex}}}",
            step.term1,
        ),
        (
            rf"-\,\partial_{{{nu_tex}}}\Gamma^{{{rho_tex}}}_{{{mu_tex}{sig_tex}}}",
            -step.term2,
        ),
        (
            rf"\Gamma^{{{rho_tex}}}_{{{mu_tex}\lambda}}\Gamma^\lambda_{{{nu_tex}{sig_tex}}}",
            step.term3,
        ),
        (
            rf"-\,\Gamma^{{{rho_tex}}}_{{{nu_tex}\lambda}}\Gamma^\lambda_{{{mu_tex}{sig_tex}}}",
            -step.term4,
        ),
    ]:
        st.latex(rf"{label_tex} = {_tex(val)}")

    conclusion_lhs = _riem_lhs(coords, rho, sigma, mu, nu)
    st.divider()
    st.latex(rf"\therefore\quad {conclusion_lhs} = {_tex(step.value)}")


def display_riemann_steps(
    steps: dict,
    coords: list,
    show_zeros: bool = False,
) -> None:
    """
    Render Riemann tensor components with the four named terms.

    Only shows μ < ν (antisymmetry in last two indices).
    Uses selectbox + detail panel — no nested expanders.
    """
    n = len(coords)

    items: list[tuple[int, int, int, int, RiemannStep]] = []
    for rho in range(n):
        for sigma in range(n):
            for mu in range(n):
                for nu in range(mu + 1, n):
                    step = steps[(rho, sigma, mu, nu)]
                    if step.is_zero and not show_zeros:
                        continue
                    items.append((rho, sigma, mu, nu, step))

    if not items:
        st.success("All Riemann components are zero — spacetime is flat.")
        st.info(
            "Enable **Show zero components** above to inspect each term."
        )
        return

    # ── Compact overview
    st.markdown("**Overview:**")
    nonzero_lines = [
        rf"{_riem_lhs(coords, r, s, m, v)} = {_tex(step.value)}"
        for r, s, m, v, step in items if not step.is_zero
    ]
    zero_lines = [
        rf"{_riem_lhs(coords, r, s, m, v)} = 0"
        for r, s, m, v, step in items if step.is_zero
    ]
    if nonzero_lines:
        st.latex(r" \\ ".join(nonzero_lines))
    if zero_lines:
        st.markdown(
            '<span style="opacity:0.45;">'
            + " &nbsp;&nbsp; ".join(f"${l}$" for l in zero_lines)
            + "</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Component picker
    labels = [
        _riem_label(coords, r, s, m, v, step.value)
        for r, s, m, v, step in items
    ]
    selected = st.selectbox(
        "Inspect component:",
        options=range(len(items)),
        format_func=lambda i: labels[i],
        key="_riem_detail_select",
    )

    if selected is not None:
        rho, sigma, mu, nu, step = items[selected]
        _render_riemann_detail(step, coords)
