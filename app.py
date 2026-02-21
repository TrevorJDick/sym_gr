"""
app.py
------
Streamlit UI for sym_gr — interactive symbolic GR tensor computation.

Layout: linear main-area scroll with five sections:
  1. EFE Setup      — configure Λ, κ, and the EFE form
  2. Coordinate System — choose coordinates
  3. Stress-Energy Tensor T_μν — enter T_μν in the chosen coordinate basis
  4. Metric Ansatz  — enter / review the metric
  5. Results        — Christoffel, Riemann, Ricci, Einstein, field equations

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
    display_equations_labeled,
)
from ui.efe_config import (
    render_efe_banner,
    render_efe_controls,
    render_efe_result,
    render_constants_helper,
    build_rhs_tensor,
)
from ui.coord_config import render_coord_config, COORD_PRESETS
from ui.drill_down import display_christoffel_steps, display_riemann_steps
from ui.export import build_full_latex, build_python_code, render_export_buttons
from ui.metric_grid import render_metric_grid

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
        "metric": None,  # set from general ansatz via steps
        "ansatz_steps": [
            {
                "description": "Static metric — t→-t symmetry kills time-space cross terms",
                "step_type": "constraint",
                "content": "g_t_r = 0\ng_t_theta = 0\ng_t_phi = 0",
            },
            {
                "description": "Spherical symmetry — no r-angle or angle-angle mixing",
                "step_type": "constraint",
                "content": "g_r_theta = 0\ng_r_phi = 0\ng_theta_phi = 0",
            },
            {
                "description": "SO(3) invariance — angular block must be a round sphere",
                "step_type": "constraint",
                "content": "g_phi_phi = sin(theta)**2 * g_theta_theta",
            },
            {
                "description": "Coordinate choice — define r so the angular area element is 4πr²",
                "step_type": "constraint",
                "content": "g_theta_theta = r**2",
            },
            {
                "description": "Rename the two remaining free functions",
                "step_type": "constraint",
                "content": "g_t_t = -A(r)\ng_r_r = B(r)",
            },
        ],
    },
    "de Sitter": {
        "lambda_str": "Lambda",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Spherical 4D",
        "signature": "-+++",
        "coords": "t, r, theta, phi",
        "metric": None,  # set from general ansatz via steps
        "ansatz_steps": [
            {
                "description": "Static metric — t→-t symmetry kills time-space cross terms",
                "step_type": "constraint",
                "content": "g_t_r = 0\ng_t_theta = 0\ng_t_phi = 0",
            },
            {
                "description": "Spherical symmetry — no r-angle or angle-angle mixing",
                "step_type": "constraint",
                "content": "g_r_theta = 0\ng_r_phi = 0\ng_theta_phi = 0",
            },
            {
                "description": "SO(3) invariance — angular block must be a round sphere",
                "step_type": "constraint",
                "content": "g_phi_phi = sin(theta)**2 * g_theta_theta",
            },
            {
                "description": "Coordinate choice — define r so the angular area element is 4πr²",
                "step_type": "constraint",
                "content": "g_theta_theta = r**2",
            },
            {
                "description": "Rename the two remaining free functions",
                "step_type": "constraint",
                "content": "g_t_t = -f(r)\ng_r_r = h(r)",
            },
        ],
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
    "FLRW (flat)": {
        "lambda_str": "0",
        "kappa_str": "8*pi*G",
        "T_str": "diag(rho, p*a(t)**2, p*a(t)**2*r**2, p*a(t)**2*r**2*sin(theta)**2)",
        "coord_preset": "Spherical 4D",
        "signature": "-+++",
        "coords": "t, r, theta, phi",
        "metric": None,
        "ansatz_steps": [
            {
                "description": "Comoving gauge — homogeneity kills time-space cross terms",
                "step_type": "constraint",
                "content": "g_t_r = 0\ng_t_theta = 0\ng_t_phi = 0",
            },
            {
                "description": "Spatial isotropy — no off-diagonal spatial terms",
                "step_type": "constraint",
                "content": "g_r_theta = 0\ng_r_phi = 0\ng_theta_phi = 0",
            },
            {
                "description": "SO(3) invariance — angular block must be a round sphere",
                "step_type": "constraint",
                "content": "g_phi_phi = sin(theta)**2 * g_theta_theta",
            },
            {
                "description": "Flat spatial slices (k=0) — angular metric is r² times radial metric",
                "step_type": "constraint",
                "content": "g_theta_theta = r**2 * g_r_r",
            },
            {
                "description": "Cosmic time gauge — normalize the lapse function to −1",
                "step_type": "constraint",
                "content": "g_t_t = -1",
            },
            {
                "description": "Introduce the scale factor a(t)",
                "step_type": "constraint",
                "content": "g_r_r = a(t)**2",
            },
        ],
    },
    "Anti-de Sitter": {
        "lambda_str": "-3/L**2",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Cartesian 4D",
        "signature": "-+++",
        "coords": "t, z, x, y",
        "metric": None,
        "ansatz_steps": [
            {
                "description": "Boundary translational symmetry — no bulk-direction time cross terms",
                "step_type": "constraint",
                "content": "g_t_z = 0\ng_t_x = 0\ng_t_y = 0",
            },
            {
                "description": "No mixing between bulk (z) and boundary spatial directions",
                "step_type": "constraint",
                "content": "g_z_x = 0\ng_z_y = 0\ng_x_y = 0",
            },
            {
                "description": "Boundary spatial isotropy — SO(2) symmetry in x-y plane",
                "step_type": "constraint",
                "content": "g_y_y = g_x_x",
            },
            {
                "description": "Conformal flatness — bulk spatial component equals boundary spatial",
                "step_type": "constraint",
                "content": "g_z_z = g_x_x",
            },
            {
                "description": "Introduce the conformal factor f(z)",
                "step_type": "constraint",
                "content": "g_t_t = -f(z)\ng_x_x = f(z)",
            },
        ],
    },
    "Kerr": {
        "lambda_str": "0",
        "kappa_str": "8*pi*G",
        "T_str": "0",
        "coord_preset": "Spherical 4D",
        "signature": "-+++",
        "coords": "t, r, theta, phi",
        "metric": (
            "Matrix(["
            "[-(1 - 2*M*r/(r**2 + a**2*cos(theta)**2)), 0, 0, -2*M*a*r*sin(theta)**2/(r**2 + a**2*cos(theta)**2)], "
            "[0, (r**2 + a**2*cos(theta)**2)/(r**2 - 2*M*r + a**2), 0, 0], "
            "[0, 0, r**2 + a**2*cos(theta)**2, 0], "
            "[-2*M*a*r*sin(theta)**2/(r**2 + a**2*cos(theta)**2), 0, 0, "
            "(r**2 + a**2 + 2*M*a**2*r*sin(theta)**2/(r**2 + a**2*cos(theta)**2))*sin(theta)**2]])"
        ),
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
        "_last_applied_preset": None,
        # Metric Expression ↔ Grid sync
        "_metric_from_grid": False,
        "_last_expr_synced_to_grid": "",
        # T_μν Expression ↔ Grid sync
        "_T_from_grid": False,
        "_last_T_synced_to_grid": "",
        # Cached tensors
        "spacetime": None,
        "christoffel": None,
        "christoffel_steps": None,
        "riemann": None,
        "riemann_steps": None,
        "ricci": None,
        "ricci_scalar": None,
        "einstein": None,
        "bianchi": None,
        "field_eqs": None,
        "field_eq_labels": None,
        "field_eq_dropped": None,
        "constrained_eqs": None,
        "rhs_tensor": None,
        # EFE config snapshot used for field-eq title
        "efe_config": None,
        # Field-equation constraint step log
        "_constraint_steps": [],
        # Signature change info message (None = no message)
        "_sig_info": None,
        # Pending metric update (written by buttons below the text area)
        "_pending_metric_update": None,
        # Ansatz step log
        "_ansatz_steps": [],
        "_ansatz_base_metric": None,
        "_use_general_ansatz": False,
        # Expander open/closed state — persists across reruns
        "_chri_expanded": False,
        "_riem_expanded": False,
        "_ricci_expanded": False,
        "_rscalar_expanded": False,
        "_ein_expanded": False,
        "_efe_expanded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ---------------------------------------------------------------------------
# Handle pending widget reset BEFORE any widget is instantiated.
# _reset_to_defaults() sets _reset_requested=True then calls st.rerun().
# On the subsequent rerun this block runs before any sidebar/main widgets
# are rendered, so deleting their session-state keys is safe and causes
# Streamlit to fall back to each widget's default `value` / `index`.
# ---------------------------------------------------------------------------

if st.session_state.pop("_reset_requested", False):
    _WIDGET_KEYS_TO_CLEAR = [
        "_preset_select",
        "_coord_preset_select",
        "_coords_input",
        "_lambda_input",
        "_kappa_input",
        "_metric_input",
        "_T_input",
    ]
    for _wk in _WIDGET_KEYS_TO_CLEAR:
        st.session_state.pop(_wk, None)
    # Clear grid and step-log widget keys
    for _wk in list(st.session_state.keys()):
        if (
            _wk.startswith("mg_")
            or _wk.startswith("tg_")
            or _wk.startswith("_sdesc_")
            or _wk.startswith("_scontent_")
            or _wk.startswith("_sapply_")
            or _wk.startswith("_sundo_")
            or _wk.startswith("_sdel_")
            or _wk.startswith("_cdesc_")
            or _wk.startswith("_ccontent_")
            or _wk.startswith("_capply_")
            or _wk.startswith("_cundo_")
            or _wk.startswith("_cdel_")
        ):
            del st.session_state[_wk]
    # If resetting within a preset, restore _preset_select so the sidebar
    # preset-loading logic sees no change and doesn't re-apply or clear the
    # carefully prepared preset state (steps, coords, EFE terms).
    _rp = st.session_state.get("_last_applied_preset")
    if _rp:
        st.session_state["_preset_select"] = _rp

# ---------------------------------------------------------------------------
# Helper: wipe cached tensors
# ---------------------------------------------------------------------------

TENSOR_KEYS = [
    "spacetime",
    "christoffel",
    "christoffel_steps",
    "riemann",
    "riemann_steps",
    "ricci",
    "ricci_scalar",
    "einstein",
    "bianchi",
    "field_eqs",
    "field_eq_labels",
    "field_eq_dropped",
    "constrained_eqs",
    "rhs_tensor",
]


_EXPANDED_FLAGS = [
    "_chri_expanded",
    "_riem_expanded",
    "_ricci_expanded",
    "_rscalar_expanded",
    "_ein_expanded",
    "_efe_expanded",
]


def _wipe_tensors() -> None:
    for k in TENSOR_KEYS:
        st.session_state[k] = None
    for k in _EXPANDED_FLAGS:
        st.session_state[k] = False
    # Constraint steps refer to the field equations — clear them too so stale
    # steps don't survive a metric/coordinate change.
    st.session_state["_constraint_steps"] = []


# ---------------------------------------------------------------------------
# Helper: reset all state to defaults
# ---------------------------------------------------------------------------

def _reset_to_defaults() -> None:
    """Reset to the beginning of the current preset, or to a blank general ansatz.

    If a preset is active, all its parameters (coords, EFE terms, steps) are
    restored to their initial values with every step marked pending — effectively
    "restart this derivation from scratch."

    If no preset is active, resets to a general ansatz in the current coordinates
    with an empty step log.

    Widget keys are NOT written directly here because some (e.g. the sidebar
    selectbox) may already be instantiated.  _reset_requested=True causes the
    block at the top of the next rerun to delete those keys safely.
    """
    current_preset = st.session_state.get("_last_applied_preset")
    p = PRESETS.get(current_preset) if current_preset else None

    # Common state to always reset
    common = {
        "simplified": False,
        "_input_key": None,
        "_metric_from_grid": False,
        "_last_expr_synced_to_grid": "",
        "_T_from_grid": False,
        "_last_T_synced_to_grid": "",
        "efe_config": None,
        "_sig_info": None,
        "_pending_metric_update": None,
        "_ansatz_base_metric": None,
        "_reset_requested": True,  # widget keys cleared at top of next rerun
    }
    for k, v in common.items():
        st.session_state[k] = v

    if p:
        # Restore preset parameters
        st.session_state["lambda_str"]   = p["lambda_str"]
        st.session_state["kappa_str"]    = p["kappa_str"]
        st.session_state["T_str"]        = p["T_str"]
        st.session_state["coord_preset"] = p["coord_preset"]
        st.session_state["signature"]    = p["signature"]
        st.session_state["coords_str"]   = p["coords"]
        st.session_state["_coord_preset_select"] = p["coord_preset"]
        st.session_state["_coords_input"] = p["coords"]
        st.session_state["_T_input"] = p["T_str"]

        if p.get("ansatz_steps"):
            from ui.ansatz_steps import _make_step
            st.session_state["_ansatz_steps"] = [
                _make_step(
                    description=s["description"],
                    step_type=s["step_type"],
                    content=s["content"],
                )
                for s in p["ansatz_steps"]
            ]
            st.session_state["_use_general_ansatz"] = True
        else:
            metric = p.get("metric", "")
            st.session_state["metric_str"] = metric
            st.session_state["_ansatz_steps"] = []
            st.session_state["_use_general_ansatz"] = False
    else:
        # No preset — general ansatz in current coordinates, empty step log
        st.session_state["_ansatz_steps"] = []
        st.session_state["_use_general_ansatz"] = True

    # Clear grid widget state
    for key in list(st.session_state.keys()):
        if key.startswith("mg_") or key.startswith("tg_"):
            del st.session_state[key]
    _wipe_tensors()


# ---------------------------------------------------------------------------
# Helpers: Expression ↔ Grid sync (shared by metric and T_μν)
# ---------------------------------------------------------------------------

def _grid_state_to_str(n: int, key_prefix: str = "mg") -> str:
    """Reconstruct a tensor expression string from grid cell session state.

    Prefers individual widget session-state keys (e.g. ``mg_0_0``) over the
    persistent ``mg_grid`` dict, because Streamlit writes the new widget value
    to the individual key *before* the script reruns, whereas the dict is only
    updated inside ``render_metric_grid`` which runs later in the script.
    """
    grid = st.session_state.get(f"{key_prefix}_grid", {})

    def _cell(i: int, j: int) -> str:
        # For symmetric grids the editable widget is always at (min, max).
        ui, uj = min(i, j), max(i, j)
        widget_key = f"{key_prefix}_{ui}_{uj}"
        if widget_key in st.session_state:
            v = st.session_state[widget_key]
            return (v or "0").strip() or "0"
        return (grid.get((ui, uj), "0") or "0").strip() or "0"

    is_diag = all(
        _cell(i, j) in ("0", "")
        for i in range(n) for j in range(n) if i != j
    )
    if is_diag:
        entries = ", ".join(_cell(i, i) for i in range(n))
        return f"diag({entries})"
    rows = []
    for i in range(n):
        row = "[" + ", ".join(_cell(i, j) for j in range(n)) + "]"
        rows.append(row)
    return "Matrix([" + ", ".join(rows) + "])"


def _sync_expr_to_grid(matrix, n: int, key_prefix: str = "mg") -> None:
    """Push a parsed Matrix into the grid widget state."""
    grid_key = f"{key_prefix}_grid"
    if grid_key not in st.session_state:
        st.session_state[grid_key] = {}
    for i in range(n):
        for j in range(i, n):
            val_str = str(matrix[i, j])
            st.session_state[grid_key][(i, j)] = val_str
            st.session_state[f"{key_prefix}_{i}_{j}"] = val_str


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Load preset")

    preset_choice = st.selectbox(
        "Example spacetime",
        options=["(none)"] + list(PRESETS.keys()),
        index=0,
        key="_preset_select",
    )

    _last = st.session_state.get("_last_applied_preset")

    if preset_choice != "(none)" and preset_choice != _last:
        p = PRESETS[preset_choice]
        st.session_state["lambda_str"]   = p["lambda_str"]
        st.session_state["kappa_str"]    = p["kappa_str"]
        st.session_state["T_str"]        = p["T_str"]
        st.session_state["coord_preset"] = p["coord_preset"]
        st.session_state["signature"]    = p["signature"]
        st.session_state["coords_str"]   = p["coords"]
        st.session_state["_T_input"]      = p["T_str"]
        st.session_state["_last_T_synced_to_grid"]    = ""
        st.session_state["_metric_from_grid"] = False
        st.session_state["_T_from_grid"]      = False
        st.session_state["_last_applied_preset"] = preset_choice
        st.session_state["_sig_info"] = None
        # Sync coord widget keys (main body — not yet rendered at sidebar time).
        # Without this, render_coord_config() sees a stale _coord_preset_select
        # value, triggers its mismatch branch, and overwrites coords_str/metric_str.
        st.session_state["_coord_preset_select"] = p["coord_preset"]
        st.session_state["_coords_input"] = p["coords"]

        if p.get("ansatz_steps"):
            # Step-based preset: start from the general ansatz, pre-populate steps.
            from ui.ansatz_steps import _make_step
            st.session_state["_ansatz_steps"] = [
                _make_step(
                    description=s["description"],
                    step_type=s["step_type"],
                    content=s["content"],
                )
                for s in p["ansatz_steps"]
            ]
            st.session_state["_use_general_ansatz"] = True  # resolved in Section 4
        else:
            metric = p.get("metric", "")
            st.session_state["metric_str"]   = metric
            st.session_state["_metric_input"] = metric
            st.session_state["_last_expr_synced_to_grid"] = ""
            st.session_state["_ansatz_steps"] = []
            st.session_state["_ansatz_base_metric"] = None
            st.session_state["_use_general_ansatz"] = False

        _wipe_tensors()
    elif preset_choice == "(none)" and _last is not None:
        # User explicitly cleared the preset — reset to general ansatz with empty steps.
        st.session_state["_last_applied_preset"] = None
        st.session_state["_ansatz_steps"] = []
        st.session_state["_use_general_ansatz"] = True
        _wipe_tensors()

    st.divider()

    if st.button("Reset to defaults", help="Clear all inputs and return to Minkowski defaults."):
        _reset_to_defaults()
        st.rerun()

    st.divider()

    st.subheader("Display")
    font_pct = st.slider(
        "Text size",
        min_value=75,
        max_value=200,
        value=st.session_state.get("_font_pct", 100),
        step=5,
        format="%d%%",
        key="_font_pct_slider",
        help="Scale the text size of the main content area.",
    )
    st.session_state["_font_pct"] = font_pct
    st.caption(
        "**Note:** every button click triggers a full page rerun — "
        "the page will scroll back to the top each time. "
        "This is a Streamlit limitation."
    )
    # Comprehensive text scaling.
    # Setting html font-size only affects rem-based elements; Streamlit uses a
    # mix of rem and hardcoded px, so we also explicitly reset the major text
    # element groups to rem units so they all inherit from the root scale.
    st.markdown(
        f"""<style>
        /* Root — all rem-based elements scale with this */
        html {{ font-size: {font_pct}% !important; }}

        /* Body text and inline elements */
        p, li, a, td, th {{ font-size: 1rem; }}

        /* Headings — keep size hierarchy but scale with root */
        h1 {{ font-size: 2.5rem; }}
        h2 {{ font-size: 2.0rem; }}
        h3 {{ font-size: 1.5rem; }}
        h4 {{ font-size: 1.25rem; }}

        /* Markdown containers */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {{ font-size: 1rem; }}

        /* Caption / small text */
        [data-testid="stCaptionContainer"] p,
        .stCaption p, small {{ font-size: 0.85rem; }}

        /* Widget labels */
        [data-testid="stWidgetLabel"] p {{ font-size: 0.95rem; }}

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {{ font-size: 1rem; }}

        /* Text inputs and text areas */
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {{ font-size: 1rem; }}

        /* Selectbox displayed value */
        [data-baseweb="select"] span {{ font-size: 1rem; }}

        /* Expander header text */
        [data-testid="stExpander"] summary p {{ font-size: 1rem; }}

        /* Tab button text */
        [data-baseweb="tab"] {{ font-size: 1rem; }}

        /* Alert / info / warning / error boxes */
        .stAlert p {{ font-size: 1rem; }}

        /* Sidebar text (keep proportional but don't over-scale controls) */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-size: 0.95rem; }}

        /* KaTeX (st.latex): anchor the container to rem so KaTeX's internal
           em-based sizing inherits the scaled root correctly */
        [data-testid="stLatex"] {{ font-size: 1rem; }}
        .stLatex {{ font-size: 1rem; }}
        .katex {{ font-size: 1.21em; }}
        </style>""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# ── Section 1: EFE Setup ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("1 · Einstein Field Equation")
st.caption(
    "Configure the terms of the EFE. The equation will update live as you fill in the fields."
)

render_efe_banner()
st.markdown("")

lambda_str, kappa_str, T_str = render_efe_controls()

render_constants_helper()

st.divider()

# ---------------------------------------------------------------------------
# ── Section 2: Coordinate System ───────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("2 · Coordinate System")

coords_str = render_coord_config()

# Parse coords here — shared by Sections 3 (T_μν) and 4 (Metric)
_parse_ok = True
try:
    _coord_syms = parse_coords(coords_str)
except ValueError as e:
    st.error(f"Coordinate error: {e}")
    _coord_syms = []
    _parse_ok = False

st.divider()

# ---------------------------------------------------------------------------
# ── Section 3: Stress-Energy Tensor T_μν ───────────────────────────────────
# ---------------------------------------------------------------------------

st.header("3 · Stress-Energy Tensor T_μν")
st.caption(
    "Enter T_μν in the coordinate basis defined above. "
    "Use 0 for vacuum. Typical forms: `diag(rho, p, p, p)` or "
    "`Matrix([[rho,0,0,0],[0,p,0,0],...])`. "
    "T_μν is assumed symmetric — lower triangle mirrors in the Grid tab."
)

# Sync T grid → expression (must happen before the text area renders)
if st.session_state.get("_T_from_grid", False) and _coord_syms:
    _T_n = len(_coord_syms)
    _T_grid_str = _grid_state_to_str(_T_n, key_prefix="tg")
    st.session_state["_T_input"] = _T_grid_str
    st.session_state["T_str"]    = _T_grid_str
    st.session_state["_T_from_grid"] = False
    st.session_state["_last_T_synced_to_grid"] = _T_grid_str

tab_T_expr, tab_T_grid = st.tabs(["Expression", "Grid"])

with tab_T_expr:
    T_input = st.text_area(
        "T_μν",
        value=st.session_state.get("T_str", "0"),
        height=90,
        key="_T_input",
        placeholder="0  or  diag(rho, p, p, p)",
        help=(
            "Stress-energy tensor. Enter 0 for vacuum, or a matrix expression.\n"
            "E.g.  diag(rho, p, p, p)  or  Matrix([[rho,0,0,0],[0,p,0,0],...])"
        ),
        label_visibility="collapsed",
    )
    st.session_state["T_str"] = T_input
    T_str = T_input

    # Sync expression → T grid when expression changes
    if _parse_ok and _coord_syms:
        if T_input != st.session_state.get("_last_T_synced_to_grid", ""):
            if T_input.strip() in ("0", ""):
                from sympy import zeros as _sp_zeros
                _sync_expr_to_grid(_sp_zeros(len(_coord_syms)), len(_coord_syms), key_prefix="tg")
            else:
                try:
                    _T_preview = parse_metric(T_input, _coord_syms)
                    _sync_expr_to_grid(_T_preview, len(_coord_syms), key_prefix="tg")
                except ValueError:
                    pass
            st.session_state["_last_T_synced_to_grid"] = T_input

with tab_T_grid:
    if not _parse_ok or not _coord_syms:
        st.warning("Fix coordinate errors above first.")
    else:
        render_metric_grid(
            len(_coord_syms),
            _coord_syms,
            key_prefix="tg",
            symmetric=True,
            changed_flag="_T_from_grid",
            default_diag="0",
        )

st.markdown("**Resulting equation:**")
render_efe_result(lambda_str, kappa_str, T_str)

st.divider()

# ---------------------------------------------------------------------------
# ── Section 4: Metric Ansatz ────────────────────────────────────────────────
# ---------------------------------------------------------------------------

st.header("4 · Metric Ansatz")

# ── Signature selector ──────────────────────────────────────────────────────
from ui.coord_config import COORD_PRESETS as _COORD_PRESETS
_old_sig = st.session_state.get("signature", "-+++")
_sig = st.radio(
    "Signature",
    options=["-+++", "+---"],
    index=0 if _old_sig == "-+++" else 1,
    horizontal=True,
    key="_signature_radio",
    help=(
        "Sign convention for the metric. −+++ is standard in GR (Carroll, Wald, MTW). "
        "Auto-updates the metric when it matches the coordinate-preset hint. "
        "Custom or named-preset metrics (e.g. de Sitter) must be adjusted manually."
    ),
)
st.session_state["signature"] = _sig

if _sig != _old_sig:
    _cp_data = _COORD_PRESETS.get(st.session_state.get("coord_preset", ""), {})
    _old_hk  = "metric_diag_minus" if _old_sig == "-+++" else "metric_diag_plus"
    _new_hk  = "metric_diag_minus" if _sig    == "-+++" else "metric_diag_plus"
    _old_h   = _cp_data.get(_old_hk)
    _new_h   = _cp_data.get(_new_hk)
    _cur_m   = st.session_state.get("metric_str", "").strip()

    if _new_h is None:
        st.session_state["_sig_info"] = (
            f"No standard metric hint is defined for this coordinate preset "
            f"in **{_sig}** convention. Edit the metric manually."
        )
    elif _old_h is None or _cur_m != _old_h.strip():
        # Metric is custom or from a named preset — don't overwrite it
        st.session_state["_sig_info"] = (
            f"Signature updated to **{_sig}**. Your metric was kept unchanged — "
            f"adjust it manually for the new sign convention."
        )
    else:
        # Metric matches the coord-preset hint → safe to auto-update
        st.session_state["metric_str"] = _new_h
        st.session_state["_metric_input"] = _new_h
        st.session_state["_last_expr_synced_to_grid"] = ""
        st.session_state["_sig_info"] = None

    _wipe_tensors()

if st.session_state.get("_sig_info"):
    st.info(st.session_state["_sig_info"])

# ── General ansatz button ───────────────────────────────────────────────────
if _parse_ok and _coord_syms:
    # Resolve a deferred general-ansatz request (e.g. from a step-based preset)
    if st.session_state.get("_use_general_ansatz"):
        from core.ansatz import generate_metric_symbols
        from ui.metric_grid import _matrix_to_str as _mts
        _gen_mat = generate_metric_symbols(_coord_syms)
        _gen_str = _mts(_gen_mat, len(_coord_syms))
        st.session_state["metric_str"] = _gen_str
        st.session_state["_metric_input"] = _gen_str
        st.session_state["_last_expr_synced_to_grid"] = ""
        st.session_state["_ansatz_base_metric"] = _gen_str
        st.session_state["_use_general_ansatz"] = False
        st.rerun()

    if st.button(
        "Fill with general ansatz",
        key="_gen_ansatz_btn",
        help=(
            "Populate the metric with 16 symbolic components g_μν "
            "(e.g. g_t_t, g_t_r, …). Then use the step log below "
            "to apply physical conditions one at a time."
        ),
    ):
        from core.ansatz import generate_metric_symbols
        from ui.metric_grid import _matrix_to_str as _mts
        _gen_mat = generate_metric_symbols(_coord_syms)
        _gen_str = _mts(_gen_mat, len(_coord_syms))
        st.session_state["metric_str"] = _gen_str
        st.session_state["_metric_input"] = _gen_str
        st.session_state["_last_expr_synced_to_grid"] = ""
        st.session_state["_ansatz_steps"] = []
        st.session_state["_ansatz_base_metric"] = _gen_str
        _wipe_tensors()
        st.rerun()

# ── Metric: sync grid → expression (must happen before text area renders) ──
# Also flush any pending metric update from buttons rendered below the text area.
_pending_m = st.session_state.get("_pending_metric_update")
if _pending_m is not None:
    st.session_state["_metric_input"] = _pending_m
    st.session_state["metric_str"] = _pending_m
    st.session_state["_last_expr_synced_to_grid"] = ""
    st.session_state["_pending_metric_update"] = None

if st.session_state.get("_metric_from_grid", False) and _coord_syms:
    _n = len(_coord_syms)
    _grid_str = _grid_state_to_str(_n)
    st.session_state["_metric_input"] = _grid_str
    st.session_state["metric_str"] = _grid_str
    st.session_state["_metric_from_grid"] = False
    st.session_state["_last_expr_synced_to_grid"] = _grid_str

# -- Metric input: two tabs
tab_expr, tab_grid = st.tabs(["Expression", "Grid"])

_metric_preview = None

with tab_expr:
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
                "automatically.\n\nUse diag(...) for diagonal metrics or "
                "Matrix([[...], ...]) for general ones."
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

    if _parse_ok:
        try:
            _metric_preview = parse_metric(metric_input, _coord_syms)
        except ValueError as e:
            st.error(f"Metric error: {e}")
            _parse_ok = False

    # Sync expression → metric grid when expression changes
    if _parse_ok and _metric_preview is not None and _coord_syms:
        if metric_input != st.session_state.get("_last_expr_synced_to_grid", ""):
            _sync_expr_to_grid(_metric_preview, len(_coord_syms))
            st.session_state["_last_expr_synced_to_grid"] = metric_input

with tab_grid:
    if not _parse_ok or not _coord_syms:
        st.warning("Fix coordinate errors first.")
    else:
        st.caption(
            "Fill in each cell of g_μν directly. "
            "Unknown functions (A(r), B(r), …) are auto-declared. "
            "Changes here are reflected in the Expression tab automatically."
        )
        n_dim = len(_coord_syms)
        render_metric_grid(n_dim, _coord_syms, key_prefix="mg")

# Show metric preview
if _metric_preview is not None:
    with st.expander("Parsed metric preview", expanded=True):
        display_metric_preview(_metric_preview, _coord_syms)

# ── Ansatz step log ──────────────────────────────────────────────────────────
if _parse_ok and _coord_syms:
    from ui.ansatz_steps import render_ansatz_steps
    st.subheader("Ansatz steps")
    st.caption(
        "Build the metric by applying constraint rules one step at a time. "
        "Start with **Fill with general ansatz** above, or type any metric directly "
        "in the Expression tab. Each step applies `lhs = rhs` substitutions to the "
        "current metric and records the result. Undo rolls back one step at a time."
    )
    render_ansatz_steps(_coord_syms, _wipe_tensors)

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

st.header("5 · Results")


def _get_spacetime():
    return st.session_state.get("spacetime")


def _need_compute_msg():
    st.info("Press **Compute** above to run the calculation.")


# ── Conventions reference ────────────────────────────────────────────────────
with st.expander("Conventions & index notation", expanded=False):
    st.caption("Carroll (2004) conventions throughout, signature (−, +, +, +).")
    st.latex(
        r"\Gamma^\sigma{}_{\mu\nu} = \tfrac{1}{2}\,g^{\sigma\rho}"
        r"\!\left(\partial_\mu g_{\nu\rho} + \partial_\nu g_{\mu\rho} - \partial_\rho g_{\mu\nu}\right)"
    )
    st.latex(
        r"R^\rho{}_{\sigma\mu\nu} = \partial_\mu\Gamma^\rho_{\nu\sigma}"
        r" - \partial_\nu\Gamma^\rho_{\mu\sigma}"
        r" + \Gamma^\rho_{\mu\lambda}\Gamma^\lambda_{\nu\sigma}"
        r" - \Gamma^\rho_{\nu\lambda}\Gamma^\lambda_{\mu\sigma}"
    )
    st.latex(
        r"R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}"
        r"\qquad R = g^{\mu\nu}R_{\mu\nu}"
        r"\qquad G_{\mu\nu} = R_{\mu\nu} - \tfrac{1}{2}R\,g_{\mu\nu}"
    )


# Track whether any tensor computed for the first time this render pass.
# If so, we rerun at the end so the updated expanded= flags take effect.
_did_compute = False

# ---- Christoffel ----------------------------------------------------------
with st.expander(
    "Christoffel Symbols  Γ^σ_μν",
    expanded=st.session_state.get("_chri_expanded", False),
):
    st.caption(
        r"Connection coefficients of the metric. "
        r"$\Gamma^\sigma{}_{\mu\nu} = 0$ in locally flat (normal) coordinates; "
        r"non-zero here reflects coordinate curvature, not necessarily spacetime curvature."
    )
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
                    st.session_state["_chri_expanded"] = True
                    _did_compute = True
                except Exception as e:
                    st.error(f"Christoffel computation failed: {e}")

        if st.session_state["christoffel"] is not None:
            opt_cols = st.columns([1, 1, 1, 2])
            with opt_cols[0]:
                chk_drill = st.checkbox(
                    "Step-by-step", key="_chk_chri_drill",
                    help="Show derivation of each component from the metric partials.",
                )
            with opt_cols[1]:
                chk_show_zero = st.checkbox(
                    "Show zero components", key="_chk_chri_zeros",
                    help="Include components that are identically zero.",
                )
            with opt_cols[2]:
                chk_rho_zeros = st.checkbox(
                    "Show vanishing ρ-terms", key="_chk_chri_rho",
                    help="In step-by-step mode: also show ρ-summation terms that vanish, with reasons.",
                )

            if chk_drill:
                if st.session_state["christoffel_steps"] is None:
                    with st.spinner("Computing derivation steps…"):
                        try:
                            from core.derivation import christoffel_steps as _chri_steps
                            st.session_state["christoffel_steps"] = _chri_steps(
                                st_obj.coords, st_obj.metric, st_obj.metric_inverse()
                            )
                        except Exception as e:
                            st.error(f"Derivation steps failed: {e}")

                if st.session_state["christoffel_steps"] is not None:
                    display_christoffel_steps(
                        st.session_state["christoffel_steps"],
                        st_obj.coords,
                        show_zeros=chk_show_zero,
                        show_zero_rho_terms=chk_rho_zeros,
                    )
            else:
                if chk_show_zero:
                    from ui.display import display_rank3_all
                    display_rank3_all(st.session_state["christoffel"], st_obj.coords)
                else:
                    display_rank3_nonzero(
                        st.session_state["christoffel"], st_obj.coords
                    )

            st.divider()
            _latex_out = build_full_latex(
                coords=st_obj.coords,
                metric=st_obj.metric,
                metric_inv=st_obj.metric_inverse(),
                christoffel_steps_data=st.session_state["christoffel_steps"],
                lambda_str=st.session_state.get("lambda_str", "0"),
                kappa_str=st.session_state.get("kappa_str", "8*pi*G"),
                T_str=st.session_state.get("T_str", "0"),
                signature=st.session_state.get("signature", "-+++"),
                applied_symmetries=st.session_state.get("_ansatz_steps", []),
            )
            _py_out = build_python_code(
                coords=st_obj.coords,
                metric=st_obj.metric,
                lambda_str=st.session_state.get("lambda_str", "0"),
                kappa_str=st.session_state.get("kappa_str", "8*pi*G"),
                T_str=st.session_state.get("T_str", "0"),
            )
            render_export_buttons(_latex_out, _py_out, key_prefix="chri_export")

# ---- Riemann --------------------------------------------------------------
with st.expander(
    "Riemann Tensor  R^ρ_σμν",
    expanded=st.session_state.get("_riem_expanded", False),
):
    st.caption(
        r"Measures intrinsic spacetime curvature. "
        r"$R^\rho{}_{\sigma\mu\nu} = 0$ everywhere iff the spacetime is flat. "
        r"Only components with $\mu < \nu$ are shown (antisymmetry in last two indices)."
    )
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
                    st.session_state["_riem_expanded"] = True
                    _did_compute = True
                except Exception as e:
                    st.error(f"Riemann computation failed: {e}")

        if st.session_state["riemann"] is not None:
            opt_cols = st.columns([1, 1, 3])
            with opt_cols[0]:
                chk_riem_drill = st.checkbox(
                    "Step-by-step", key="_chk_riem_drill",
                    help="Show the four named terms for each Riemann component.",
                )
            with opt_cols[1]:
                chk_riem_zeros = st.checkbox(
                    "Show zero components", key="_chk_riem_zeros",
                )

            if chk_riem_drill:
                if st.session_state["riemann_steps"] is None:
                    with st.spinner("Computing Riemann derivation steps…"):
                        try:
                            from core.derivation import riemann_steps as _riem_steps
                            if st.session_state["christoffel"] is None:
                                st.session_state["christoffel"] = st_obj.christoffel(
                                    simplified=simplified
                                )
                            st.session_state["riemann_steps"] = _riem_steps(
                                st_obj.coords, st.session_state["christoffel"]
                            )
                        except Exception as e:
                            st.error(f"Riemann steps failed: {e}")

                if st.session_state["riemann_steps"] is not None:
                    display_riemann_steps(
                        st.session_state["riemann_steps"],
                        st_obj.coords,
                        show_zeros=chk_riem_zeros,
                    )
            else:
                if chk_riem_zeros:
                    from ui.display import display_rank4_all
                    display_rank4_all(st.session_state["riemann"], st_obj.coords)
                else:
                    display_rank4_nonzero(
                        st.session_state["riemann"], st_obj.coords
                    )

# ---- Ricci tensor ---------------------------------------------------------
with st.expander(
    "Ricci Tensor  R_μν",
    expanded=st.session_state.get("_ricci_expanded", False),
):
    st.caption(
        r"$R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}$ — contract Riemann on its 1st and 3rd indices. "
        r"Symmetric: $R_{\mu\nu} = R_{\nu\mu}$. "
        r"Vanishes in vacuum ($G_{\mu\nu} = 0$) only if $R_{\mu\nu} = 0$ (follows from the EFE with $\Lambda = 0$)."
    )
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
                    st.session_state["_ricci_expanded"] = True
                    _did_compute = True
                except Exception as e:
                    st.error(f"Ricci computation failed: {e}")
        if st.session_state["ricci"] is not None:
            chk_ricci_zeros = st.checkbox(
                "Show zero components", key="_chk_ricci_zeros"
            )
            display_rank2_nonzero(
                st.session_state["ricci"], st_obj.coords, "R",
                symmetry=True, show_zeros=chk_ricci_zeros,
            )

# ---- Ricci scalar ---------------------------------------------------------
with st.expander(
    "Ricci Scalar  R",
    expanded=st.session_state.get("_rscalar_expanded", False),
):
    st.caption(
        r"$R = g^{\mu\nu} R_{\mu\nu}$ — full contraction of the Ricci tensor. "
        r"Constant on maximally symmetric spaces (e.g. $R = 4\Lambda$ for de Sitter, $R = -12/L^2$ for AdS)."
    )
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
                    st.session_state["_rscalar_expanded"] = True
                    _did_compute = True
                except Exception as e:
                    st.error(f"Ricci scalar computation failed: {e}")
        if st.session_state["ricci_scalar"] is not None:
            display_scalar(st.session_state["ricci_scalar"], "R")

# ---- Einstein tensor ------------------------------------------------------
with st.expander(
    "Einstein Tensor  G_μν",
    expanded=st.session_state.get("_ein_expanded", False),
):
    st.caption(
        r"$G_{\mu\nu} = R_{\mu\nu} - \tfrac{1}{2}R\,g_{\mu\nu}$ — the LHS of the Einstein field equations. "
        r"Automatically satisfies $\nabla^\mu G_{\mu\nu} = 0$ (contracted Bianchi identity), "
        r"which guarantees $\nabla^\mu T_{\mu\nu} = 0$ (stress-energy conservation)."
    )
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
                    st.session_state["_ein_expanded"] = True
                    _did_compute = True
                except Exception as e:
                    st.error(f"Einstein tensor computation failed: {e}")
        if st.session_state["einstein"] is not None:
            chk_ein_zeros = st.checkbox(
                "Show zero components", key="_chk_ein_zeros"
            )
            display_rank2_nonzero(
                st.session_state["einstein"], st_obj.coords, "G",
                symmetry=True, show_zeros=chk_ein_zeros,
            )

            st.divider()
            st.markdown("**Contracted Bianchi identity**")
            st.caption(
                r"$\nabla_\lambda G^\lambda{}_\nu = 0$ is a mathematical identity "
                r"satisfied by any Einstein tensor computed from a metric-compatible connection. "
                r"Verifying it numerically confirms internal consistency of the computation."
            )
            bianchi_btn = st.button(
                "Verify  ∇_λ G^λ_ν = 0",
                key="_bianchi_btn",
                help=(
                    "Computes the covariant divergence of the mixed Einstein tensor G^λ_ν "
                    "for each coordinate index ν. All n components should cancel to zero."
                ),
            )
            if bianchi_btn or st.session_state.get("bianchi") is not None:
                if bianchi_btn or st.session_state["bianchi"] is None:
                    with st.spinner("Computing Bianchi identity check…"):
                        try:
                            st.session_state["bianchi"] = st_obj.bianchi_check(
                                simplified=simplified
                            )
                        except Exception as e:
                            st.error(f"Bianchi check failed: {e}")

                if st.session_state["bianchi"] is not None:
                    from sympy import latex as _bianchi_latex
                    bianchi_res = st.session_state["bianchi"]
                    all_zero = all(c == 0 for c in bianchi_res)
                    if all_zero:
                        st.success("✓ All components are identically zero — identity confirmed.")
                    else:
                        for _nu, _c in enumerate(bianchi_res):
                            _nu_label = str(st_obj.coords[_nu])
                            if _c == 0:
                                st.markdown(
                                    rf"$\nabla_\lambda G^\lambda{{}}_{{{_nu_label}}} = 0$ ✓"
                                )
                            else:
                                st.latex(
                                    rf"\nabla_\lambda G^\lambda{{}}_{{{_nu_label}}} = "
                                    + _bianchi_latex(_c)
                                )
                        st.caption(
                            "Non-zero residuals above may still vanish under stronger simplification. "
                            "Enable **Simplify results** in the metric section and recompute."
                        )

# ---- Field equations -------------------------------------------------------

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


with st.expander(
    _efe_title(),
    expanded=st.session_state.get("_efe_expanded", False),
):
    st.caption(
        "Independent non-trivial components of the Einstein field equations, "
        "after removing duplicates (symmetry of $G_{\\mu\\nu}$) and identically zero equations. "
        "The contracted Bianchi identity $\\nabla_\\lambda G^\\lambda{}_\\nu = 0$ "
        "provides $n$ further constraints, reducing the 10 metric unknowns to at most 6 truly "
        "independent equations — verify this with the button in the Einstein tensor expander above. "
        "Enter substitution rules below to apply a known solution or equation of state and verify residuals."
    )
    st_obj = _get_spacetime()
    if st_obj is None:
        _need_compute_msg()
    else:
        if st.session_state["einstein"] is None:
            with st.spinner("Computing Einstein tensor for field equations…"):
                try:
                    st.session_state["einstein"] = st_obj.einstein(
                        simplified=simplified
                    )
                    st.session_state["_ein_expanded"] = True
                    _did_compute = True
                except Exception as e:
                    st.error(f"Einstein tensor computation failed: {e}")

        if st.session_state["einstein"] is not None:
            gen_eqs = st.button("Generate field equations", key="_gen_eqs_btn")

            if gen_eqs or st.session_state["field_eqs"] is not None:
                if gen_eqs or st.session_state["field_eqs"] is None:
                    from core.system import field_equations_classified

                    rhs_tensor = None
                    lam = st.session_state.get("lambda_str", "0").strip()
                    T   = st.session_state.get("T_str", "0").strip()
                    lam_zero = lam in ("0", "")
                    T_zero   = T   in ("0", "")

                    if not (lam_zero and T_zero):
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
                        _feq_result = field_equations_classified(
                            st.session_state["einstein"],
                            rhs_tensor=st.session_state["rhs_tensor"],
                        )
                        st.session_state["field_eqs"]       = _feq_result.equations
                        st.session_state["field_eq_labels"] = _feq_result.labels
                        st.session_state["field_eq_dropped"] = _feq_result.dropped
                        st.session_state["efe_config"] = (lam, T)
                        st.session_state["_efe_expanded"] = True
                        # New field equations — old constraint steps are stale.
                        st.session_state["_constraint_steps"] = []
                        st.session_state["constrained_eqs"] = None
                        _did_compute = True
                    except Exception as e:
                        st.error(f"Field equation generation failed: {e}")

                if st.session_state["field_eqs"] is not None:
                    st.subheader("Equations")
                    _verbose_efe = st.checkbox(
                        "Verbose derivation",
                        key="_chk_efe_verbose",
                        help=(
                            "Show the full derivation trace: RHS construction, "
                            "dropped components, index-labelled equations, "
                            "per-equation simplification stages, and Bianchi redundancy. "
                            "All items are included in the LaTeX export when this is checked."
                        ),
                    )

                    if _verbose_efe:
                        from sympy import latex as _sp_latex, Matrix as _SpMat

                        # ── 1. RHS construction ───────────────────────────────
                        st.markdown("**1 · RHS construction: κ·T_μν − Λ·g_μν**")
                        _rhs = st.session_state.get("rhs_tensor")
                        if _rhs is None:
                            st.caption(
                                "Λ = 0 and T_μν = 0 → RHS = 0 for every component."
                            )
                        else:
                            _n = len(st_obj.coords)
                            _rhs_mat = _SpMat(
                                [[_rhs[mu, nu] for nu in range(_n)] for mu in range(_n)]
                            )
                            from sympy import latex as _sp_latex2
                            st.latex(
                                r"\mathrm{RHS}_{\mu\nu} = \kappa T_{\mu\nu}"
                                r" - \Lambda g_{\mu\nu} = "
                                + _sp_latex2(_rhs_mat)
                            )

                        # ── 2. Dropped components ─────────────────────────────
                        st.markdown("**2 · Dropped components (structurally 0 = 0)**")
                        _dropped = st.session_state.get("field_eq_dropped") or []
                        _labels  = st.session_state.get("field_eq_labels") or []
                        _n_upper = len(st_obj.coords) * (len(st_obj.coords) + 1) // 2
                        if _dropped:
                            st.caption(
                                f"{len(_dropped)} of {_n_upper} upper-triangle components "
                                "are identically satisfied and excluded:"
                            )
                            _drop_strs = [
                                rf"$\mu={_sp_latex(st_obj.coords[mu])},\;"
                                rf"\nu={_sp_latex(st_obj.coords[nu])}$"
                                for mu, nu in _dropped
                            ]
                            st.markdown("  ·  ".join(_drop_strs), unsafe_allow_html=True)
                        else:
                            st.caption(
                                f"All {_n_upper} upper-triangle components are non-trivial "
                                "(none dropped)."
                            )

                        # ── 3. Labeled equations ──────────────────────────────
                        st.markdown(
                            f"**3 · Field equations "
                            f"({len(st.session_state['field_eqs'])} surviving)**"
                        )
                        display_equations_labeled(
                            st.session_state["field_eqs"],
                            _labels,
                            st_obj.coords,
                        )

                        # ── 4. Per-equation simplification (opt-in) ───────────
                        _efe_simp_cb = st.checkbox(
                            "Show per-equation simplification stages",
                            key="_chk_efe_verbose_simp",
                            help=(
                                "For each field equation run cancel → trigsimp → simplify "
                                "and show which steps change the expression. "
                                "Slow on large symbolic metrics."
                            ),
                        )
                        if _efe_simp_cb:
                            from core.constraints import simplify_equation_steps
                            for _vi, (_veq, (_vmu, _vnu)) in enumerate(
                                zip(st.session_state["field_eqs"], _labels), start=1
                            ):
                                _vc_mu = _sp_latex(st_obj.coords[_vmu])
                                _vc_nu = _sp_latex(st_obj.coords[_vnu])
                                st.markdown(
                                    f"**Equation ({_vi})** "
                                    rf"$[\mu={_vc_mu},\,\nu={_vc_nu}]$:"
                                )
                                st.latex(
                                    rf"({_vi})\quad {_sp_latex(_veq.lhs)}"
                                    rf" = {_sp_latex(_veq.rhs)}"
                                )
                                with st.spinner(f"Simplifying equation ({_vi})…"):
                                    _vs = simplify_equation_steps(_veq)
                                if not _vs:
                                    st.caption("Already in simplified form.")
                                else:
                                    st.caption("LHS − RHS after each stage:")
                                    for _vl, _ve in _vs:
                                        _iz = _ve == 0
                                        st.markdown(
                                            f"&nbsp;&nbsp;**{_vl}**: "
                                            f"$\\displaystyle {_sp_latex(_ve)}$"
                                            + (" ✓ zero" if _iz else "")
                                        )

                        # ── 5. Bianchi redundancy ─────────────────────────────
                        st.markdown("**4 · Bianchi redundancy**")
                        _bianchi = st.session_state.get("bianchi")
                        _n_eqs   = len(st.session_state["field_eqs"])
                        if _bianchi is not None:
                            _b_all_zero = all(c == 0 for c in _bianchi)
                            _n_b = len(_bianchi)
                            if _b_all_zero:
                                st.success(
                                    f"Bianchi identity verified (∇_λ G^λ_ν = 0 for all "
                                    f"{_n_b} coordinates). Among the {_n_eqs} surviving "
                                    f"equations, at most {max(0, _n_eqs - _n_b)} are truly "
                                    "independent."
                                )
                            else:
                                st.warning(
                                    "Bianchi identity has non-zero residuals — "
                                    "enable Simplify results and recompute."
                                )
                        else:
                            st.info(
                                "Bianchi identity not yet checked. "
                                "Use the **Verify ∇_λ G^λ_ν = 0** button in the "
                                "Einstein tensor expander above, then return here."
                            )
                    else:
                        display_equations(st.session_state["field_eqs"])

                    st.divider()
                    st.subheader("Constraint steps")
                    st.caption(
                        "Apply substitution rules one step at a time to reduce the field equations. "
                        "Each step's output becomes the input to the next step. "
                        "Undo rolls back one step at a time."
                    )
                    from ui.constraint_steps import render_constraint_steps
                    render_constraint_steps(
                        field_eqs=st.session_state["field_eqs"],
                        coord_syms=st_obj.coords,
                        simplified=simplified,
                    )

# Trigger a rerun whenever a tensor computed for the first time this pass,
# so the updated expanded= flags take effect immediately.
if _did_compute:
    st.rerun()

# ---------------------------------------------------------------------------
# ── Full derivation export ──────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_st_obj = _get_spacetime()
if _st_obj is not None:
    st.divider()
    st.subheader("Export full derivation")
    st.caption(
        "Download a complete LaTeX document or Python script covering all "
        "computed tensors and field equations."
    )
    _full_latex = build_full_latex(
        coords=_st_obj.coords,
        metric=_st_obj.metric,
        metric_inv=_st_obj.metric_inverse(),
        christoffel_steps_data=st.session_state.get("christoffel_steps"),
        riemann=st.session_state.get("riemann"),
        ricci=st.session_state.get("ricci"),
        ricci_scalar=st.session_state.get("ricci_scalar"),
        einstein=st.session_state.get("einstein"),
        field_eqs=st.session_state.get("field_eqs"),
        constrained_eqs=st.session_state.get("constrained_eqs"),
        constraint_steps=st.session_state.get("_constraint_steps", []),
        lambda_str=st.session_state.get("lambda_str", "0"),
        kappa_str=st.session_state.get("kappa_str", "8*pi*G"),
        T_str=st.session_state.get("T_str", "0"),
        signature=st.session_state.get("signature", "-+++"),
        applied_symmetries=st.session_state.get("_ansatz_steps", []),
        field_eq_verbose=st.session_state.get("_chk_efe_verbose", False),
        field_eq_labels=st.session_state.get("field_eq_labels"),
        field_eq_dropped=st.session_state.get("field_eq_dropped"),
        rhs_tensor=st.session_state.get("rhs_tensor"),
        bianchi_results=st.session_state.get("bianchi"),
    )
    _full_py = build_python_code(
        coords=_st_obj.coords,
        metric=_st_obj.metric,
        lambda_str=st.session_state.get("lambda_str", "0"),
        kappa_str=st.session_state.get("kappa_str", "8*pi*G"),
        T_str=st.session_state.get("T_str", "0"),
        with_field_eqs=True,
    )
    render_export_buttons(_full_latex, _full_py, key_prefix="full_export")
