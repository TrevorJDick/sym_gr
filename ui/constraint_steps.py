"""
ui/constraint_steps.py
----------------------
Field-equation constraint step log — sequential substitution with history.

Each step is a dict:
    {
        "id":           str            # unique widget-key prefix (uuid)
        "description":  str            # optional label
        "step_type":    "constraint"   # only type for now
        "content":      str            # substitution rules, one per line
        "eqs_after":    list | None    # equations after this step (None = pending)
        "applied":      bool
    }

Steps are applied sequentially: each step's eqs_after becomes the input to the
next step.  Undo is O(1) — just mark the last step unapplied and restore from
the previous step's eqs_after (or the raw field equations for step 0).
"""

from __future__ import annotations

import uuid

import streamlit as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_constraint_step(description: str = "", content: str = "") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "description": description,
        "step_type": "constraint",
        "content": content,
        "eqs_after": None,
        "applied": False,
    }


def _current_eqs(field_eqs: list) -> list:
    """Return equations after all applied steps (or the raw field_eqs)."""
    steps = st.session_state.get("_constraint_steps", [])
    for step in reversed(steps):
        if step["applied"] and step["eqs_after"] is not None:
            return step["eqs_after"]
    return field_eqs


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_constraint_steps(
    field_eqs: list,
    coord_syms: list,
    simplified: bool,
) -> None:
    """
    Render the field-equation constraint step log.

    Parameters
    ----------
    field_eqs : list of sympy.Eq
        The raw field equations (before any constraints).
    coord_syms : list
        Coordinate symbols (for parse_constraint).
    simplified : bool
        Whether to auto-simplify after each step.
    """
    from ui.parse import parse_constraint
    from core.constraints import apply_constraints
    from ui.display import display_equations

    steps: list[dict] = st.session_state.setdefault("_constraint_steps", [])

    applied = [s for s in steps if s["applied"]]
    pending = [s for s in steps if not s["applied"]]

    current_eqs = _current_eqs(field_eqs)

    # ── Applied steps (read-only history log) ─────────────────────────────────
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
                st.code(step["content"].strip(), language=None)
                prev_eqs = (
                    applied[rank - 1]["eqs_after"] if rank > 0 else field_eqs
                )
                n_before = len(prev_eqs) if prev_eqs else 0
                n_after = len(step["eqs_after"]) if step["eqs_after"] is not None else 0
                dropped = n_before - n_after
                drop_note = f" ({dropped} dropped)" if dropped else ""
                st.caption(f"{n_before} → {n_after} equations{drop_note}")
            with col_btn:
                if is_last:
                    if st.button("Undo", key=f"_cundo_{step['id']}", use_container_width=True):
                        step["applied"] = False
                        step["eqs_after"] = None
                        st.rerun()

    # ── Pending steps ─────────────────────────────────────────────────────────
    if pending:
        if applied:
            st.divider()
        st.caption("**Pending steps** — edit then apply")

    for step in pending:
        sid = step["id"]
        with st.container(border=True):
            col_desc, col_del = st.columns([5, 0.6])
            with col_desc:
                new_desc = st.text_input(
                    "desc",
                    value=step["description"],
                    key=f"_cdesc_{sid}",
                    placeholder="Description (optional)",
                    label_visibility="collapsed",
                )
                step["description"] = new_desc
            with col_del:
                if st.button("✕", key=f"_cdel_{sid}", help="Delete step"):
                    steps.remove(step)
                    st.rerun()

            new_content = st.text_area(
                "Constraints",
                value=step["content"],
                key=f"_ccontent_{sid}",
                placeholder="A(r) = 1 - 2*M/r\nB(r) = 1/(1 - 2*M/r)",
                height=80,
                label_visibility="collapsed",
            )
            step["content"] = new_content

            apply_label = f"Apply step {len(applied) + 1}"
            if st.button(apply_label, key=f"_capply_{sid}", type="primary"):
                lines = [ln.strip() for ln in new_content.splitlines() if ln.strip()]
                if not lines:
                    st.warning("No constraints entered.")
                    st.stop()

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

                with st.spinner(f"Applying step {len(applied) + 1}…"):
                    try:
                        result = apply_constraints(
                            current_eqs, parsed, auto_simplify=simplified
                        )
                        step["applied"] = True
                        step["eqs_after"] = result
                        st.rerun()
                    except Exception as e:
                        st.error(f"Constraint application failed: {e}")

    # ── Controls ──────────────────────────────────────────────────────────────
    st.divider()
    col_add, col_reset = st.columns([1.5, 1.2])
    with col_add:
        if st.button("＋ Add constraint step", key="_cadd", use_container_width=True):
            steps.append(_make_constraint_step())
            st.rerun()
    with col_reset:
        if applied and st.button(
            "↺ Reset steps",
            key="_creset",
            use_container_width=True,
            help="Clear all applied steps and restore the raw field equations.",
        ):
            st.session_state["_constraint_steps"] = []
            st.session_state["constrained_eqs"] = None
            st.rerun()

    # ── Sync constrained_eqs for export ───────────────────────────────────────
    # Keep session_state["constrained_eqs"] up to date so the export module
    # continues to work without changes.
    if applied:
        st.session_state["constrained_eqs"] = current_eqs
    else:
        st.session_state["constrained_eqs"] = None

    # ── Reduced equations display ──────────────────────────────────────────────
    if not applied:
        return

    st.subheader("Reduced equations")
    remaining = current_eqs

    if not remaining:
        st.success("All equations are satisfied — no residuals remain.")
        return

    _simp_steps_cb = st.checkbox(
        "Show simplification stages",
        key="_chk_csimp_steps",
        help=(
            "For each remaining equation run cancel → trigsimp → simplify "
            "and show which steps change the expression. Slow on large systems."
        ),
    )

    if _simp_steps_cb:
        from core.constraints import simplify_equation_steps
        from sympy import latex as _sp_latex

        for _idx, _eq in enumerate(remaining, start=1):
            st.markdown(f"**Equation {_idx}:**")
            st.latex(
                rf"({_idx})\quad "
                + _sp_latex(_eq.lhs)
                + " = "
                + _sp_latex(_eq.rhs)
            )
            with st.spinner(f"Simplifying equation {_idx}…"):
                _s_steps = simplify_equation_steps(_eq)
            if not _s_steps:
                st.success("Already zero — satisfied identically.")
            else:
                st.caption("LHS − RHS after each stage:")
                for _step_label, _step_expr in _s_steps:
                    _step_latex = _sp_latex(_step_expr)
                    _is_zero = _step_expr == 0
                    _icon = "✓ zero" if _is_zero else ""
                    st.markdown(
                        f"&nbsp;&nbsp;**{_step_label}**: "
                        f"$\\displaystyle {_step_latex}$ {_icon}"
                    )
                if _s_steps and _s_steps[-1][1] != 0:
                    st.warning("Not reduced to zero by available simplifications.")
    else:
        display_equations(remaining)
