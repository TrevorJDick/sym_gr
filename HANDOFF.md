# Session Handoff

## State as of 2026-02-18 (updated)

### What has been built

#### Core computation pipeline (`core/`)

| File | Purpose |
|------|---------|
| `core/spacetime.py` | `Spacetime` class with lazy-cached tensors |
| `core/tensors.py` | Pure functions: Christoffel, Riemann, Ricci, Einstein, **Bianchi check** |
| `core/derivation.py` | Step-by-step derivation data structures (`ChristoffelStep`, `RiemannStep`, `RhoTerm`) and builders |
| `core/system.py` | `field_equations()` — extracts independent non-trivial equations; supports optional per-component RHS tensor |
| `core/constraints.py` | `apply_constraints()`, `constrain_tensor()`, `simplify_equation_steps()`, `_function_subs()` |
| `core/ansatz.py` | `generate_metric_symbols()`, `apply_metric_constraints()`, `diagonal_constraints()`, `stationary_constraints()` |

#### Streamlit UI (`ui/` + `app.py`)

The app is a linear five-section scroll:

1. **EFE Setup** — configure Λ, κ, T_μν; live equation preview
2. **Coordinate System** — preset selector (Cartesian, Spherical, Cylindrical, Schwarzschild), editable coord names, coordinate transform display
3. **Stress-Energy Tensor T_μν** — Expression tab and Grid tab (synced); used to form the RHS of the EFE
4. **Metric Ansatz** — signature selector, Fill with general ansatz button, Expression/Grid tabs (synced), **Ansatz step log**
5. **Results** — Conventions expander, per-tensor expanders with step-by-step toggle, show-zeros toggle, field equations, constraints, export

| File | Purpose |
|------|---------|
| `ui/parse.py` | Parse coord strings, metric expressions, constraints into SymPy |
| `ui/display.py` | LaTeX rendering for rank-2/3/4 tensors and scalars; `display_equations(start_index=)` |
| `ui/efe_config.py` | EFE banner, 5-column controls, live equation display (actual values rendered), `build_rhs_tensor()` |
| `ui/coord_config.py` | `COORD_PRESETS` dict, `render_coord_config()` (returns `coords_str` only) |
| `ui/metric_grid.py` | n×n symmetric grid input; auto-syncs with Expression tab |
| `ui/drill_down.py` | Compact overview + selectbox + detail panel for Christoffel and Riemann (no nested expanders) |
| `ui/export.py` | Narrative LaTeX document builder and Python script builder; `_sec_symmetry_reductions()` renders applied step log |
| `ui/ansatz_steps.py` | **New.** Ansatz step log UI — sequential constraint application with history, undo, and manual edit recording |

#### Presets

| Preset | Λ | T_μν | Coords | Notes |
|--------|---|------|--------|-------|
| Minkowski | 0 | 0 | Cartesian | Flat sanity check |
| Schwarzschild ansatz | 0 | 0 | Spherical | **Step-based**: general ansatz + 5 pending steps |
| de Sitter | Λ | 0 | Spherical | **Step-based**: same 5 steps as Schwarzschild |
| Flat polar | 0 | 0 | Spherical | Flat space in spherical coords |
| FLRW (flat) | 0 | diag(ρ, pa², pa²r², pa²r²sin²θ) | Spherical | **Step-based**: 6 steps; cosmological principle → Friedmann eqs |
| Anti-de Sitter | -3/L² | 0 | t,z,x,y | **Step-based**: 5 steps; Poincaré patch → f(z)=L²/z² |
| Kerr | 0 | 0 | Spherical | Boyer-Lindquist; off-diagonal; very slow |

---

### Ansatz step log — how it works

The old "Symmetry reductions" expander has been replaced with a sequential step log.

#### Step data structure

Each step is a dict stored in `st.session_state["_ansatz_steps"]`:

```python
{
    "id":           str,           # UUID for stable widget keys
    "description":  str,           # optional label (mainly for presets)
    "step_type":    "constraint" | "edit",
    "content":      str,           # lhs=rhs constraint text, or captured metric string
    "metric_after": str | None,    # metric string after this step applied (None = pending)
    "applied":      bool,
}
```

#### UI behaviour

- **Applied steps** shown as a read-only history log; Undo button on the last applied step only
- **Pending steps** are editable (description + constraint text area + Apply button)
- **＋ Add constraint step** — append a blank pending step
- **Record manual edit as step** — capture the current expression tab state as an applied step
- **↺ Reset steps** — clears all steps and restores `_ansatz_base_metric`
- **Reset to defaults** (sidebar) — restarts the current preset from scratch (all steps pending again, general ansatz regenerated); if no preset, gives general ansatz + empty steps in current coords

#### Metric computation flow

1. `_ansatz_base_metric` — the general ansatz string set when "Fill with general ansatz" is clicked or a step-based preset loads
2. Applying a constraint step: parses the current metric expression, applies `apply_metric_constraints()`, stores `metric_after` in the step, writes result to `_pending_metric_update`
3. `_pending_metric_update` is flushed into `_metric_input` before the text area renders on the next rerun
4. Undo: restores to the previous applied step's `metric_after` (or `_ansatz_base_metric` if first step)

#### Preset loading for step-based presets

Presets with `"ansatz_steps"` key (Schwarzschild, de Sitter, FLRW, Anti-de Sitter):
- Load the general ansatz instead of the final metric
- Pre-populate `_ansatz_steps` with pending steps
- Set `_use_general_ansatz = True` — resolved in Section 4 once `_coord_syms` is parsed

The Schwarzschild preset's 5 steps mirror the textbook derivation:
1. Static metric — t→-t kills time-space cross terms
2. Spherical symmetry — no r-angle or angle-angle mixing
3. SO(3) invariance — angular block must be a round sphere (`g_φφ = sin²θ · g_θθ`)
4. Coordinate choice — define r so `g_θθ = r²`
5. Rename remaining free functions (`g_tt = -A(r)`, `g_rr = B(r)`)

#### Session state keys (ansatz area)

| Key | Purpose |
|-----|---------|
| `_ansatz_steps` | List of step dicts (see structure above) |
| `_ansatz_base_metric` | Metric string before any steps; used by Undo and ↺ Reset |
| `_use_general_ansatz` | Flag set by preset loading; resolved in Section 4 to generate the general ansatz with the correct coord symbols |
| `_pending_metric_update` | Staging key: written by step Apply; flushed into `_metric_input` before text area renders |
| `_sig_info` | Persistent info message when signature change can't auto-update the metric |

#### Key Streamlit gotchas encountered

- **Widget key write-after-render**: cannot write to `st.session_state[key]` after the widget with that key has rendered. Use `_pending_metric_update` for the metric, and `_reset_requested = True` for widget resets.
- **`_reset_requested` pattern**: `_reset_to_defaults()` sets this flag; a block at the very top of `app.py` (before any widget renders) deletes widget keys from session state, causing Streamlit to fall back to each widget's default `value`/`index`. After deleting, `_preset_select` is restored to `_last_applied_preset` (if set) so the preset-loading branch doesn't misfire.
- **Coord widget staleness**: `_coord_preset_select` and `_coords_input` must be set during preset loading (sidebar time, before main body renders), otherwise `render_coord_config()` sees a stale value, triggers its mismatch branch, and overwrites `coords_str` and `metric_str` — breaking the general ansatz generation.

---

### Field equations — what "Generate field equations" actually does

#### Step-by-step pipeline

1. **Build RHS tensor** (`build_rhs_tensor()` in `ui/efe_config.py`)
   - Parses λ (Λ), κ, and T_μν strings via SymPy
   - Computes per-component RHS matrix: `κ·T_μν − Λ·g_μν`
   - For vacuum + no Λ: RHS is the zero matrix

2. **Extract independent equations** (`field_equations()` in `core/system.py`)
   - Iterates upper triangle only (μ ≤ ν), since G_μν is symmetric → at most 10 equations in 4D
   - Drops equations where `G_μν[μ,ν] == RHS[μ,ν]` structurally (e.g. `0 = 0`)
   - Returns `list[sympy.Eq]` of non-trivial independent equations
   - **No simplification is applied here** — equations are raw symbolic expressions

3. **Display** (`display_equations()` in `ui/display.py`)
   - Renders each equation as numbered LaTeX

4. **Apply constraints** (optional, `apply_constraints()` in `core/constraints.py`)
   - User enters substitution rules (e.g. `A(r) = 1 - 2*M/r`)
   - Applies `_function_subs()` to handle functions inside derivatives
   - Drops any equation that becomes trivially satisfied
   - Optionally runs `simplify_equation_steps()` (cancel → trigsimp → simplify) per equation

---

### Known caveats

- **Schwarzschild constraint verification**: applying `A(r) = 1-2M/r`, `B(r) = 1/(1-2M/r)` requires "Simplify" to be ticked — without simplification the residuals don't structurally cancel
- **Computation speed**: ~60–90 s for Schwarzschild full pipeline; Kerr much longer
- **No pickle / cache_data**: `Spacetime` objects are not serializable; all caching is manual via `st.session_state`
- **Expression ↔ Grid sync**: round-trips through SymPy's `str()` — canonical form may differ from user input
- **Stationary condition and symbol ansatz**: `g_t_t` etc. are SymPy `Symbol`s (constants), so ∂_t g_μν = 0 is trivially satisfied. Functional dependence must be introduced explicitly via constraint steps or Grid tab.

---

### Important implementation notes

#### SymPy gotchas (see MEMORY.md for full details)

- `ImmutableDenseNDimArray`: iterate with `for idx in product(*[range(d) for d in arr.shape])`, not `for c in arr`
- Function substitution inside derivatives: use `replace` + `doit()` (see `core/constraints._function_subs()`)
- `Lambda` name collision: SymPy exports `Lambda` as a function constructor; `_build_local_dict()` in `ui/parse.py` overrides it with `symbols("Lambda")`

#### Index conventions (Carroll)

- Christoffel: `gamma[σ, μ, ν]` = Γ^σ_μν
- Riemann: `R[ρ, σ, μ, ν]` = R^ρ_σμν (Carroll eq 3.113)
- Ricci: `Ric[μ, ν]` = R^ρ_μρν (contract first & third)
- Einstein: `G[μ, ν]` = R_μν − ½ R g_μν

---

### Potential next steps

#### Ansatz step log — remaining work

- **Step-based presets**: All four main derivable presets are now step-based:
  Schwarzschild (5 steps), de Sitter (5 steps), FLRW (6 steps), Anti-de Sitter
  (5 steps). Minkowski (definition, no steps), Flat polar (coordinate transform,
  no steps), and Kerr (derivation too complex for constraint steps) remain as
  direct metrics.
- **Step reordering**: currently steps apply in list order; drag-and-drop or up/down buttons would allow reordering without delete-and-re-add.
- **Spherical symmetry as a proper condition**: currently modelled as two separate constraint steps (no mixing + round sphere). A single named step that enforces both `g_φφ = sin²θ·g_θθ` and zeros all angle-mixing terms would be more pedagogical.
- **Rename / introduce functions**: after reducing to free symbols (e.g. `g_t_t`), a step that renames them to named functions (e.g. `g_t_t → -A(r)`) could be a dedicated step type with better UX than a raw constraint.

#### Field equation display improvements

1. **Equation labelling by (μ,ν)**: show "(t,t)", "(t,r)", etc. next to each equation number
2. **RHS construction trace**: show the κ·T_μν − Λ·g_μν matrix before the Generate button
3. **Dropped equations trace**: show which (μ,ν) pairs were dropped as structurally zero
4. **Simplification toggle for raw equations**: extend the cancel→trigsimp→simplify toggle to the initial field equations (currently only available post-constraint)

#### Other

- **More presets**: pp-wave, Reissner-Nordström, FLRW with curvature (k = ±1)
- **PDF compilation**: if `tectonic` or `pdflatex` is available, offer a one-click PDF download
- **Deployment**: Streamlit Community Cloud (free tier) — just needs a `requirements.txt` and a public GitHub repo
