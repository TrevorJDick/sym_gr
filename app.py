"""
app.py
------
Streamlit UI for sym_gr — interactive symbolic GR tensor computation.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on path so `core` and `ui` packages are importable.
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

# ---------------------------------------------------------------------------
# Preset examples
# ---------------------------------------------------------------------------

PRESETS: dict[str, tuple[str, str]] = {
    "Minkowski": (
        "t, x, y, z",
        "diag(-1, 1, 1, 1)",
    ),
    "Schwarzschild ansatz": (
        "t, r, theta, phi",
        "diag(-A(r), B(r), r**2, r**2*sin(theta)**2)",
    ),
    "Flat polar": (
        "t, r, theta, phi",
        "diag(-1, 1, r**2, r**2*sin(theta)**2)",
    ),
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
# Initialise session state
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        "coords_str": "t, x, y, z",
        "metric_str": "diag(-1, 1, 1, 1)",
        "simplified": False,
        "_input_key": None,
        "spacetime": None,
        "christoffel": None,
        "riemann": None,
        "ricci": None,
        "ricci_scalar": None,
        "einstein": None,
        "field_eqs": None,
        "constrained_eqs": None,
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
]


def _wipe_tensors() -> None:
    for k in TENSOR_KEYS:
        st.session_state[k] = None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Input")

    # -- Preset selector
    preset_choice = st.selectbox(
        "Load example",
        options=["(none)"] + list(PRESETS.keys()),
        index=0,
        key="_preset_select",
    )
    if preset_choice != "(none)":
        coords_preset, metric_preset = PRESETS[preset_choice]
        # Populate fields via session state
        st.session_state["coords_str"] = coords_preset
        st.session_state["metric_str"] = metric_preset
        # Reset preset selector to avoid re-triggering on rerun
        # (Streamlit reruns on every widget interaction; the selectbox
        #  will keep its value but we don't re-apply it.)

    st.divider()

    # -- Coordinate input
    coords_input = st.text_input(
        "Coordinates (comma-separated)",
        value=st.session_state["coords_str"],
        key="_coords_input",
        help="E.g. t, r, theta, phi",
    )
    st.session_state["coords_str"] = coords_input

    # -- Metric input
    metric_input = st.text_area(
        "Metric g_μν",
        value=st.session_state["metric_str"],
        height=120,
        key="_metric_input",
        help="Use diag(...) or Matrix([[...], ...]). "
             "Functions like A(r), B(r) are auto-declared.",
    )
    st.session_state["metric_str"] = metric_input

    # -- Parse inputs eagerly for error feedback
    _parse_ok = True
    try:
        _coord_syms = parse_coords(coords_input)
    except ValueError as e:
        st.error(f"Coordinate error: {e}")
        _coord_syms = []
        _parse_ok = False

    if _parse_ok:
        try:
            _metric_preview = parse_metric(metric_input, _coord_syms)
        except ValueError as e:
            st.error(f"Metric error: {e}")
            _metric_preview = None
            _parse_ok = False
    else:
        _metric_preview = None

    # -- Options
    simplified = st.checkbox(
        "Simplify results (slow)",
        value=st.session_state["simplified"],
        key="_simplified_cb",
    )
    st.session_state["simplified"] = simplified

    st.divider()

    # -- Compute button
    compute_clicked = st.button("Compute", type="primary", disabled=not _parse_ok)

    if compute_clicked and _parse_ok:
        _wipe_tensors()
        from core.spacetime import Spacetime
        try:
            st.session_state["spacetime"] = Spacetime(_coord_syms, _metric_preview)
            st.session_state["_input_key"] = (
                coords_input,
                metric_input,
                simplified,
            )
        except Exception as e:
            st.error(f"Spacetime construction failed: {e}")

    # -- Invalidate cache when inputs change
    current_key = (coords_input, metric_input, simplified)
    if st.session_state["_input_key"] is not None and current_key != st.session_state["_input_key"]:
        _wipe_tensors()
        st.session_state["_input_key"] = None

# ---------------------------------------------------------------------------
# Main area helpers
# ---------------------------------------------------------------------------

def _get_spacetime():
    return st.session_state.get("spacetime")


def _need_compute_msg():
    st.info("Press **Compute** in the sidebar to run the calculation.")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

col_main = st.container()

with col_main:

    # ---- Metric preview -----------------------------------------------
    with st.expander("Parsed Metric Preview", expanded=True):
        if _metric_preview is not None:
            display_metric_preview(_metric_preview, _coord_syms)
        elif _parse_ok:
            st.info("Enter a valid metric and press Compute.")

    # ---- Christoffel --------------------------------------------------
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
                display_rank3_nonzero(
                    st.session_state["christoffel"], st_obj.coords
                )

    # ---- Riemann ------------------------------------------------------
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
                display_rank4_nonzero(
                    st.session_state["riemann"], st_obj.coords
                )

    # ---- Ricci tensor -------------------------------------------------
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
                display_rank2_nonzero(
                    st.session_state["ricci"], st_obj.coords, "R"
                )

    # ---- Ricci scalar -------------------------------------------------
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

    # ---- Einstein tensor ----------------------------------------------
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

    # ---- Field equations ----------------------------------------------
    with st.expander("Field Equations  G_μν = 0"):
        st_obj = _get_spacetime()
        if st_obj is None:
            _need_compute_msg()
        else:
            # Make sure Einstein tensor is available
            if st.session_state["einstein"] is None:
                with st.spinner("Computing Einstein tensor for field equations…"):
                    try:
                        st.session_state["einstein"] = st_obj.einstein(
                            simplified=simplified
                        )
                    except Exception as e:
                        st.error(f"Einstein tensor computation failed: {e}")

            if st.session_state["einstein"] is not None:
                gen_eqs = st.button("Generate G = 0 equations", key="_gen_eqs_btn")
                if gen_eqs or st.session_state["field_eqs"] is not None:
                    if gen_eqs or st.session_state["field_eqs"] is None:
                        from core.system import field_equations
                        try:
                            st.session_state["field_eqs"] = field_equations(
                                st.session_state["einstein"]
                            )
                        except Exception as e:
                            st.error(f"Field equation generation failed: {e}")

                    if st.session_state["field_eqs"] is not None:
                        st.subheader("Equations")
                        display_equations(st.session_state["field_eqs"])

                        st.divider()
                        st.subheader("Apply constraints")

                        # -- Coordinate symbols for the current spacetime
                        coord_syms_for_constraints = st_obj.coords

                        constraint_text = st.text_area(
                            "Constraints (one per line, e.g.  A(r) = 1 - 2*M/r)",
                            height=100,
                            key="_constraint_text",
                            placeholder="A(r) = 1 - 2*M/r\nB(r) = 1/(1 - 2*M/r)",
                        )

                        apply_btn = st.button("Apply Constraints", key="_apply_constraints_btn")

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
                                        parse_constraint(ln, coord_syms_for_constraints)
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
