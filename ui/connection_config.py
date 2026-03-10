"""
ui/connection_config.py
-----------------------
Connection mode selector and tensor input grids.

Three modes:
  1. Levi-Civita   — no extra input; connection derived from metric.
  2. Torsion       — user enters T^σ_μν (antisymmetric in μ, ν).
                     Full connection = LC + contorsion(T).
  3. Full          — user enters all Γ^σ_μν directly; no symmetry assumed.

``render_connection_config`` returns ``(mode, tensor)`` where:
  - mode   : 'levi_civita' | 'torsion' | 'full'
  - tensor : ImmutableDenseNDimArray (T or Γ) | None (LC or parse error)

The app assembles the Connection object in the results section after the
metric has been parsed, so this module has no dependency on core/.
"""

from __future__ import annotations

import streamlit as st
from sympy import Integer, latex, zeros as sp_zeros
from sympy.tensor.array import ImmutableDenseNDimArray


# ---------------------------------------------------------------------------
# Mode selector
# ---------------------------------------------------------------------------

MODES = {
    "Levi-Civita (torsion-free, metric-compatible)": "levi_civita",
    "Metric + torsion tensor  T^σ_μν": "torsion",
    "Full connection  Γ^σ_μν  (specify all coefficients)": "full",
}

MODE_HELP = {
    "levi_civita": (
        "The standard GR connection: uniquely determined by the metric, "
        "symmetric in lower indices, zero torsion."
    ),
    "torsion": (
        "Enter the torsion tensor T^σ_μν (antisymmetric in μ, ν). "
        "The full connection Γ = Γ_LC + K is assembled automatically, "
        "where K is the contorsion built from your torsion input."
    ),
    "full": (
        "Specify all n³ connection coefficients Γ^σ_μν directly. "
        "No symmetry is assumed. Useful for exploring exotic connections, "
        "Weitzenböck geometry, or arbitrary affine structures. "
        "The metric is still used for index gymnastics in the results."
    ),
}


def render_connection_config(
    n: int,
    coord_syms: list,
) -> tuple[str, ImmutableDenseNDimArray | None]:
    """
    Render the connection mode selector and (for torsion / full mode)
    the tensor input grids.

    Parameters
    ----------
    n : int
        Spacetime dimension.
    coord_syms : list of sympy.Symbol
        Coordinate symbols (needed for labels and parsing).

    Returns
    -------
    (mode, tensor)
        mode   : 'levi_civita', 'torsion', or 'full'
        tensor : parsed ImmutableDenseNDimArray or None
                 None for 'levi_civita' or if there are parse errors.
    """
    mode_labels = list(MODES.keys())
    saved_label = st.session_state.get("_conn_mode_label", mode_labels[0])
    if saved_label not in mode_labels:
        saved_label = mode_labels[0]

    chosen_label = st.radio(
        "Connection type",
        options=mode_labels,
        index=mode_labels.index(saved_label),
        key="_conn_mode_radio",
        horizontal=False,
    )
    st.session_state["_conn_mode_label"] = chosen_label
    mode = MODES[chosen_label]

    st.caption(MODE_HELP[mode])

    if mode == "levi_civita":
        return "levi_civita", None

    if mode == "torsion":
        st.markdown(
            r"Enter the components of the torsion tensor $T^\sigma{}_{\mu\nu}$. "
            r"The tensor must be antisymmetric in $(\mu, \nu)$: "
            r"$T^\sigma{}_{\mu\nu} = -T^\sigma{}_{\nu\mu}$. "
            r"Diagonal entries are always zero."
        )
        tensor = _render_rank3_antisym_grid(n, coord_syms, key_prefix="tor")
        if tensor is not None:
            _preview_rank3(tensor, coord_syms, tensor_symbol="T", antisym=True)
        return "torsion", tensor

    # mode == "full"
    st.markdown(
        r"Enter all components of the connection $\Gamma^\sigma{}_{\mu\nu}$ "
        r"directly.  No symmetry in $(\mu, \nu)$ is assumed."
    )
    tensor = _render_rank3_full_grid(n, coord_syms, key_prefix="conn")
    if tensor is not None:
        _preview_rank3(tensor, coord_syms, tensor_symbol=r"\Gamma", antisym=False)
    return "full", tensor


# ---------------------------------------------------------------------------
# Rank-3 tensor input: antisymmetric in last two indices (torsion)
# ---------------------------------------------------------------------------

def _render_rank3_antisym_grid(
    n: int,
    coord_syms: list,
    key_prefix: str,
) -> ImmutableDenseNDimArray | None:
    """
    Render n sub-grids (one per upper index σ) for an antisymmetric tensor.

    For each σ slice:
      - Diagonal (μ = ν): disabled, always 0.
      - Upper triangle (μ < ν): editable text inputs.
      - Lower triangle (μ > ν): mirrors upper with a minus sign (disabled).

    Returns the parsed ImmutableDenseNDimArray or None on error.
    """
    from ui.parse import _build_local_dict
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import Function
    import re

    local = _build_local_dict(coord_syms)
    grid_key = f"{key_prefix}_asym_grid"

    # Initialise session state with zeros for upper-triangle pairs
    if grid_key not in st.session_state:
        st.session_state[grid_key] = {
            (s, mu, nu): "0"
            for s in range(n)
            for mu in range(n)
            for nu in range(mu + 1, n)
        }

    data = st.session_state[grid_key]
    parsed: dict = {}
    errors: dict = {}

    for sigma in range(n):
        coord_lbl = _sym_label(coord_syms, sigma)
        with st.expander(f"σ = {coord_lbl}", expanded=(sigma == 0)):
            # Column headers
            hcols = st.columns([0.4] + [1] * n)
            hcols[0].markdown("&nbsp;", unsafe_allow_html=True)
            for j in range(n):
                hcols[j + 1].markdown(f"**{_sym_label(coord_syms, j)}**")

            for mu in range(n):
                rcols = st.columns([0.4] + [1] * n)
                rcols[0].markdown(f"**{_sym_label(coord_syms, mu)}**")

                for nu in range(n):
                    with rcols[nu + 1]:
                        cell = (sigma, mu, nu)
                        upper = (sigma, min(mu, nu), max(mu, nu))

                        if mu == nu:
                            # Diagonal: always 0
                            st.text_input(
                                label=f"_d{key_prefix}_{sigma}{mu}{nu}",
                                value="0",
                                disabled=True,
                                label_visibility="collapsed",
                            )
                            parsed[cell] = Integer(0)

                        elif mu < nu:
                            # Editable upper-triangle entry
                            default = data.get(upper, "0")
                            entered = st.text_input(
                                label=f"_{key_prefix}_{sigma}{mu}{nu}",
                                value=default,
                                key=f"{key_prefix}_{sigma}_{mu}_{nu}",
                                label_visibility="collapsed",
                                placeholder="0",
                            )
                            data[upper] = entered
                            raw = (entered or "0").strip()
                            for fn in set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', raw)):
                                if fn not in local:
                                    local[fn] = Function(fn)
                            try:
                                parsed[upper] = parse_expr(raw, local_dict=local, evaluate=True)
                            except Exception as exc:
                                errors[upper] = str(exc)
                                parsed[upper] = None
                            if upper in errors:
                                st.error(f"↑ {errors[upper]}", icon="🚨")

                        else:
                            # Lower triangle: mirror of (σ, nu, mu) with minus sign
                            mirror_val = data.get((sigma, nu, mu), "0")
                            display_val = f"-({mirror_val})" if mirror_val not in ("0", "") else "0"
                            st.text_input(
                                label=f"_m{key_prefix}_{sigma}{mu}{nu}",
                                value=display_val,
                                disabled=True,
                                label_visibility="collapsed",
                            )
                            mirror_key = (sigma, nu, mu)
                            if mirror_key in parsed and parsed[mirror_key] is not None:
                                parsed[cell] = -parsed[mirror_key]
                            else:
                                parsed[cell] = Integer(0)

    if errors:
        return None

    # Build full (n, n, n) array
    arr = [
        [
            [
                _resolve_cell(parsed, sigma, mu, nu, n)
                for nu in range(n)
            ]
            for mu in range(n)
        ]
        for sigma in range(n)
    ]
    return ImmutableDenseNDimArray(arr)


def _resolve_cell(parsed: dict, sigma: int, mu: int, nu: int, n: int):
    """Return the parsed value for (σ, μ, ν), respecting antisymmetry."""
    if mu == nu:
        return Integer(0)
    key = (sigma, mu, nu)
    upper = (sigma, min(mu, nu), max(mu, nu))
    if key in parsed and parsed[key] is not None:
        return parsed[key]
    if upper in parsed and parsed[upper] is not None:
        return -parsed[upper] if mu > nu else parsed[upper]
    return Integer(0)


# ---------------------------------------------------------------------------
# Rank-3 tensor input: fully general (full connection)
# ---------------------------------------------------------------------------

def _render_rank3_full_grid(
    n: int,
    coord_syms: list,
    key_prefix: str,
) -> ImmutableDenseNDimArray | None:
    """
    Render n sub-grids (one per upper index σ) for a general rank-3 tensor.

    All n² entries per σ slice are independently editable.

    Returns the parsed ImmutableDenseNDimArray or None on error.
    """
    from ui.parse import _build_local_dict
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import Function
    import re

    local = _build_local_dict(coord_syms)
    grid_key = f"{key_prefix}_full_grid"

    if grid_key not in st.session_state:
        st.session_state[grid_key] = {
            (s, mu, nu): "0"
            for s in range(n)
            for mu in range(n)
            for nu in range(n)
        }

    data = st.session_state[grid_key]
    parsed: dict = {}
    errors: dict = {}

    for sigma in range(n):
        coord_lbl = _sym_label(coord_syms, sigma)
        with st.expander(f"σ = {coord_lbl}", expanded=(sigma == 0)):
            hcols = st.columns([0.4] + [1] * n)
            hcols[0].markdown("&nbsp;", unsafe_allow_html=True)
            for j in range(n):
                hcols[j + 1].markdown(f"**{_sym_label(coord_syms, j)}**")

            for mu in range(n):
                rcols = st.columns([0.4] + [1] * n)
                rcols[0].markdown(f"**{_sym_label(coord_syms, mu)}**")

                for nu in range(n):
                    with rcols[nu + 1]:
                        cell = (sigma, mu, nu)
                        default = data.get(cell, "0")
                        entered = st.text_input(
                            label=f"_{key_prefix}_{sigma}_{mu}_{nu}",
                            value=default,
                            key=f"{key_prefix}_{sigma}_{mu}_{nu}",
                            label_visibility="collapsed",
                            placeholder="0",
                        )
                        data[cell] = entered
                        raw = (entered or "0").strip()
                        for fn in set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', raw)):
                            if fn not in local:
                                local[fn] = Function(fn)
                        try:
                            parsed[cell] = parse_expr(raw, local_dict=local, evaluate=True)
                        except Exception as exc:
                            errors[cell] = str(exc)
                            parsed[cell] = None
                        if cell in errors:
                            st.error(f"↑ {errors[cell]}", icon="🚨")

    if errors:
        return None

    arr = [
        [
            [parsed.get((s, mu, nu), Integer(0)) or Integer(0) for nu in range(n)]
            for mu in range(n)
        ]
        for s in range(n)
    ]
    return ImmutableDenseNDimArray(arr)


# ---------------------------------------------------------------------------
# Symbolic preview
# ---------------------------------------------------------------------------

def _preview_rank3(
    tensor: ImmutableDenseNDimArray,
    coord_syms: list,
    tensor_symbol: str,
    antisym: bool,
) -> None:
    """
    Show a symbolic summary of a rank-3 tensor after input.

    For each σ slice, renders the n×n matrix as LaTeX so the researcher
    can immediately verify what they entered.
    """
    from sympy import Matrix as spMatrix

    n = tensor.shape[0]
    st.divider()
    st.markdown("**Symbolic preview** — verify your input below:")

    any_nonzero = False
    for sigma in range(n):
        lbl = _sym_label(coord_syms, sigma)
        slice_mat = spMatrix(
            [[tensor[sigma, mu, nu] for nu in range(n)] for mu in range(n)]
        )
        if slice_mat.equals(spMatrix.zeros(n)):
            continue
        any_nonzero = True
        st.markdown(f"**σ = {lbl}**")
        st.latex(latex(slice_mat))

    if not any_nonzero:
        st.info("All components are currently zero.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sym_label(coord_syms: list, i: int) -> str:
    """LaTeX label for coordinate i, rendered in a markdown-safe way."""
    from sympy import latex as sp_latex
    return f"${sp_latex(coord_syms[i])}$"
