# Session Handoff

## State as of 2026-02-17

### What has been built

#### Core computation pipeline (`core/`)

| File | Purpose |
|------|---------|
| `core/spacetime.py` | `Spacetime` class with lazy-cached tensors |
| `core/tensors.py` | Pure functions: Christoffel, Riemann, Ricci, Einstein |
| `core/derivation.py` | Step-by-step derivation data structures (`ChristoffelStep`, `RiemannStep`, `RhoTerm`) and builders |
| `core/system.py` | `field_equations()` — extracts independent non-trivial equations; supports optional per-component RHS tensor |
| `core/constraints.py` | `apply_constraints()`, `constrain_tensor()`, `simplify_equation_steps()`, `_function_subs()` |
| `core/ansatz.py` | `generate_metric_symbols()`, `apply_metric_constraints()`, `diagonal_constraints()`, `stationary_constraints()` |

#### Streamlit UI (`ui/` + `app.py`)

The app is a linear five-section scroll:

1. **EFE Setup** — configure Λ, κ, T_μν; live equation preview
2. **Coordinate System** — preset selector (Cartesian, Spherical, Cylindrical, Schwarzschild), editable coord names, coordinate transform display
3. **Stress-Energy Tensor T_μν** — Expression tab and Grid tab (synced); used to form the RHS of the EFE
4. **Metric Ansatz** — signature selector, Fill with general ansatz button, Expression/Grid tabs (synced), Symmetry reductions expander
5. **Results** — per-tensor expanders with step-by-step toggle, show-zeros toggle, field equations, constraints, export

| File | Purpose |
|------|---------|
| `ui/parse.py` | Parse coord strings, metric expressions, constraints into SymPy |
| `ui/display.py` | LaTeX rendering for rank-2/3/4 tensors and scalars; `display_equations(start_index=)` |
| `ui/efe_config.py` | EFE banner, 5-column controls, live equation display, `build_rhs_tensor()` |
| `ui/coord_config.py` | `COORD_PRESETS` dict, `render_coord_config()` (returns `coords_str` only) |
| `ui/metric_grid.py` | n×n symmetric grid input; auto-syncs with Expression tab |
| `ui/drill_down.py` | Compact overview + selectbox + detail panel for Christoffel and Riemann (no nested expanders) |
| `ui/export.py` | Narrative LaTeX document builder and Python script builder; `_sec_symmetry_reductions()` for derivation export |

#### Presets

| Preset | Λ | T_μν | Coords | Notes |
|--------|---|------|--------|-------|
| Minkowski | 0 | 0 | Cartesian | Flat sanity check |
| Schwarzschild ansatz | 0 | 0 | Spherical | diag(-A(r), B(r), r², r²sin²θ) |
| de Sitter | Λ | 0 | Spherical | Cosmological constant metric |
| Flat polar | 0 | 0 | Spherical | Flat space in spherical coords |

---

### Metric Ansatz workflow

#### General ansatz + symmetry reductions (new in `feature/ansatz-variables`)

1. Press **Fill with general ansatz** → metric populated with `g_t_t, g_t_r, …` symbols (fully general, all components independent). `_applied_symmetries` list is cleared.
2. Open **Symmetry reductions** expander, apply named conditions:
   - **Diagonal** — zeros all off-diagonal entries via `diagonal_constraints()` + `apply_metric_constraints()`
   - **Static (t → −t)** — zeros all time–space cross terms via `stationary_constraints()` + `apply_metric_constraints()`; derivation: under t→−t the Jacobian is diag(−1,1,…,1), so g_ti → −g_ti; invariance requires g_ti = 0
   - **Custom constraints** — text area for `lhs = rhs` rules (e.g. `g_t_t = -A(r)`); applied via `apply_metric_constraints()`
3. Each symmetry button appends to `_applied_symmetries` session-state list (e.g. `["diagonal", "static"]`).
4. On export, `_sec_symmetry_reductions()` generates a LaTeX section with full algebraic derivation for each applied symmetry. Passes through `build_full_latex(applied_symmetries=...)`.

#### Session state keys (metric/ansatz area)

| Key | Purpose |
|-----|---------|
| `_pending_metric_update` | Staging key for buttons that can't write `_metric_input` directly (rendered below the text area). Flushed before the text area renders. |
| `_applied_symmetries` | List of symmetry names applied to the current metric (e.g. `["diagonal", "static"]`). Cleared on preset load and Fill with general ansatz. |
| `_sig_info` | Persistent info message when signature change can't auto-update the metric (e.g. custom or named-preset metrics). |

---

### Known caveats

- **Schwarzschild constraint verification**: applying `A(r) = 1-2M/r`, `B(r) = 1/(1-2M/r)` requires "Simplify" to be ticked — without simplification the residuals don't structurally cancel
- **Computation speed**: ~60–90 s for Schwarzschild full pipeline (symbolic derivatives over 4D metric with unknown functions)
- **No pickle / cache_data**: `Spacetime` objects are not serializable; all caching is manual via `st.session_state`
- **Expression ↔ Grid sync**: the sync round-trips through SymPy's `str()` — if SymPy renders a component differently than what the user typed, the cell will update to SymPy's canonical form on first sync
- **Stationary condition and symbol ansatz**: `g_t_t` etc. are SymPy `Symbol`s (constants), so ∂_t g_μν = 0 is trivially satisfied for all coordinates. Functional dependence must be introduced explicitly via the Grid tab or custom constraints.

---

### Important implementation notes

#### SymPy gotchas (see MEMORY.md for full details)

- `ImmutableDenseNDimArray`: iterate with `for idx in product(*[range(d) for d in arr.shape])`, not `for c in arr`
- Function substitution inside derivatives: use `replace` + `doit()` (see `core/constraints._function_subs()`)
- `Lambda` name collision: SymPy exports `Lambda` as a function constructor; `_build_local_dict()` in `ui/parse.py` overrides it with `symbols("Lambda")`

#### Streamlit session state patterns

- Preset loading: sets `_last_applied_preset`; only applied when selection changes (prevents rerun-triggered re-fires)
- Expression ↔ Grid sync: `_metric_from_grid` flag set by `on_change` callback; grid→expr runs before text area renders; expr→grid runs after successful parse when `metric_input != _last_expr_synced_to_grid`
- `_pending_metric_update` staging: buttons below the text area write to this key; it is flushed into `_metric_input` before the text area renders on the next rerun
- Tensor cache keys in `TENSOR_KEYS`: wiped on input change and preset load
- Expander persistence: `_X_expanded` flags + `st.rerun()` after first compute so expanded= takes effect

#### Index conventions (Carroll)

- Christoffel: `gamma[σ, μ, ν]` = Γ^σ_μν
- Riemann: `R[ρ, σ, μ, ν]` = R^ρ_σμν (Carroll eq 3.113)
- Ricci: `Ric[μ, ν]` = R^ρ_μρν (contract first & third)
- Einstein: `G[μ, ν]` = R_μν − ½ R g_μν

---

### Potential next steps

- **More symmetry conditions**: spherical symmetry (g_θφ = 0, g_rθ = 0, etc.), axisymmetry (Killing vector ∂_φ), FLRW homogeneity
- **Ansatz parameter labelling**: after Fill + reductions, offer a button to rename surviving diagonal symbols to user-chosen function names (e.g. rename `g_t_t` → `A(r)`)
- **Constraint drill-down**: step-by-step display of the substitution chain when applying constraints
- **Bianchi identity check**: verify `∇_μ G^μν = 0` symbolically for the computed Einstein tensor
- **More presets**: FLRW cosmological metric, Kerr ansatz, pp-wave
- **PDF compilation**: if `tectonic` or `pdflatex` is available, offer a one-click PDF download
