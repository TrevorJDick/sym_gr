"""
ui/efe_config.py
----------------
EFE (Einstein Field Equation) section widgets.

Renders the full EFE banner, input controls for Λ and κ, and a live LaTeX
summary of the configured equation.  T_μν is configured separately via
render_T_controls() which lives below the metric section (it needs coords).

No heavy computation here — SymPy is only touched in build_rhs_tensor()
which is called at field-equation generation time.
"""

from __future__ import annotations

import streamlit as st


# ---------------------------------------------------------------------------
# Section 1a: EFE banner
# ---------------------------------------------------------------------------

def render_efe_banner() -> None:
    """Render the full EFE as a large LaTeX banner."""
    st.latex(
        r"G_{\mu\nu} + \Lambda\, g_{\mu\nu} = \kappa\, T_{\mu\nu}"
    )


# ---------------------------------------------------------------------------
# Section 1b: EFE controls  (Λ and κ only — T configured in Section 3)
# ---------------------------------------------------------------------------

def render_efe_controls() -> tuple[str, str, str]:
    """
    Render EFE term controls for Λ, κ, and a T_μν status display.

    T_μν is edited in Section 3 (needs coord context); this column just
    shows the current value from session state.

    Returns
    -------
    (lambda_str, kappa_str, T_str)
    """
    col_G, col_lam, col_g, col_kap, col_T = st.columns([1, 1, 1, 1, 1.4])

    with col_G:
        st.markdown("**G_μν**")
        st.caption("Einstein tensor — computed from metric")

    with col_lam:
        lambda_str = st.text_input(
            "Λ  (cosmological constant)",
            value=st.session_state.get("lambda_str", "0"),
            key="_lambda_input",
            placeholder="e.g. 0 or Lambda",
            help="Scalar. Use 0 for vacuum without cosmological constant.",
        )
        st.session_state["lambda_str"] = lambda_str

    with col_g:
        st.markdown("**g_μν**")
        st.caption("metric — from ansatz below")

    with col_kap:
        kappa_str = st.text_input(
            "κ  (coupling constant)",
            value=st.session_state.get("kappa_str", "8*pi*G"),
            key="_kappa_input",
            placeholder="e.g. 8*pi*G",
            help="Scalar. Typically 8πG/c⁴ (geometric units: 8πG). Use the κ calculator below to compute from G and c.",
        )
        st.session_state["kappa_str"] = kappa_str

    with col_T:
        st.markdown("**T_μν**")
        st.caption("stress-energy — configured below")

    T_str = st.session_state.get("T_str", "0")
    return lambda_str, kappa_str, T_str


# ---------------------------------------------------------------------------
# Section 1c: κ calculator — physical constants helper
# ---------------------------------------------------------------------------

_UNIT_SYSTEMS = {
    "Geometric  (G = c = 1)": ("1", "1"),
    "Natural  (c = 1, G = 1)": ("1", "1"),
    "SI  (MKS)": ("6.674e-11", "299792458"),
    "CGS": ("6.674e-8", "29979245800"),
}


def render_constants_helper() -> None:
    """
    Optional expander: compute κ = 8πG/c⁴ from unit-system presets.

    When the user clicks Apply, the κ text input is updated.
    """
    with st.expander("κ calculator — set G and c (optional)", expanded=False):
        st.caption(
            "Choose a unit system to pre-fill G and c, then click **Apply** "
            "to push the computed κ = 8πG/c⁴ into the κ field above. "
            "You can still edit κ directly at any time."
        )

        unit_sys = st.selectbox(
            "Unit system",
            options=["Custom (enter below)"] + list(_UNIT_SYSTEMS.keys()),
            key="_gc_unit_sys",
        )

        if unit_sys in _UNIT_SYSTEMS:
            g_default, c_default = _UNIT_SYSTEMS[unit_sys]
        else:
            g_default = st.session_state.get("_G_val_input", "G")
            c_default = st.session_state.get("_c_val_input", "c")

        gc_cols = st.columns(2)
        with gc_cols[0]:
            G_val = st.text_input(
                "G (gravitational constant)",
                value=g_default,
                key="_G_val_input",
                placeholder="e.g. 6.674e-11 or G",
            )
        with gc_cols[1]:
            c_val = st.text_input(
                "c (speed of light)",
                value=c_default,
                key="_c_val_input",
                placeholder="e.g. 299792458 or c",
            )

        # Compute κ = 8πG/c⁴
        try:
            from sympy import pi, sympify, latex as sp_latex
            G_sym = sympify(G_val or "G")
            c_sym = sympify(c_val or "c")
            kap_computed = 8 * pi * G_sym / c_sym**4
            kap_str = str(kap_computed)
            st.markdown(
                r"Computed: $\kappa = \frac{8\pi G}{c^4} = $ "
                + f"$\\displaystyle {sp_latex(kap_computed)}$"
            )
            if st.button("Apply to κ", key="_apply_kap_btn"):
                st.session_state["_kappa_input"] = kap_str
                st.session_state["kappa_str"] = kap_str
                st.rerun()
        except Exception as exc:
            st.error(f"Could not compute κ: {exc}")


# ---------------------------------------------------------------------------
# Section 1d: live equation summary (pure string logic, no SymPy)
# ---------------------------------------------------------------------------

def _expr_to_latex(expr_str: str, fallback: str) -> str:
    """
    Try to convert a user-entered expression string to LaTeX for display.

    Returns *fallback* if parsing fails.
    """
    import re
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import latex as sp_latex, pi, symbols as sp_symbols

    s = expr_str.strip()
    if not s:
        return fallback
    # Auto-create any bare names as symbols so parse_expr doesn't choke
    tokens = set(re.findall(r'\b([A-Za-z][A-Za-z0-9_]*)\b', s))
    local: dict = {"pi": pi}
    builtins = {"pi", "E", "I", "oo", "sin", "cos", "sqrt", "exp", "log"}
    for tok in tokens:
        if tok not in builtins:
            local[tok] = sp_symbols(tok)
    try:
        return sp_latex(parse_expr(s, local_dict=local, evaluate=True))
    except Exception:
        return fallback


def render_efe_result(lambda_str: str, kappa_str: str, T_str: str) -> None:
    """
    Show a simplified LaTeX equation based on what terms are non-zero.

    Renders the actual entered values of Λ and κ rather than generic symbols.
    """
    lam = lambda_str.strip()
    T   = T_str.strip()
    kap = kappa_str.strip()

    lam_zero = (lam == "0" or lam == "")
    T_zero   = (T   == "0" or T   == "")
    any_empty = (lam == "" or kap == "" or T == "")

    if any_empty:
        st.markdown(
            '<span style="opacity:0.45;">'
            r'$G_{\mu\nu} + \Lambda\, g_{\mu\nu} = \kappa\, T_{\mu\nu}$'
            '</span>  &nbsp; *(fill in all terms above)*',
            unsafe_allow_html=True,
        )
        return

    # Render actual values as LaTeX where possible
    lam_tex = _expr_to_latex(lam, r"\Lambda")
    kap_tex = _expr_to_latex(kap, r"\kappa")

    if lam_zero and T_zero:
        st.latex(r"G_{\mu\nu} = 0")
    elif not lam_zero and T_zero:
        # RHS is -Λ g_μν; compute -Λ so the displayed sign is explicit
        try:
            import re
            from sympy.parsing.sympy_parser import parse_expr
            from sympy import latex as sp_latex, pi, symbols as sp_symbols
            tokens = set(re.findall(r'\b([A-Za-z][A-Za-z0-9_]*)\b', lam))
            local: dict = {"pi": pi}
            for tok in tokens:
                if tok not in {"pi", "E", "I", "oo", "sin", "cos", "sqrt", "exp", "log"}:
                    local[tok] = sp_symbols(tok)
            neg_lam_tex = sp_latex(-parse_expr(lam, local_dict=local, evaluate=True))
        except Exception:
            neg_lam_tex = r"-\left(" + lam_tex + r"\right)"
        st.latex(rf"G_{{\mu\nu}} = {neg_lam_tex}\, g_{{\mu\nu}}")
    elif lam_zero and not T_zero:
        st.latex(rf"G_{{\mu\nu}} = {kap_tex}\, T_{{\mu\nu}}")
    else:
        st.latex(rf"G_{{\mu\nu}} + \left({lam_tex}\right) g_{{\mu\nu}} = {kap_tex}\, T_{{\mu\nu}}")


# ---------------------------------------------------------------------------
# build_rhs_tensor — called at compute time
# ---------------------------------------------------------------------------

def build_rhs_tensor(
    lambda_str: str,
    kappa_str: str,
    T_str: str,
    metric_matrix,   # sympy.Matrix
    coord_syms: list,
):
    """
    Build the per-component RHS tensor: κ·T_μν − Λ·g_μν.

    Parameters
    ----------
    lambda_str, kappa_str, T_str : str
        User-entered strings for Λ, κ, T_μν.
    metric_matrix : sympy.Matrix
        The parsed metric (n×n).
    coord_syms : list of sympy.Symbol
        Coordinate symbols for parsing.

    Returns
    -------
    sympy.tensor.array.ImmutableDenseNDimArray  shape (n, n)
    or None if parsing fails (caller should handle / fall back to scalar 0).

    Raises
    ------
    ValueError on parse errors.
    """
    from sympy import Integer, zeros as sp_zeros
    from sympy.tensor.array import ImmutableDenseNDimArray
    from ui.parse import _build_local_dict
    from sympy.parsing.sympy_parser import parse_expr
    import re

    n = metric_matrix.shape[0]
    local = _build_local_dict(coord_syms)

    from sympy import symbols as sp_symbols
    if "G" not in local:
        local["G"] = sp_symbols("G")
    if "Lambda" not in local:
        local["Lambda"] = sp_symbols("Lambda")
    if "c" not in local:
        local["c"] = sp_symbols("c")

    def _parse_scalar(s: str, name: str):
        s = s.strip()
        if s == "0" or s == "":
            return Integer(0)
        try:
            return parse_expr(s, local_dict=local, evaluate=True)
        except Exception as exc:
            raise ValueError(f"Could not parse {name}={s!r}: {exc}") from exc

    def _parse_tensor(s: str, name: str):
        s = s.strip()
        if s == "0" or s == "":
            from sympy import zeros as sp_zeros2
            return sp_zeros2(n, n)
        func_names = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', s))
        from sympy import Function
        for fn in func_names:
            if fn not in local:
                local[fn] = Function(fn)
        try:
            result = parse_expr(s, local_dict=local, evaluate=True)
        except Exception as exc:
            raise ValueError(f"Could not parse {name}={s!r}: {exc}") from exc
        from sympy import Matrix
        if isinstance(result, Matrix):
            if result.shape != (n, n):
                raise ValueError(
                    f"{name} must be {n}×{n} (got {result.shape[0]}×{result.shape[1]})"
                )
            return result
        try:
            scalar_val = result
            if scalar_val == Integer(0):
                from sympy import zeros as sp_zeros2
                return sp_zeros2(n, n)
        except Exception:
            pass
        raise ValueError(
            f"{name} must be a Matrix expression or 0, got: {s!r}"
        )

    lam = _parse_scalar(lambda_str, "Λ")
    kap = _parse_scalar(kappa_str, "κ")
    T_mat = _parse_tensor(T_str, "T_μν")

    from sympy import Matrix
    rhs_mat = kap * T_mat - lam * Matrix(metric_matrix)

    return ImmutableDenseNDimArray(rhs_mat.tolist())
