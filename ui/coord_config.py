"""
ui/coord_config.py
------------------
Coordinate system selection widget with preset transforms and metric hints.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Preset definitions
# ---------------------------------------------------------------------------

COORD_PRESETS: dict[str, dict] = {
    "Cartesian 4D": {
        "coords": "t, x, y, z",
        "transforms": None,
        "metric_diag_minus": "diag(-1, 1, 1, 1)",
        "metric_diag_plus":  "diag(1, -1, -1, -1)",
    },
    "Spherical 4D": {
        "coords": "t, r, theta, phi",
        "transforms": [
            r"x = r\sin\theta\cos\phi",
            r"y = r\sin\theta\sin\phi",
            r"z = r\cos\theta",
        ],
        "metric_diag_minus": "diag(-1, 1, r**2, r**2*sin(theta)**2)",
        "metric_diag_plus":  "diag(1, -1, -r**2, -r**2*sin(theta)**2)",
    },
    "Cylindrical 4D": {
        "coords": "t, rho, phi, z",
        "transforms": [
            r"x = \rho\cos\phi",
            r"y = \rho\sin\phi",
        ],
        "metric_diag_minus": "diag(-1, 1, rho**2, 1)",
        "metric_diag_plus":  "diag(1, -1, -rho**2, -1)",
    },
    "Schwarzschild ansatz": {
        "coords": "t, r, theta, phi",
        "transforms": [
            r"x = r\sin\theta\cos\phi",
            r"y = r\sin\theta\sin\phi",
            r"z = r\cos\theta",
        ],
        "metric_diag_minus": "diag(-A(r), B(r), r**2, r**2*sin(theta)**2)",
        "metric_diag_plus":  None,   # ansatz — only defined for −+++
    },
    "Custom": {
        "coords": "",
        "transforms": None,
        "metric_diag_minus": None,
        "metric_diag_plus":  None,
    },
}

# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

def render_coord_config() -> tuple[str, str]:
    """
    Render coordinate system selector.

    Returns
    -------
    (coords_str, metric_hint_str)
        coords_str     — editable coordinate list string
        metric_hint_str — suggested metric string for the ansatz section
                          (may be None if no hint available)
    """
    col_preset, col_coords = st.columns([1, 2])

    with col_preset:
        preset_names = list(COORD_PRESETS.keys())
        current_preset = st.session_state.get("coord_preset", "Cartesian 4D")
        if current_preset not in preset_names:
            current_preset = "Cartesian 4D"

        chosen = st.selectbox(
            "Coordinate preset",
            options=preset_names,
            index=preset_names.index(current_preset),
            key="_coord_preset_select",
        )
        # Only update if the preset actually changed
        if chosen != st.session_state.get("coord_preset"):
            st.session_state["coord_preset"] = chosen
            preset_data = COORD_PRESETS[chosen]
            if preset_data["coords"]:
                st.session_state["coords_str"] = preset_data["coords"]
            # Reset metric hint to force re-population
            sig = st.session_state.get("signature", "-+++")
            hint_key = "metric_diag_minus" if sig == "-+++" else "metric_diag_plus"
            hint = preset_data.get(hint_key)
            if hint:
                st.session_state["metric_str"] = hint
                st.session_state["_metric_input"] = hint
                st.session_state["_last_expr_synced_to_grid"] = ""

    with col_coords:
        coords_input = st.text_input(
            "Coordinates (comma-separated)",
            value=st.session_state.get("coords_str", "t, x, y, z"),
            key="_coords_input",
            help="Coordinate names used throughout the calculation.",
        )
        st.session_state["coords_str"] = coords_input

    # --- Signature radio
    sig = st.radio(
        "Signature",
        options=["-+++", "+---"],
        index=0 if st.session_state.get("signature", "-+++") == "-+++" else 1,
        horizontal=True,
        key="_signature_radio",
        help="Sign convention for the metric.  −+++ is standard in GR (e.g. Carroll).",
    )
    old_sig = st.session_state.get("signature", "-+++")
    st.session_state["signature"] = sig

    # If signature changed, update metric hint
    if sig != old_sig:
        preset_data = COORD_PRESETS.get(st.session_state.get("coord_preset", ""), {})
        hint_key = "metric_diag_minus" if sig == "-+++" else "metric_diag_plus"
        hint = preset_data.get(hint_key)
        if hint:
            st.session_state["metric_str"] = hint
            st.session_state["_metric_input"] = hint
            st.session_state["_last_expr_synced_to_grid"] = ""

    # --- Show coordinate transforms if preset has them
    preset_data = COORD_PRESETS.get(chosen, {})
    transforms = preset_data.get("transforms")
    if transforms:
        with st.expander("Coordinate transforms", expanded=False):
            for t in transforms:
                st.latex(t)

    # Determine metric hint
    hint_key = "metric_diag_minus" if sig == "-+++" else "metric_diag_plus"
    metric_hint = preset_data.get(hint_key)

    return coords_input, metric_hint
