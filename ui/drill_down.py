"""
ui/drill_down.py
----------------
Step-by-step tensor derivation display for the Streamlit UI.

Renders each tensor component as a collapsible expander showing every
intermediate partial derivative and summation term — including vanishing
terms with explicit reasons for their vanishing.
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
    return latex(coords[i])


# ---------------------------------------------------------------------------
# Christoffel drill-down
# ---------------------------------------------------------------------------

def display_christoffel_steps(
    steps: dict,
    coords: list,
    show_zeros: bool = False,
    show_zero_rho_terms: bool = False,
) -> None:
    """
    Render Christoffel symbols with full step-by-step derivation.

    Parameters
    ----------
    steps : dict[(σ,μ,ν) → ChristoffelStep]
        From core.derivation.christoffel_steps().
    coords : list of sympy.Symbol
    show_zeros : bool
        If True, also show components that evaluate to zero.
    show_zero_rho_terms : bool
        If True, show ρ-summation terms whose contribution is zero.
        Always shows them with the reason for vanishing.
    """
    n = len(coords)
    any_shown = False

    for sigma in range(n):
        for mu in range(n):
            for nu in range(mu, n):   # upper triangle only — symmetry μ↔ν
                step: ChristoffelStep = steps[(sigma, mu, nu)]

                if step.is_zero and not show_zeros:
                    continue

                any_shown = True
                sig_tex = _coord_tex(coords, sigma)
                mu_tex  = _coord_tex(coords, mu)
                nu_tex  = _coord_tex(coords, nu)
                lhs     = rf"\Gamma^{{{sig_tex}}}_{{{mu_tex} {nu_tex}}}"
                val_tex = _tex(step.value)

                # Expander label — plain text, no LaTeX
                label = (
                    f"Γ^{coords[sigma]}_{{{coords[mu]}{coords[nu]}}}  =  "
                    + ("0" if step.is_zero else str(step.value))
                )

                with st.expander(label, expanded=False):
                    # ── Header formula
                    st.latex(
                        rf"{lhs} = \frac{{1}}{{2}}\, g^{{{sig_tex}\rho}}"
                        rf"\Bigl(\partial_{{{mu_tex}}} g_{{{nu_tex}\rho}}"
                        rf" + \partial_{{{nu_tex}}} g_{{{mu_tex}\rho}}"
                        rf" - \partial_{{\rho}}\, g_{{{mu_tex}{nu_tex}}}\Bigr)"
                    )

                    # ── ρ-summation table
                    st.markdown("**Summation over ρ:**")

                    nonzero_shown = 0
                    zero_count = 0

                    for term in step.rho_terms:
                        rho_tex = _coord_tex(coords, term.rho)
                        is_zero = term.is_zero

                        if is_zero:
                            zero_count += 1
                            if not show_zero_rho_terms:
                                continue
                            # Show vanishing term with reason
                            if term.g_inv_zero:
                                reason = rf"g^{{{sig_tex}{rho_tex}}} = 0"
                            else:
                                parts = []
                                if term.d1 == Integer(0):
                                    parts.append(
                                        rf"\partial_{{{mu_tex}}} g_{{{nu_tex}{rho_tex}}} = 0"
                                    )
                                if term.d2 == Integer(0):
                                    parts.append(
                                        rf"\partial_{{{nu_tex}}} g_{{{mu_tex}{rho_tex}}} = 0"
                                    )
                                if term.d3 == Integer(0):
                                    parts.append(
                                        rf"\partial_{{{rho_tex}}} g_{{{mu_tex}{nu_tex}}} = 0"
                                    )
                                reason = r",\quad ".join(parts) if parts else r"\text{bracket} = 0"
                            st.latex(
                                rf"\rho = {rho_tex}:\quad"
                                rf"\ g^{{{sig_tex}{rho_tex}}} = {_tex(term.g_inv)}"
                                rf"\quad \Rightarrow \quad"
                                rf"\text{{contribution}} = 0 \quad"
                                rf"\bigl({reason}\bigr)"
                            )
                        else:
                            nonzero_shown += 1
                            # Show full nonzero calculation
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
                            "enable *Show vanishing ρ-terms* to see them with reasons."
                        )

                    # ── Final result
                    st.divider()
                    if step.is_zero:
                        st.latex(rf"\therefore\quad {lhs} = 0")
                        st.caption("All ρ contributions vanish → component is zero.")
                    else:
                        st.latex(rf"\therefore\quad {lhs} = {val_tex}")

    if not any_shown:
        if show_zeros:
            st.info("No components to display.")
        else:
            st.success(
                "All Christoffel symbols are zero — spacetime is flat in these coordinates."
            )
            st.info(
                "To inspect the vanishing derivations, enable both "
                "**Step-by-step** and **Show zero components** above."
            )


# ---------------------------------------------------------------------------
# Riemann drill-down
# ---------------------------------------------------------------------------

def display_riemann_steps(
    steps: dict,
    coords: list,
    show_zeros: bool = False,
) -> None:
    """
    Render Riemann tensor components with the four named terms.

    Only shows μ < ν (antisymmetry in last two indices).
    """
    n = len(coords)
    any_shown = False

    for rho in range(n):
        for sigma in range(n):
            for mu in range(n):
                for nu in range(mu + 1, n):
                    step: RiemannStep = steps[(rho, sigma, mu, nu)]
                    if step.is_zero and not show_zeros:
                        continue

                    any_shown = True
                    rho_tex = _coord_tex(coords, rho)
                    sig_tex = _coord_tex(coords, sigma)
                    mu_tex  = _coord_tex(coords, mu)
                    nu_tex  = _coord_tex(coords, nu)
                    lhs = rf"R^{{{rho_tex}}}_{{{sig_tex}{mu_tex}{nu_tex}}}"
                    label = (
                        f"R^{coords[rho]}_{{{coords[sigma]}{coords[mu]}{coords[nu]}}}  =  "
                        + ("0" if step.is_zero else str(step.value))
                    )

                    with st.expander(label, expanded=False):
                        st.latex(
                            rf"{lhs} = "
                            rf"\partial_{{{mu_tex}}}\Gamma^{{{rho_tex}}}_{{{nu_tex}{sig_tex}}}"
                            rf" - \partial_{{{nu_tex}}}\Gamma^{{{rho_tex}}}_{{{mu_tex}{sig_tex}}}"
                            rf" + \Gamma^{{{rho_tex}}}_{{{mu_tex}\lambda}}\Gamma^\lambda_{{{nu_tex}{sig_tex}}}"
                            rf" - \Gamma^{{{rho_tex}}}_{{{nu_tex}\lambda}}\Gamma^\lambda_{{{mu_tex}{sig_tex}}}"
                        )

                        for term_label, term_val, term_latex in [
                            (
                                rf"\partial_{{{mu_tex}}}\Gamma^{{{rho_tex}}}_{{{nu_tex}{sig_tex}}}",
                                step.term1,
                                _tex(step.term1),
                            ),
                            (
                                rf"-\partial_{{{nu_tex}}}\Gamma^{{{rho_tex}}}_{{{mu_tex}{sig_tex}}}",
                                -step.term2,
                                _tex(-step.term2),
                            ),
                            (
                                rf"\Gamma^{{{rho_tex}}}_{{{mu_tex}\lambda}}\Gamma^\lambda_{{{nu_tex}{sig_tex}}}",
                                step.term3,
                                _tex(step.term3),
                            ),
                            (
                                rf"-\Gamma^{{{rho_tex}}}_{{{nu_tex}\lambda}}\Gamma^\lambda_{{{mu_tex}{sig_tex}}}",
                                -step.term4,
                                _tex(-step.term4),
                            ),
                        ]:
                            st.latex(rf"{term_label} = {term_latex}")

                        st.divider()
                        st.latex(rf"\therefore\quad {lhs} = {_tex(step.value)}")

    if not any_shown:
        if show_zeros:
            st.info("No components to display.")
        else:
            st.success(
                "All Riemann components are zero — spacetime is flat. "
                "Enable *Show zero components* to inspect each term."
            )
