"""
ui/efe_config.py
----------------
EFE (Einstein Field Equation) section widgets.

Renders the full EFE banner, input controls for Λ, κ, T_μν, and
a live LaTeX summary of the configured equation.

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
# Section 1b: EFE controls
# ---------------------------------------------------------------------------

def render_efe_controls() -> tuple[str, str, str]:
    """
    Render the 5-column EFE term controls.

    Columns correspond to: G_μν | Λ | g_μν | κ | T_μν

    Writes lambda_str, kappa_str, T_str to session_state and returns them.

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
            help="Scalar. Typically 8πG/c⁴ (natural units: 8πG).",
        )
        st.session_state["kappa_str"] = kappa_str

    with col_T:
        T_str = st.text_area(
            "T_μν  (stress-energy tensor, rank-2)",
            value=st.session_state.get("T_str", "0"),
            height=90,
            key="_T_input",
            placeholder="0  or  diag(rho, p, p, p)",
            help=(
                "Stress-energy tensor. Enter 0 for vacuum, or a matrix expression.\n"
                "E.g.  diag(rho, p, p, p)  or  Matrix([[rho,0,0,0],[0,p,0,0],...])"
            ),
        )
        st.session_state["T_str"] = T_str

    return lambda_str, kappa_str, T_str


# ---------------------------------------------------------------------------
# Section 1c: live equation summary (pure string logic, no SymPy)
# ---------------------------------------------------------------------------

def render_efe_result(lambda_str: str, kappa_str: str, T_str: str) -> None:
    """
    Show a simplified LaTeX equation based on what terms are non-zero.

    This is pure string/LaTeX logic — no SymPy calls.
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

    if lam_zero and T_zero:
        st.latex(r"G_{\mu\nu} = 0")
    elif not lam_zero and T_zero:
        st.latex(r"G_{\mu\nu} = -\Lambda\, g_{\mu\nu}")
    elif lam_zero and not T_zero:
        st.latex(r"G_{\mu\nu} = \kappa\, T_{\mu\nu}")
    else:
        st.latex(r"G_{\mu\nu} + \Lambda\, g_{\mu\nu} = \kappa\, T_{\mu\nu}")


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

    # Add G as a symbol (gravitational constant) if not already a coord
    from sympy import symbols as sp_symbols
    if "G" not in local:
        local["G"] = sp_symbols("G")
    if "Lambda" not in local:
        local["Lambda"] = sp_symbols("Lambda")
    if "c" not in local:
        local["c"] = sp_symbols("c")

    # Helper: parse a scalar string
    def _parse_scalar(s: str, name: str):
        s = s.strip()
        if s == "0" or s == "":
            return Integer(0)
        try:
            return parse_expr(s, local_dict=local, evaluate=True)
        except Exception as exc:
            raise ValueError(f"Could not parse {name}={s!r}: {exc}") from exc

    # Helper: parse a matrix string (or scalar 0)
    def _parse_tensor(s: str, name: str):
        s = s.strip()
        if s == "0" or s == "":
            from sympy import zeros as sp_zeros2
            return sp_zeros2(n, n)
        # inject function names
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
        # scalar — broadcast to diagonal? No, assume scalar means zero tensor
        # Actually if they entered a plain scalar for T, treat as 0-tensor
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

    # RHS = κ·T − Λ·g
    from sympy import Matrix
    rhs_mat = kap * T_mat - lam * Matrix(metric_matrix)

    return ImmutableDenseNDimArray(rhs_mat.tolist())
