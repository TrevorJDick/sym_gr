"""
ui/metric_grid.py
-----------------
Interactive n×n tensor grid input (metric or stress-energy).

For symmetric tensors (e.g. g_μν, T_μν): upper triangle including diagonal
is editable; lower triangle mirrors automatically.

For general tensors: all cells are editable independently.

Returns a SymPy Matrix on success, or None if any cell fails to parse.
"""

from __future__ import annotations

import streamlit as st
from sympy import Matrix, Integer, latex, zeros as sp_zeros


def _on_grid_cell_change(changed_flag: str) -> None:
    """Mark the grid as the source of the most recent tensor change."""
    st.session_state[changed_flag] = True


def render_metric_grid(
    n: int,
    coord_syms: list,
    key_prefix: str = "mg",
    symmetric: bool = True,
    changed_flag: str = "_metric_from_grid",
    default_diag: str = "1",
) -> Matrix | None:
    """
    Render an n×n tensor grid and return the parsed Matrix.

    Parameters
    ----------
    n : int
        Dimension (typically 4).
    coord_syms : list of sympy.Symbol
        Coordinate symbols for parsing.
    key_prefix : str
        Prefix for Streamlit widget keys (avoids key collisions).
    symmetric : bool
        If True (default): upper-triangle cells editable, lower mirrors.
        If False: all cells independently editable.
    changed_flag : str
        Session state key to set True when any cell changes.
    default_diag : str
        Default string value for diagonal cells when the grid is first
        created. Use "1" for the metric (Minkowski default) and "0" for
        the stress-energy tensor (vacuum default).

    Returns
    -------
    sympy.Matrix or None
        Parsed matrix, or None if any cell has a parse error.
    """
    from ui.parse import _build_local_dict
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import Function
    import re

    if symmetric:
        st.caption(
            "Upper triangle and diagonal are editable. "
            "Lower triangle mirrors automatically (symmetric tensor)."
        )
    else:
        st.caption("All cells are independently editable.")

    # State key for grid values
    grid_key = f"{key_prefix}_grid"
    if grid_key not in st.session_state:
        if symmetric:
            st.session_state[grid_key] = {
                (i, j): (default_diag if i == j else "0")
                for i in range(n)
                for j in range(i, n)
            }
        else:
            st.session_state[grid_key] = {
                (i, j): "0"
                for i in range(n)
                for j in range(n)
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
                if symmetric and j < i:
                    # Lower triangle — mirror of upper cell (i, j) → (j, i)
                    mirror_key = (j, i)
                    val_str = st.session_state[grid_key].get(mirror_key, "0")
                    st.text_input(
                        label=f"_{key_prefix}_{i}{j}",
                        value=val_str,
                        key=f"{key_prefix}_{i}_{j}_mirror",
                        disabled=True,
                        label_visibility="collapsed",
                    )
                    cell_key = (j, i)
                else:
                    # Editable cell
                    cell_key = (i, j)
                    default_val = st.session_state[grid_key].get(cell_key, "0")
                    entered = st.text_input(
                        label=f"_{key_prefix}_{i}{j}",
                        value=default_val,
                        key=f"{key_prefix}_{i}_{j}",
                        label_visibility="collapsed",
                        placeholder="0",
                        on_change=_on_grid_cell_change,
                        args=(changed_flag,),
                    )
                    st.session_state[grid_key][cell_key] = entered

                # Parse the cell
                if cell_key not in parsed and cell_key not in errors:
                    raw = st.session_state[grid_key].get(cell_key, "0").strip() or "0"
                    for fn in set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', raw)):
                        if fn not in local:
                            local[fn] = Function(fn)
                    try:
                        parsed[cell_key] = parse_expr(raw, local_dict=local, evaluate=True)
                    except Exception as exc:
                        errors[cell_key] = str(exc)
                        parsed[cell_key] = None

                # Show errors only on editable cells
                show_error = (j >= i) if symmetric else True
                if cell_key in errors and show_error:
                    st.error(f"↑ {errors[cell_key]}", icon="🚨")

    if errors:
        return None

    # Build Matrix
    if symmetric:
        mat = [[Integer(0)] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                key = (min(i, j), max(i, j))
                val = parsed.get(key)
                if val is None:
                    return None
                mat[i][j] = val
    else:
        mat = [[Integer(0)] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                val = parsed.get((i, j))
                if val is None:
                    return None
                mat[i][j] = val

    result = Matrix(mat)

    # Matrix preview
    st.divider()
    from sympy import latex as sp_latex
    st.latex(sp_latex(result))

    return result


def _matrix_to_str(mat: "Matrix", n: int) -> str:
    """Convert a SymPy Matrix to a diag(...) or Matrix([[...]]) string."""
    # Check if diagonal
    is_diag = all(
        mat[i, j] == Integer(0)
        for i in range(n) for j in range(n) if i != j
    )
    if is_diag:
        diag_entries = ", ".join(str(mat[i, i]) for i in range(n))
        return f"diag({diag_entries})"
    rows = []
    for i in range(n):
        row = "[" + ", ".join(str(mat[i, j]) for j in range(n)) + "]"
        rows.append(row)
    return "Matrix([" + ", ".join(rows) + "])"


def coords_label(coord_syms: list, i: int) -> str:
    from sympy import latex
    return f"${latex(coord_syms[i])}$"
