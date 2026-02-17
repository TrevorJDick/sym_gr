# Session Handoff

## State as of 2026-02-16

### What has been built

#### Core computation pipeline (`core/`)

| File | Purpose |
|------|---------|
| `core/spacetime.py` | `Spacetime` class with lazy-cached tensors |
| `core/tensors.py` | Pure functions: Christoffel, Riemann, Ricci, Einstein |
| `core/derivation.py` | Step-by-step derivation data structures (`ChristoffelStep`, `RiemannStep`, `RhoTerm`) and builders |
| `core/system.py` | `field_equations()` — extracts independent non-trivial equations; supports optional per-component RHS tensor |
| `core/constraints.py` | `apply_constraints()` — substitutes candidate solutions, handles `Derivative` terms correctly |

#### Streamlit UI (`ui/` + `app.py`)

The app is a linear four-section scroll:

1. **EFE Setup** — configure Λ, κ, T_μν; live equation preview
2. **Coordinate System** — preset selector (Cartesian, Spherical, Cylindrical, Schwarzschild), editable coord names, signature −+++ / +−−−, coordinate transform display
3. **Metric Ansatz** — Expression tab (text area) and Grid tab (n×n interactive cells) that stay in sync automatically
4. **Results** — per-tensor expanders with step-by-step toggle, show-zeros toggle, field equations, constraints, export

| File | Purpose |
|------|---------|
| `ui/parse.py` | Parse coord strings, metric expressions, constraints into SymPy |
| `ui/display.py` | LaTeX rendering for rank-2/3/4 tensors and scalars |
| `ui/efe_config.py` | EFE banner, 5-column controls, live equation display, `build_rhs_tensor()` |
| `ui/coord_config.py` | `COORD_PRESETS` dict, `render_coord_config()` |
| `ui/metric_grid.py` | n×n symmetric grid input; auto-syncs with Expression tab |
| `ui/drill_down.py` | Compact overview + selectbox + detail panel for Christoffel and Riemann (no nested expanders) |
| `ui/export.py` | Narrative LaTeX document builder and Python script builder |

#### Presets

| Preset | Λ | T_μν | Coords | Notes |
|--------|---|------|--------|-------|
| Minkowski | 0 | 0 | Cartesian | Flat sanity check |
| Schwarzschild ansatz | 0 | 0 | Spherical | diag(-A(r), B(r), r², r²sin²θ) |
| de Sitter | Λ | 0 | Spherical | Cosmological constant metric |
| Flat polar | 0 | 0 | Spherical | Flat space in spherical coords |

---

### Known caveats

- **Schwarzschild constraint verification**: applying `A(r) = 1-2M/r`, `B(r) = 1/(1-2M/r)` requires "Simplify" to be ticked — without simplification the residuals don't structurally cancel
- **Computation speed**: ~60–90 s for Schwarzschild full pipeline (symbolic derivatives over 4D metric with unknown functions)
- **No pickle / cache_data**: `Spacetime` objects are not serializable; all caching is manual via `st.session_state`
- **Expression ↔ Grid sync**: the sync round-trips through SymPy's `str()` — if SymPy renders a component differently than what the user typed (e.g. `sin(theta)**2` vs `sin(theta)^2`), the cell will update to SymPy's canonical form on first sync

---

### Important implementation notes

#### SymPy gotchas (see MEMORY.md for full details)

- `ImmutableDenseNDimArray`: iterate with `for idx in product(*[range(d) for d in arr.shape])`, not `for c in arr`
- Function substitution inside derivatives: use `replace` + `doit()` (see `core/constraints._function_subs()`)
- `Lambda` name collision: SymPy exports `Lambda` as a function constructor; `_build_local_dict()` in `ui/parse.py` overrides it with `symbols("Lambda")`

#### Streamlit session state patterns

- Preset loading: sets `_last_applied_preset`; only applied when selection changes (prevents rerun-triggered re-fires)
- Expression ↔ Grid sync: `_metric_from_grid` flag set by `on_change` callback; grid→expr runs before text area renders; expr→grid runs after successful parse when `metric_input != _last_expr_synced_to_grid`
- Tensor cache keys in `TENSOR_KEYS`: wiped on input change and preset load

#### Index conventions (Carroll)

- Christoffel: `gamma[σ, μ, ν]` = Γ^σ_μν
- Riemann: `R[ρ, σ, μ, ν]` = R^ρ_σμν (Carroll eq 3.113)
- Ricci: `Ric[μ, ν]` = R^ρ_μρν (contract first & third)
- Einstein: `G[μ, ν]` = R_μν − ½ R g_μν

---

### Potential next steps

- **Constraint drill-down**: step-by-step display of the substitution chain when applying constraints (what each equation looks like after each substitution)
- **Bianchi identity check**: verify `∇_μ G^μν = 0` symbolically for the computed Einstein tensor
- **2D / 3D support**: currently hardcoded to 4D in some places; generalise coordinate dimension
- **More presets**: FLRW cosmological metric, Kerr ansatz, pp-wave
- **Equation numbering in export**: cross-reference derived equations by number in the narrative LaTeX output
- **PDF compilation**: if `tectonic` or `pdflatex` is available, offer a one-click PDF download
