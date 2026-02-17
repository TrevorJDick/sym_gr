"""
ui/metric_grid.py
-----------------
Interactive n×n metric grid input.

Renders a symmetric n×n grid of text_input cells.  The upper triangle
(including diagonal) is editable; the lower triangle mirrors it.  Each cell
displays an inline parse error if its expression is invalid.

Returns a SymPy Matrix on success, or None if any cell fails to parse.
"""

from __future__ import annotations

import streamlit as st
from sympy import Matrix, Integer, latex, zeros as sp_zeros


def render_metric_grid(
    n: int,
    coord_syms: list,
    key_prefix: str = "mg",
) -> Matrix | None:
    """
    Render an n×n symmetric metric grid and return the parsed Matrix.

    Upper-triangle cells (i ≤ j) are editable text inputs.
    Lower-triangle cells mirror the upper-triangle entry (read-only display).

    Parameters
    ----------
    n : int
        Dimension (typically 4).
    coord_syms : list of sympy.Symbol
        Coordinate symbols for parsing.
    key_prefix : str
        Prefix for Streamlit widget keys (avoids key collisions).

    Returns
    -------
    sympy.Matrix or None
        Parsed metric matrix, or None if any cell has a parse error.
    """
    from ui.parse import _build_local_dict
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import Function
    import re

    st.caption(
        "Upper triangle and diagonal are editable. "
        "Lower triangle mirrors automatically (symmetric metric)."
    )

    # State key for grid values
    grid_key = f"{key_prefix}_grid"
    if grid_key not in st.session_state:
        # Default: identity-ish (zeros off-diagonal, 1 on diagonal)
        st.session_state[grid_key] = {
            (i, j): ("1" if i == j else "0")
            for i in range(n)
            for j in range(i, n)
        }

    local = _build_local_dict(coord_syms)

    # Column headers
    header_cols = st.columns([0.4] + [1] * n)
    with header_cols[0]:
        st.markdown("&nbsp;", unsafe_allow_html=True)
    for j in range(n):
        with header_cols[j + 1]:
            st.markdown(f"**{coords_label(coord_syms, j)}**")

    parsed: dict[tuple[int, int], object] = {}
    errors: dict[tuple[int, int], str] = {}

    for i in range(n):
        row_cols = st.columns([0.4] + [1] * n)
        with row_cols[0]:
            st.markdown(f"**{coords_label(coord_syms, i)}**")

        for j in range(n):
            with row_cols[j + 1]:
                if j < i:
                    # Lower triangle — mirror of (i, j) → (j, i) cell
                    mirror_key = (j, i)
                    val_str = st.session_state[grid_key].get(mirror_key, "0")
                    # Read-only display using st.text_input disabled
                    st.text_input(
                        label=f"g_{i}{j}",
                        value=val_str,
                        key=f"{key_prefix}_{i}_{j}_mirror",
                        disabled=True,
                        label_visibility="collapsed",
                    )
                    # Use the same parsed value as upper cell
                    cell_key = (j, i)
                else:
                    # Editable upper-triangle / diagonal cell
                    cell_key = (i, j)
                    default_val = st.session_state[grid_key].get(cell_key, "0")
                    entered = st.text_input(
                        label=f"g_{i}{j}",
                        value=default_val,
                        key=f"{key_prefix}_{i}_{j}",
                        label_visibility="collapsed",
                        placeholder="0",
                    )
                    st.session_state[grid_key][cell_key] = entered

                # Parse the cell (use upper-triangle key for both)
                if cell_key not in parsed and cell_key not in errors:
                    raw = st.session_state[grid_key].get(cell_key, "0").strip() or "0"
                    # Inject function names
                    for fn in set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', raw)):
                        if fn not in local:
                            local[fn] = Function(fn)
                    try:
                        parsed[cell_key] = parse_expr(raw, local_dict=local, evaluate=True)
                    except Exception as exc:
                        errors[cell_key] = str(exc)
                        parsed[cell_key] = None

                if cell_key in errors and j >= i:
                    st.error(f"↑ {errors[cell_key]}", icon="🚨")

    if errors:
        return None

    # Build symmetric Matrix
    mat = [[Integer(0)] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            key = (min(i, j), max(i, j))
            val = parsed.get(key)
            if val is None:
                return None
            mat[i][j] = val

    return Matrix(mat)


def coords_label(coord_syms: list, i: int) -> str:
    from sympy import latex
    return f"${latex(coord_syms[i])}$"
