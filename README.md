# sym_gr

**Symbolic General Relativity with SymPy**

A Python toolkit for symbolic tensor computation and equation derivation in General Relativity. Built for researchers, educators, and PhD-level students who want a transparent, scriptable symbolic pipeline — from metric ansatz to system of PDEs — using only standard scientific Python.

**License:** MIT — free to use, modify, and distribute for research and education.

---

## What This Is

`sym_gr` provides a clean Python API and an interactive Streamlit UI for:

- Defining a spacetime metric over arbitrary coordinates
- Applying named symmetry reductions (diagonal, static, custom constraints) step by step
- Computing derived geometric objects: Christoffel symbols, Riemann tensor, Ricci tensor, Ricci scalar, Einstein tensor
- Verifying the contracted Bianchi identity ∇_λ G^λ_ν = 0 as a consistency check
- Configuring the full Einstein field equation (Λ, κ, T_μν) before any computation
- Generating field equations with a full verbose derivation trace (RHS construction, dropped components, index labels, Bianchi redundancy)
- Entering constraints as SymPy expressions and reducing the resulting ODE/PDE system
- Exporting the full derivation as a narrative LaTeX document or a runnable Python script

The key design principle: **the toolkit makes no physical assumptions**. The user specifies the metric ansatz, the field equations, and any constraints. The system applies what you tell it to apply.

---

## Conceptual Workflow

In GR, the metric is not known in advance — it is the *solution* to the Einstein field equations. To make the problem tractable, a researcher typically:

1. **Chooses a coordinate system** — e.g. `(t, r, θ, φ)` for spherical coordinates
2. **Applies symmetry assumptions** — e.g. static + spherical symmetry forces the metric to be diagonal
3. **Writes a metric ansatz** — the symmetry-reduced form with unknown functions, e.g.:

   ```
   ds² = -A(r) dt² + B(r) dr² + r² dθ² + r² sin²θ dφ²
   ```

4. **Computes the Einstein tensor** `G_μν` symbolically
5. **Sets physical conditions** — e.g. vacuum (`T_μν = 0`, `Λ = 0`) gives `G_μν = 0`
6. **Applies further constraints** — e.g. a candidate solution to verify it satisfies the equations

**This tool handles all six steps.** Steps 1–3 are supported via coordinate presets, the general ansatz builder, and named symmetry reductions. Steps 4–6 are the core computational pipeline.

---

## What This Is Not

- Not a numerical ODE/PDE solver (though the output equations can be fed into SciPy)
- Not a black-box "give me the Schwarzschild solution" tool
- Not a hardcoded GR library — no built-in physics beyond SymPy's algebra

---

## Running the Streamlit UI

```bash
pip install -e ".[ui]"
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`. It is organised as a linear scrolling page with five sections:

| Section | Purpose |
|---------|---------|
| **1 · EFE Setup** | Configure Λ, κ, and T_μν. The equation preview updates live, rendering the actual values (e.g. `G_μν = 3/L² g_μν` for Anti-de Sitter). |
| **2 · Coordinate System** | Pick a coordinate preset or enter custom coordinates. |
| **3 · Stress-Energy Tensor T_μν** | Enter T_μν via expression or interactive grid; the two stay in sync. |
| **4 · Metric Ansatz** | Enter the metric, or use **Fill with general ansatz** then apply named symmetry reductions (diagonal, static, custom constraints) step by step. |
| **5 · Results** | Expandable panels for each tensor. Toggle step-by-step derivation, show/hide zero components. Generate field equations with optional **Verbose derivation** trace. Verify the Bianchi identity. Apply constraints and simplify. Export to LaTeX or Python. |

**Sidebar:** Load a built-in preset to pre-fill all sections.

| Preset | Physics |
|--------|---------|
| Minkowski | Flat spacetime sanity check |
| Schwarzschild ansatz | Static spherically symmetric vacuum |
| de Sitter | Positive cosmological constant |
| Flat polar | Flat space in spherical coordinates |
| FLRW (flat) | Cosmological metric with scale factor `a(t)` and perfect fluid T_μν |
| Anti-de Sitter | Poincaré patch with Λ = −3/L² |
| Kerr | Rotating black hole in Boyer-Lindquist coordinates (slow) |

**Verbose derivation** (field equations): a single toggle in the Field Equations expander reveals the full derivation trace — RHS construction, dropped 0=0 components, index-labelled equations, per-equation simplification stages, and Bianchi redundancy count. All items flow into the LaTeX export.

**Bianchi identity check**: the Einstein tensor expander includes a "Verify ∇_λ G^λ_ν = 0" button that computes the contracted Bianchi identity component by component as a numerical consistency check.

---

## API

All computation is done through standard SymPy objects. The entry point is a `Spacetime` object.

### Defining a spacetime

```python
from sympy import symbols, Function, sin, diag
from core.spacetime import Spacetime

r, theta = symbols('r theta', positive=True)
A = Function('A')(r)
B = Function('B')(r)

coords = [symbols('t'), r, theta, symbols('phi')]
metric = diag(-A, B, r**2, r**2 * sin(theta)**2)

st = Spacetime(coords, metric)
```

### Computing tensors

```python
# All returned as sympy.tensor.array.ImmutableDenseNDimArray
christoffel = st.christoffel()       # Γ^σ_μν, shape (4,4,4)
riemann     = st.riemann()           # R^ρ_σμν,  shape (4,4,4,4)
ricci       = st.ricci()             # R_μν,     shape (4,4)
ricci_sc    = st.ricci_scalar()      # R,        scalar
einstein    = st.einstein()          # G_μν,     shape (4,4)
```

### Verifying the Bianchi identity

```python
# Returns list of n expressions; all should be zero
residuals = st.bianchi_check()
print(all(c == 0 for c in residuals))  # True
```

### Extracting independent equations

```python
from core.system import field_equations_classified

# Returns equations, (mu,nu) labels, and dropped index pairs
result = field_equations_classified(st.einstein(), condition=0)
print(len(result.equations))  # non-trivial equations
print(result.labels)          # [(mu,nu), ...] for each equation
print(result.dropped)         # [(mu,nu), ...] for 0=0 components
```

### Adding user constraints

```python
from core.constraints import apply_constraints
from sympy import Eq, Function, symbols

r = symbols('r')
A, B = Function('A'), Function('B')

constraints = [
    Eq(A(r), 1 - 2/r),
    Eq(B(r), 1 / (1 - 2/r)),
]

reduced = apply_constraints(result.equations, constraints, auto_simplify=True)
```

### LaTeX output

```python
from sympy import latex, pprint

print(latex(st.einstein()))   # LaTeX string
pprint(st.ricci())             # pretty-printed to terminal
```

---

## Installation

Requires Python 3.11+.

```bash
git clone https://github.com/TrevorJDick/sym_gr.git
cd sym_gr
pip install -e .
```

### Run the examples

**Minkowski sanity check** (fast, ~1s):
```bash
python -m examples.minkowski
```

**Schwarzschild vacuum derivation** (slow, ~60–90s):
```bash
python -m examples.schwarzschild
```

### Run the tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

All 10 tests pass in under 2 seconds.

### Dependencies

| Package | Role | Install |
|---------|------|---------|
| `sympy >= 1.13` | All symbolic computation | core |
| `numpy >= 1.26` | Numerical array support | core |
| `streamlit >= 1.35` | Interactive UI | `.[ui]` |
| `scipy >= 1.13` | Optional ODE solving | `.[numerical]` |
| `pytest >= 8.0` | Tests | `.[dev]` |

---

## Project Structure

```
sym_gr/
├── app.py                    # Streamlit UI entry point
├── core/
│   ├── spacetime.py          # Spacetime class: coordinates + metric + Bianchi check
│   ├── tensors.py            # Christoffel, Riemann, Ricci, Einstein, Bianchi check
│   ├── derivation.py         # Step-by-step derivation data (Christoffel, Riemann)
│   ├── system.py             # field_equations() and field_equations_classified()
│   ├── constraints.py        # Apply user-defined constraints
│   └── ansatz.py             # General metric symbols and symmetry reductions
├── ui/
│   ├── parse.py              # Parse user strings into SymPy objects
│   ├── display.py            # LaTeX rendering helpers
│   ├── efe_config.py         # EFE banner, term controls, RHS tensor builder
│   ├── coord_config.py       # Coordinate presets and signature selector
│   ├── metric_grid.py        # Interactive n×n symmetric metric grid input
│   ├── drill_down.py         # Step-by-step Christoffel / Riemann display
│   └── export.py             # LaTeX document and Python script builders
├── examples/
│   ├── minkowski.py          # Flat spacetime sanity check
│   └── schwarzschild.py      # Vacuum spherically symmetric derivation
├── tests/
│   └── test_tensors.py       # 10 unit tests
├── docs/
│   ├── presets.md            # Documentation and references for all built-in presets
│   └── references.md         # Annotated bibliography
└── pyproject.toml
```

---

## Contributing

Contributions welcome. Please open an issue before submitting a large PR. Code should:

- Use type hints
- Have a corresponding test in `tests/`
- Not introduce dependencies beyond those in `pyproject.toml`

---

## References

See [`docs/references.md`](docs/references.md) for a full annotated bibliography and [`docs/presets.md`](docs/presets.md) for derivation notes and references for each built-in preset.

---

## Acknowledgements

This project builds on SymPy's tensor and differential geometry modules, developed by the SymPy community. See the [SymPy paper](https://peerj.com/articles/cs-103/) for citation details.
