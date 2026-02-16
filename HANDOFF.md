# Session Handoff

## State as of 2026-02-16

### What was built this session

**Milestone 3 complete: Streamlit UI** (`feature/streamlit-ui`, merged to `main`)

Three new files:

| File | Purpose |
|---|---|
| `ui/parse.py` | Parse raw user strings into SymPy objects (coords, metric ansatz, constraints) |
| `ui/display.py` | Render SymPy tensors as LaTeX via `st.latex` |
| `app.py` | Streamlit entry point — sidebar input, per-tensor expanders, field equations, constraints |

**UI features:**
- Preset examples: Minkowski, Schwarzschild ansatz, flat polar
- Coordinates and metric ansatz entered as plain text; functions like `A(r)` auto-declared
- Each tensor computed lazily on first expander open, cached in `st.session_state`
- "Simplify (slow)" toggle affects all tensor calls and constraint application
- Field equations expander: generate G_μν = 0, enter constraints line-by-line, apply and see reduced system
- Cache invalidation when inputs change
- README updated with Conceptual Workflow section explaining the ansatz-based approach

**Run:**
```bash
streamlit run app.py
```

---

## Next feature: full EFE starting point (planned, not started)

Currently the app jumps straight to entering a metric ansatz. The user wants to start from the **full Einstein field equations**:

```
G_μν + Λ g_μν = 8πG T_μν
```

and let the user configure each term explicitly before any ansatz is entered. The workflow would look like:

1. **Choose coordinate system** — dimension, coordinate names, signature (`-+++` or `+---`)
2. **Configure the EFE** — user sets:
   - Cosmological constant Λ: `0` / symbolic `Λ` / numeric value
   - Stress-energy tensor T_μν: vacuum (`0`) / perfect fluid / user-specified matrix of expressions
   - Gravitational constant G: `1` (geometric units) / symbolic / numeric
3. **Enter metric ansatz** — based on symmetry assumptions; unknown functions become the ODEs/PDEs to solve
4. **Compute tensors and derive equations** — same pipeline as now, but the RHS of the field equations is whatever T_μν was specified (not hardcoded to 0)
5. **Apply constraints / verify solutions** — same as now

**Key design requirement:** The app must not assume vacuum or any value of Λ unless the user explicitly sets them or loads a preset that does. Presets may pre-fill these fields for convenience but the user should always be able to see and change every assumption.

### What this requires in the codebase

- `field_equations()` in `core/system.py` already accepts a `condition` parameter — needs to accept a full symbolic RHS tensor (T_μν scaled appropriately), not just a scalar
- A new `ui/` widget for configuring T_μν (at minimum: a selectbox for "vacuum / perfect fluid / custom" + a text area for custom expressions)
- The EFE configuration step should output the RHS tensor that gets passed into field equation generation
- Presets should populate all fields (coordinates, metric ansatz, Λ, T_μν, G) consistently

---

## Known caveats

- Schwarzschild constraint verification (applying `A(r) = 1-2M/r`, `B(r) = 1/(1-2M/r)`) requires "Simplify" to be ticked — without simplification the residuals don't structurally cancel to zero
- `Spacetime` objects are not pickle-serializable so `@st.cache_data` is not used; all caching is manual via `st.session_state`
- Computation is slow for symbolic metrics with unknown functions (~60–90s for Schwarzschild full pipeline)
