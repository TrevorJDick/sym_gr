# Session Handoff

## State as of 2026-02-17 (updated)

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

1. **EFE Setup** — configure Λ, κ, T_μν; live equation preview (now renders actual parsed values, not generic symbols)
2. **Coordinate System** — preset selector (Cartesian, Spherical, Cylindrical, Schwarzschild), editable coord names, coordinate transform display
3. **Stress-Energy Tensor T_μν** — Expression tab and Grid tab (synced); used to form the RHS of the EFE
4. **Metric Ansatz** — signature selector, Fill with general ansatz button, Expression/Grid tabs (synced), Symmetry reductions expander
5. **Results** — Conventions expander, per-tensor expanders with step-by-step toggle, show-zeros toggle, field equations, constraints, export

| File | Purpose |
|------|---------|
| `ui/parse.py` | Parse coord strings, metric expressions, constraints into SymPy |
| `ui/display.py` | LaTeX rendering for rank-2/3/4 tensors and scalars; `display_equations(start_index=)` |
| `ui/efe_config.py` | EFE banner, 5-column controls, live equation display (actual values rendered), `build_rhs_tensor()` |
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
| FLRW (flat) | 0 | diag(ρ, pa², pa²r², pa²r²sin²θ) | Spherical | Scale factor a(t); gives Friedmann eqs |
| Anti-de Sitter | -3/L² | 0 | t,z,x,y | Poincaré patch; conformally flat |
| Kerr | 0 | 0 | Spherical | Boyer-Lindquist; off-diagonal; very slow |

---

### Field equations — what "Generate field equations" actually does

This is the step users interact with last, and where most display clarity is needed.

#### Step-by-step pipeline

1. **Build RHS tensor** (`build_rhs_tensor()` in `ui/efe_config.py`)
   - Parses λ (Λ), κ, and T_μν strings via SymPy
   - Computes per-component RHS matrix: `κ·T_μν − Λ·g_μν`
   - For vacuum + no Λ: RHS is the zero matrix
   - For AdS (Λ = −3/L²): RHS = (3/L²)·g_μν per component

2. **Extract independent equations** (`field_equations()` in `core/system.py`)
   - Iterates upper triangle only (μ ≤ ν), since G_μν is symmetric → at most 10 equations in 4D
   - Drops equations where `G_μν[μ,ν] == RHS[μ,ν]` structurally (e.g. `0 = 0`)
   - Returns `list[sympy.Eq]` of non-trivial independent equations
   - **No simplification is applied here** — equations are raw symbolic expressions

3. **Display** (`display_equations()` in `ui/display.py`)
   - Renders each equation as numbered LaTeX
   - No further reduction unless user clicks "Apply Constraints"

4. **Apply constraints** (optional, `apply_constraints()` in `core/constraints.py`)
   - User enters substitution rules (e.g. `A(r) = 1 - 2*M/r`)
   - Applies `_function_subs()` to handle functions inside derivatives
   - Drops any equation that becomes trivially satisfied
   - Optionally runs `simplify_equation_steps()` (cancel → trigsimp → simplify) per equation

#### What is NOT shown / NOT done automatically

- **No intermediate derivation trace**: the user sees the final G_μν = RHS equations, not how G was assembled from R_μν and R
- **No simplification by default**: raw symbolic expressions from SymPy, which can be long for ansatz metrics
- **No Bianchi reduction**: the Bianchi identity check (in the Einstein expander) shows that ∇_λ G^λ_ν = 0 holds, but this is computed separately and doesn't automatically remove equations from the field equation list
- **No explanation of which equations are independent vs. redundant**: the upper-triangle filter handles symmetry, but Bianchi redundancy (which further reduces 10→6) is not surfaced in the field equations display

---

### Metric Ansatz workflow

#### General ansatz + symmetry reductions

1. Press **Fill with general ansatz** → metric populated with `g_t_t, g_t_r, …` symbols. `_applied_symmetries` list is cleared.
2. Open **Symmetry reductions** expander, apply named conditions:
   - **Diagonal** — zeros all off-diagonal entries
   - **Static (t → −t)** — zeros all time–space cross terms
   - **Custom constraints** — text area for `lhs = rhs` rules
3. Each symmetry button appends to `_applied_symmetries` session-state list.
4. On export, `_sec_symmetry_reductions()` generates a LaTeX section with full algebraic derivation.

#### Session state keys (metric/ansatz area)

| Key | Purpose |
|-----|---------|
| `_pending_metric_update` | Staging key for buttons that can't write `_metric_input` directly. Flushed before the text area renders. |
| `_applied_symmetries` | List of symmetry names applied to the current metric. Cleared on preset load and Fill with general ansatz. |
| `_sig_info` | Persistent info message when signature change can't auto-update the metric. |

---

### Known caveats

- **Schwarzschild constraint verification**: applying `A(r) = 1-2M/r`, `B(r) = 1/(1-2M/r)` requires "Simplify" to be ticked — without simplification the residuals don't structurally cancel
- **Computation speed**: ~60–90 s for Schwarzschild full pipeline; Kerr much longer
- **No pickle / cache_data**: `Spacetime` objects are not serializable; all caching is manual via `st.session_state`
- **Expression ↔ Grid sync**: round-trips through SymPy's `str()` — canonical form may differ from user input
- **Stationary condition and symbol ansatz**: `g_t_t` etc. are SymPy `Symbol`s (constants), so ∂_t g_μν = 0 is trivially satisfied. Functional dependence must be introduced explicitly via Grid tab or custom constraints.

---

### Important implementation notes

#### SymPy gotchas (see MEMORY.md for full details)

- `ImmutableDenseNDimArray`: iterate with `for idx in product(*[range(d) for d in arr.shape])`, not `for c in arr`
- Function substitution inside derivatives: use `replace` + `doit()` (see `core/constraints._function_subs()`)
- `Lambda` name collision: SymPy exports `Lambda` as a function constructor; `_build_local_dict()` in `ui/parse.py` overrides it with `symbols("Lambda")`

#### Streamlit session state patterns

- Preset loading: sets `_last_applied_preset`; only applied when selection changes
- Expression ↔ Grid sync: `_metric_from_grid` flag set by `on_change` callback; grid→expr runs before text area renders; expr→grid runs after successful parse
- `_pending_metric_update` staging: buttons below the text area write to this key; flushed into `_metric_input` before the text area renders on the next rerun
- Tensor cache keys in `TENSOR_KEYS`: wiped on input change and preset load (includes `"bianchi"`)
- Expander persistence: `_X_expanded` flags + `st.rerun()` after first compute

#### Index conventions (Carroll)

- Christoffel: `gamma[σ, μ, ν]` = Γ^σ_μν
- Riemann: `R[ρ, σ, μ, ν]` = R^ρ_σμν (Carroll eq 3.113)
- Ricci: `Ric[μ, ν]` = R^ρ_μρν (contract first & third)
- Einstein: `G[μ, ν]` = R_μν − ½ R g_μν

---

### Potential next steps

#### Priority: display improvements around field equations

The user explicitly wants more clarity about what is shown and what steps occur. Key areas:

1. **Field equation provenance / step trace**
   - Currently: user sees final `G_μν = RHS` equations with no context about how they were assembled
   - Desired: show which (μ,ν) components were dropped (structurally zero), which survive, and why
   - Possible approach: add an optional "Show dropped equations" toggle alongside the existing display

2. **Bianchi reduction display**
   - The Bianchi identity check lives in the Einstein expander but has no connection to the field equations list
   - The field equations caption mentions Bianchi reduces 10→6, but doesn't show *which* equations are Bianchi-redundant
   - Possible approach: after Bianchi check confirms identity, annotate or highlight the `n` equations that are linearly dependent via the identity

3. **RHS construction trace**
   - `build_rhs_tensor()` silently computes κ·T_μν − Λ·g_μν
   - Users may not understand what the per-component RHS is before generating equations
   - Possible approach: show the RHS tensor as a preview matrix before the "Generate field equations" button, similar to the parsed metric preview in Section 4

4. **Intermediate simplification display**
   - Raw G_μν components can be very long before simplification
   - The "Show simplification stages" checkbox (cancel → trigsimp → simplify) exists for constrained equations but not for the raw field equations
   - Possible approach: add the same per-step simplification toggle to the initial field equation display

5. **Equation numbering and labelling**
   - Equations are numbered sequentially but not labelled by their index pair (μ, ν)
   - Possible approach: show "(μ=0, ν=0)" or "(t,t)" annotations next to each equation number

#### Other potential next steps

- **More symmetry conditions**: spherical symmetry (g_θφ = 0), axisymmetry (Killing vector ∂_φ), FLRW homogeneity
- **Ansatz parameter labelling**: after Fill + reductions, rename surviving symbols to user-chosen function names (e.g. rename `g_t_t` → `A(r)`)
- **Constraint drill-down**: step-by-step display of the substitution chain when applying constraints
- **PDF compilation**: if `tectonic` or `pdflatex` is available, offer a one-click PDF download
- **More presets**: pp-wave, Reissner-Nordström, FLRW with curvature (k = ±1)
- **Deployment**: Streamlit Community Cloud (free tier) — just needs a `requirements.txt` and a public GitHub repo; secrets not required for this app
