"""
app.py
------
Streamlit UI for sym_gr — interactive symbolic GR tensor computation.

Layout: linear main-area scroll with four sections:
  1. EFE Setup      — configure the Einstein field equation
  2. Coordinate System — choose coordinates and signature
  3. Metric Ansatz  — enter / review the metric
  4. Results        — Christoffel, Riemann, Ricci, Einstein, field equations

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from ui.parse import parse_coords, parse_metric, parse_constraint
from ui.display import (
    display_metric_preview,
    display_rank3_nonzero,
    display_rank4_nonzero,
    display_rank2_nonzero,
    display_scalar,
    display_equations,
)
from ui.efe_config import render_efe_banner, render_efe_controls, render_efe_result, build_rhs_tensor
from ui.coord_config import render_coord_config, COORD_PRESETS

# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict] = {
    "Minkowski": {
        "lambda_str": "0",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Cartesian 4D",
        "signature": "-+++",
        "coords": "t, x, y, z",
        "metric": "diag(-1, 1, 1, 1)",
    },
    "Schwarzschild ansatz": {
        "lambda_str": "0",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Schwarzschild ansatz",
        "signature": "-+++",
        "coords": "t, r, theta, phi",
        "metric": "diag(-A(r), B(r), r**2, r**2*sin(theta)**2)",
    },
    "de Sitter": {
        "lambda_str": "Lambda",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Spherical 4D",
        "signature": "-+++",
        "coords": "t, r, theta, phi",
        "metric": "diag(-1, (1 - Lambda*r**2/3)**(-1), r**2, r**2*sin(theta)**2)",
    },
    "Flat polar": {
        "lambda_str": "0",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Spherical 4D",
        "signature": "-+++",
        "coords": "t, r, theta, phi",
        "metric": "diag(-1, 1, r**2, r**2*sin(theta)**2)",
    },
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="sym_gr — Symbolic GR",
    page_icon=":ringed_planet:",
    layout="wide",
)

st.title("sym_gr — Symbolic General Relativity")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        # EFE terms
        "lambda_str": "0",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        # Coordinate / metric
        "coord_preset": "Cartesian 4D",
        "signature": "-+++",
        "coords_str": "t, x, y, z",
        "metric_str": "diag(-1, 1, 1, 1)",
        # Compute options
        "simplified": False,
        "_input_key": None,
        # Cached tensors
        "spacetime": None,
        "christoffel": None,
        "riemann": None,
        "ricci": None,
        "ricci_scalar": None,
        "einstein": None,
        "field_eqs": None,
        "constrained_eqs": None,
        "rhs_tensor": None,
        # EFE config snapshot used for field-eq title
        "efe_config": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ---------------------------------------------------------------------------
# Helper: wipe cached tensors
# ---------------------------------------------------------------------------

TENSOR_KEYS = [
    "spacetime",
    "christoffel",
    "riemann",
    "ricci",
    "ricci_scalar",
    "einstein",
    "field_eqs",
    "constrained_eqs",
    "rhs_tensor",
]


def _wipe_tensors() -> None:
    for k in TENSOR_KEYS:
        st.session_state[k] = None


# ---------------------------------------------------------------------------
# Sidebar — slim preset loader only
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Load preset")

    preset_choice = st.selectbox(
        "Example spacetime",
        options=["(none)"] + list(PRESETS.keys()),
        index=0,
        key="_preset_select",
    )

    if preset_choice != "(none)":
        p = PRESETS[preset_choice]
        st.session_state["lambda_str"]  = p["lambda_str"]
        st.session_state["kappa_str"]   = p["kappa_str"]
        st.session_state["T_str"]       = p["T_str"]
        st.session_state["coord_preset"] = p["coord_preset"]
        st.session_state["signature"]   = p["signature"]
        st.session_state["coords_str"]  = p["coords"]
        st.session_state["metric_str"]  = p["metric"]
        _wipe_tensors()

# ---------------------------------------------------------------------------
# ── Section 1: EFE Setup ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("1 · Einstein Field Equation")
st.caption(
    "Configure the terms of the EFE. The equation will update live as you fill in the fields."
)

render_efe_banner()
st.markdown("")  # small spacing

lambda_str, kappa_str, T_str = render_efe_controls()

st.markdown("**Resulting equation:**")
render_efe_result(lambda_str, kappa_str, T_str)

st.divider()

# ---------------------------------------------------------------------------
# ── Section 2: Coordinate System ───────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("2 · Coordinate System")

coords_str, metric_hint = render_coord_config()

st.divider()

# ---------------------------------------------------------------------------
# ── Section 3: Metric Ansatz ────────────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("3 · Metric Ansatz")

# If a metric hint came from the coord preset, offer it but let user override
metric_default = st.session_state.get("metric_str", "diag(-1, 1, 1, 1)")

col_metric, col_opts = st.columns([3, 1])
with col_metric:
    metric_input = st.text_area(
        "Metric g_μν",
        value=metric_default,
        height=110,
        key="_metric_input",
        help=(
            "Symmetry-reduced metric. Unknown functions like A(r), B(r) are declared "
            "automatically.\n\nUse diag(...) for diagonal metrics or Matrix([[...], ...]) "
            "for general ones."
        ),
    )
    st.session_state["metric_str"] = metric_input

with col_opts:
    simplified = st.checkbox(
        "Simplify results (slow)",
        value=st.session_state.get("simplified", False),
        key="_simplified_cb",
    )
    st.session_state["simplified"] = simplified

# -- Parse inputs eagerly for error feedback
_parse_ok = True
try:
    _coord_syms = parse_coords(coords_str)
except ValueError as e:
    st.error(f"Coordinate error: {e}")
    _coord_syms = []
    _parse_ok = False

_metric_preview = None
if _parse_ok:
    try:
        _metric_preview = parse_metric(metric_input, _coord_syms)
    except ValueError as e:
        st.error(f"Metric error: {e}")
        _parse_ok = False

# Show metric preview
if _metric_preview is not None:
    with st.expander("Parsed metric preview", expanded=True):
        display_metric_preview(_metric_preview, _coord_syms)

# -- Compute button
compute_clicked = st.button("Compute", type="primary", disabled=not _parse_ok)

if compute_clicked and _parse_ok:
    _wipe_tensors()
    from core.spacetime import Spacetime
    try:
        st.session_state["spacetime"] = Spacetime(_coord_syms, _metric_preview)
        st.session_state["_input_key"] = (
            coords_str,
            metric_input,
            simplified,
            lambda_str,
            kappa_str,
            T_str,
        )
    except Exception as e:
        st.error(f"Spacetime construction failed: {e}")

# Invalidate cache when inputs change
current_key = (coords_str, metric_input, simplified, lambda_str, kappa_str, T_str)
if (
    st.session_state["_input_key"] is not None
    and current_key != st.session_state["_input_key"]
):
    _wipe_tensors()
    st.session_state["_input_key"] = None

st.divider()

# ---------------------------------------------------------------------------
# ── Section 4: Results ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("4 · Results")


def _get_spacetime():
    return st.session_state.get("spacetime")


def _need_compute_msg():
    st.info("Press **Compute** above to run the calculation.")


# ---- Christoffel ----------------------------------------------------------
with st.expander("Christoffel Symbols  Γ^σ_μν"):
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        if st.session_state["christoffel"] is None:
            with st.spinner("Computing Christoffel symbols…"):
                try:
                    st.session_state["christoffel"] = st_obj.christoffel(
                        simplified=simplified
                    )
                except Exception as e:
                    st.error(f"Christoffel computation failed: {e}")
        if st.session_state["christoffel"] is not None:
            display_rank3_nonzero(st.session_state["christoffel"], st_obj.coords)

# ---- Riemann --------------------------------------------------------------
with st.expander("Riemann Tensor  R^ρ_σμν"):
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        if st.session_state["riemann"] is None:
            with st.spinner("Computing Riemann tensor…"):
                try:
                    st.session_state["riemann"] = st_obj.riemann(
                        simplified=simplified
                    )
                except Exception as e:
                    st.error(f"Riemann computation failed: {e}")
        if st.session_state["riemann"] is not None:
            display_rank4_nonzero(st.session_state["riemann"], st_obj.coords)

# ---- Ricci tensor ---------------------------------------------------------
with st.expander("Ricci Tensor  R_μν"):
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        if st.session_state["ricci"] is None:
            with st.spinner("Computing Ricci tensor…"):
                try:
                    st.session_state["ricci"] = st_obj.ricci(
                        simplified=simplified
                    )
                except Exception as e:
                    st.error(f"Ricci computation failed: {e}")
        if st.session_state["ricci"] is not None:
            display_rank2_nonzero(st.session_state["ricci"], st_obj.coords, "R")

# ---- Ricci scalar ---------------------------------------------------------
with st.expander("Ricci Scalar  R"):
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        if st.session_state["ricci_scalar"] is None:
            with st.spinner("Computing Ricci scalar…"):
                try:
                    st.session_state["ricci_scalar"] = st_obj.ricci_scalar(
                        simplified=simplified
                    )
                except Exception as e:
                    st.error(f"Ricci scalar computation failed: {e}")
        if st.session_state["ricci_scalar"] is not None:
            display_scalar(st.session_state["ricci_scalar"], "R")

# ---- Einstein tensor ------------------------------------------------------
with st.expander("Einstein Tensor  G_μν"):
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        if st.session_state["einstein"] is None:
            with st.spinner("Computing Einstein tensor…"):
                try:
                    st.session_state["einstein"] = st_obj.einstein(
                        simplified=simplified
                    )
                except Exception as e:
                    st.error(f"Einstein tensor computation failed: {e}")
        if st.session_state["einstein"] is not None:
            display_rank2_nonzero(
                st.session_state["einstein"], st_obj.coords, "G"
            )

# ---- Field equations -------------------------------------------------------

# Build expander title reflecting EFE config
def _efe_title() -> str:
    lam = st.session_state.get("lambda_str", "0").strip()
    T   = st.session_state.get("T_str", "0").strip()
    lam_zero = lam in ("0", "")
    T_zero   = T   in ("0", "")
    if lam_zero and T_zero:
        return "Field Equations  G_μν = 0  (vacuum)"
    elif not lam_zero and T_zero:
        return "Field Equations  G_μν = −Λ g_μν"
    elif lam_zero and not T_zero:
        return "Field Equations  G_μν = κ T_μν"
    else:
        return "Field Equations  G_μν + Λ g_μν = κ T_μν"


with st.expander(_efe_title()):
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        # Ensure Einstein tensor is available
        if st.session_state["einstein"] is None:
            with st.spinner("Computing Einstein tensor for field equations…"):
                try:
                    st.session_state["einstein"] = st_obj.einstein(
                        simplified=simplified
                    )
                except Exception as e:
                    st.error(f"Einstein tensor computation failed: {e}")

        if st.session_state["einstein"] is not None:
            gen_eqs = st.button("Generate field equations", key="_gen_eqs_btn")

            if gen_eqs or st.session_state["field_eqs"] is not None:
                if gen_eqs or st.session_state["field_eqs"] is None:
                    from core.system import field_equations

                    # Build RHS tensor from EFE config
                    rhs_tensor = None
                    lam = st.session_state.get("lambda_str", "0").strip()
                    T   = st.session_state.get("T_str", "0").strip()
                    lam_zero = lam in ("0", "")
                    T_zero   = T   in ("0", "")

                    if not (lam_zero and T_zero):
                        # Non-vacuum: build per-component RHS
                        try:
                            rhs_tensor = build_rhs_tensor(
                                lambda_str=st.session_state.get("lambda_str", "0"),
                                kappa_str=st.session_state.get("kappa_str", "8*pi*G"),
                                T_str=st.session_state.get("T_str", "0"),
                                metric_matrix=_metric_preview,
                                coord_syms=_coord_syms,
                            )
                            st.session_state["rhs_tensor"] = rhs_tensor
                        except ValueError as e:
                            st.error(f"RHS tensor error: {e}")
                            rhs_tensor = None
                    else:
                        st.session_state["rhs_tensor"] = None

                    try:
                        st.session_state["field_eqs"] = field_equations(
                            st.session_state["einstein"],
                            rhs_tensor=st.session_state["rhs_tensor"],
                        )
                        st.session_state["efe_config"] = (lam, T)
                    except Exception as e:
                        st.error(f"Field equation generation failed: {e}")

                if st.session_state["field_eqs"] is not None:
                    st.subheader("Equations")
                    display_equations(st.session_state["field_eqs"])

                    st.divider()
                    st.subheader("Apply constraints")

                    constraint_text = st.text_area(
                        "Constraints (one per line, e.g.  A(r) = 1 - 2*M/r)",
                        height=100,
                        key="_constraint_text",
                        placeholder="A(r) = 1 - 2*M/r\nB(r) = 1/(1 - 2*M/r)",
                    )

                    apply_btn = st.button(
                        "Apply Constraints", key="_apply_constraints_btn"
                    )

                    if apply_btn:
                        lines = [
                            ln.strip()
                            for ln in constraint_text.splitlines()
                            if ln.strip()
                        ]
                        parsed_constraints = []
                        any_error = False
                        for ln in lines:
                            try:
                                parsed_constraints.append(
                                    parse_constraint(ln, st_obj.coords)
                                )
                            except ValueError as e:
                                st.error(f"Parse error on `{ln}`: {e}")
                                any_error = True

                        if not any_error and parsed_constraints:
                            from core.constraints import apply_constraints
                            with st.spinner("Applying constraints…"):
                                try:
                                    st.session_state["constrained_eqs"] = apply_constraints(
                                        st.session_state["field_eqs"],
                                        parsed_constraints,
                                        auto_simplify=simplified,
                                    )
                                except Exception as e:
                                    st.error(f"Constraint application failed: {e}")
                        elif not lines:
                            st.warning("No constraints entered.")

                    if st.session_state["constrained_eqs"] is not None:
                        st.subheader("Reduced equations")
                        display_equations(st.session_state["constrained_eqs"])
