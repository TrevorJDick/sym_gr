"""
ui/ansatz_steps.py
------------------
Ansatz step log — sequential constraint application with history.

Each step is a dict:
    {
        "id":           str           # unique widget-key prefix (uuid)
        "description":  str           # optional label (mainly for presets)
        "step_type":    "constraint" | "edit"
        "content":      str           # constraint text OR captured metric string
        "metric_after": str | None    # metric after this step (None = pending)
        "applied":      bool
    }

The step log replaces the old "Symmetry reductions" expander. Steps are
applied sequentially to the current metric; each step stores the resulting
metric string so that Undo is O(1) (no re-derivation needed).
"""

from __future__ import annotations

import uuid

import streamlit as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_step(
    description: str = "",
    step_type: str = "constraint",
    content: str = "",
    applied: bool = False,
    metric_after: str | None = None,
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "description": description,
        "step_type": step_type,
        "content": content,
        "metric_after": metric_after,
        "applied": applied,
    }


def _current_metric_str() -> str:
    """Return the metric string after all applied steps (or the base)."""
    steps = st.session_state.get("_ansatz_steps", [])
    for step in reversed(steps):
        if step["applied"] and step["metric_after"]:
            return step["metric_after"]
    return st.session_state.get("_ansatz_base_metric") or st.session_state.get("metric_str", "")


def _push_metric(new_str: str, wipe_fn) -> None:
    """Stage a new metric string for the next rerun and wipe tensor cache.

    Writes to _pending_metric_update (not _metric_input directly) because
    the text area widget keyed to _metric_input has already rendered by the
    time the step log runs.  The pending value is flushed into _metric_input
    before the text area renders on the subsequent rerun.
    """
    st.session_state["metric_str"] = new_str
    st.session_state["_pending_metric_update"] = new_str
    st.session_state["_last_expr_synced_to_grid"] = ""
    wipe_fn()


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_ansatz_steps(coord_syms: list, wipe_tensors_fn) -> None:
    """
    Render the ansatz step log.

    Parameters
    ----------
    coord_syms : list of sympy.Symbol
        Parsed coordinate symbols (needed for constraint parsing / metric parsing).
    wipe_tensors_fn : callable
        Callback that clears the cached tensor results.
    """
    from ui.parse import parse_constraint, parse_metric
    from core.ansatz import apply_metric_constraints
    from ui.metric_grid import _matrix_to_str as _mts

    steps: list[dict] = st.session_state.setdefault("_ansatz_steps", [])

    applied = [s for s in steps if s["applied"]]
    pending = [s for s in steps if not s["applied"]]

    # ── Applied steps (read-only history log) ────────────────────────────────
    if applied:
        st.caption("**Applied steps**")
        for rank, step in enumerate(applied):
            is_last = rank == len(applied) - 1
            col_num, col_content, col_btn = st.columns([0.25, 3.75, 0.8])
            with col_num:
                st.markdown(f"**{rank + 1}**")
            with col_content:
                if step["description"]:
                    st.caption(step["description"])
                if step["step_type"] == "constraint":
                    st.code(step["content"].strip(), language=None)
                else:
                    st.caption("_manual edit_")
            with col_btn:
                if is_last:
                    if st.button("Undo", key=f"_undo_{step['id']}", use_container_width=True):
                        # Restore to state before this step
                        prev_applied = [s for s in steps if s["applied"]][:-1]
                        restore = (
                            prev_applied[-1]["metric_after"]
                            if prev_applied
                            else st.session_state.get("_ansatz_base_metric", "")
                        )
                        step["applied"] = False
                        step["metric_after"] = None
                        _push_metric(restore, wipe_tensors_fn)
                        st.rerun()

    # ── Pending steps ─────────────────────────────────────────────────────────
    if pending:
        if applied:
            st.divider()
        st.caption("**Pending steps** — edit then apply")

    for step in pending:
        sid = step["id"]
        with st.container(border=True):
            # Description row
            col_desc, col_del = st.columns([5, 0.6])
            with col_desc:
                new_desc = st.text_input(
                    "desc",
                    value=step["description"],
                    key=f"_sdesc_{sid}",
                    placeholder="Description (optional)",
                    label_visibility="collapsed",
                )
                step["description"] = new_desc
            with col_del:
                if st.button("✕", key=f"_sdel_{sid}", help="Delete step"):
                    steps.remove(step)
                    st.rerun()

            # Constraint text area
            new_content = st.text_area(
                "Constraints",
                value=step["content"],
                key=f"_scontent_{sid}",
                placeholder="g_t_r = 0\ng_t_theta = 0\ng_phi_phi = sin(theta)**2 * g_theta_theta",
                height=80,
                label_visibility="collapsed",
            )
            step["content"] = new_content

            # Apply button
            apply_label = f"Apply step {len(applied) + 1}"
            if st.button(apply_label, key=f"_sapply_{sid}", type="primary"):
                lines = [ln.strip() for ln in new_content.splitlines() if ln.strip()]
                if not lines:
                    st.warning("No constraints entered.")
                    st.stop()

                # Parse current metric
                current_str = _current_metric_str()
                try:
                    current_mat = parse_metric(current_str, coord_syms)
                except ValueError as e:
                    st.error(f"Could not parse current metric: {e}")
                    st.stop()

                # Parse constraints
                parsed = []
                any_error = False
                for ln in lines:
                    try:
                        parsed.append(parse_constraint(ln, coord_syms))
                    except ValueError as e:
                        st.error(f"Parse error `{ln}`: {e}")
                        any_error = True
                if any_error:
                    st.stop()

                new_mat = apply_metric_constraints(current_mat, parsed, coord_syms)
                new_str = _mts(new_mat, len(coord_syms))
                step["applied"] = True
                step["metric_after"] = new_str
                _push_metric(new_str, wipe_tensors_fn)
                st.rerun()

    # ── Controls ──────────────────────────────────────────────────────────────
    st.divider()
    col_add, col_rec, col_reset = st.columns([1.4, 1.8, 1.2])

    with col_add:
        if st.button("＋ Add constraint step", key="_sadd", use_container_width=True):
            steps.append(_make_step())
            st.rerun()

    with col_rec:
        if st.button(
            "Record manual edit as step",
            key="_srec",
            use_container_width=True,
            help="Capture the current metric expression as a step in the log.",
        ):
            current_str = st.session_state.get("metric_str", "")
            steps.append(
                _make_step(
                    description="Manual edit",
                    step_type="edit",
                    content=current_str,
                    applied=True,
                    metric_after=current_str,
                )
            )
            wipe_tensors_fn()
            st.rerun()

    with col_reset:
        if steps and st.button(
            "↺ Reset steps",
            key="_sreset",
            use_container_width=True,
            help="Clear all steps and restore the base metric.",
        ):
            base = st.session_state.get("_ansatz_base_metric", "")
            st.session_state["_ansatz_steps"] = []
            if base:
                _push_metric(base, wipe_tensors_fn)
            st.rerun()
