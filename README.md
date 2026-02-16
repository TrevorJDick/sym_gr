# sym_gr

**Symbolic General Relativity with SymPy**

A Python toolkit for symbolic tensor computation and equation derivation in General Relativity. Built for researchers, educators, and PhD-level students who want a transparent, scriptable symbolic pipeline — from metric ansatz to system of PDEs — using only standard scientific Python.

**License:** MIT — free to use, modify, and distribute for research and education.

---

## What This Is

`sym_gr` provides a clean Python API for:

- Defining a spacetime metric over arbitrary coordinates
- Computing derived geometric objects: Christoffel symbols, Riemann tensor, Ricci tensor, Ricci scalar, Einstein tensor
- Entering field equations and constraints as SymPy expressions
- Extracting and simplifying the resulting system of independent PDEs/ODEs
- Rendering every step as LaTeX via a Streamlit interface

The key design principle: **the toolkit makes no physical assumptions**. The user specifies the metric ansatz, the field equations, and any constraints (Bianchi identities, symmetry conditions, gauge choices). The system applies what you tell it to apply.

---

## Conceptual Workflow

In GR, the metric is not known in advance — it is the *solution* to the Einstein field equations. To make the problem tractable, a researcher typically:

1. **Chooses a coordinate system** — e.g. `(t, r, θ, φ)` for spherical coordinates
2. **Applies symmetry assumptions** — e.g. static (no time dependence) + spherical symmetry forces the metric to be diagonal with specific structure
3. **Writes a metric ansatz** — the symmetry-reduced form with unknown functions standing in for the components not yet determined, e.g.:

   ```
   ds² = -A(r) dt² + B(r) dr² + r² dθ² + r² sin²θ dφ²
   ```

   Here `A(r)` and `B(r)` are unknown functions. The ansatz encodes *what you know about the solution's structure* without assuming the solution itself.

4. **Computes the Einstein tensor** `G_μν` symbolically — this produces expressions in terms of `A(r)`, `B(r)`, and their derivatives
5. **Sets physical conditions** — e.g. vacuum (`T_μν = 0`, `Λ = 0`) gives `G_μν = 0`, yielding a system of ODEs for `A(r)` and `B(r)`
6. **Applies further constraints** — e.g. Bianchi identities, boundary conditions, or a candidate solution to verify it satisfies the equations

**This tool handles steps 4–6.** Steps 1–3 are the researcher's physical reasoning — the tool takes that ansatz as input.

---

## What This Is Not

- Not a numerical ODE/PDE solver (though the output equations can be fed into SciPy)
- Not a black-box "give me the Schwarzschild solution" tool
- Not a hardcoded GR library — no built-in physics beyond SymPy's algebra

---

## Milestones

### Milestone 1 — Minkowski sanity check

Input the known flat-space metric `diag(-1, 1, 1, 1)` in Cartesian coordinates `(t, x, y, z)`. Every derived tensor should be identically zero — this validates that the pipeline computes correct zero results for the simplest case.

### Milestone 2 — Schwarzschild metric from vacuum EFE

Input the spherically symmetric static ansatz with unknown functions:

```
ds² = -A(r) dt² + B(r) dr² + r² dΩ²
```

Apply vacuum field equations `G_μν = 0` to derive the ODE system for `A(r)` and `B(r)`. Verify that the known Schwarzschild solution `A(r) = 1 - 2M/r`, `B(r) = (1 - 2M/r)⁻¹` satisfies those equations identically.

### Milestone 3 — Interactive Streamlit UI

Wrap the computation pipeline in a Streamlit app where users can:

- Enter a coordinate system and metric ansatz in plain text
- Compute all GR tensors and view them rendered as LaTeX
- Generate vacuum field equations with one click
- Apply constraints (candidate solutions, Bianchi conditions, gauge choices) and see the reduced equation system

---

## API

All computation is done through standard SymPy objects. The entry point is a `Spacetime` object that takes coordinates and a metric matrix.

### Defining a spacetime

```python
from sympy import symbols, Function, diag
from sym_gr.core.spacetime import Spacetime

r, theta = symbols('r theta', positive=True)
A = Function('A')(r)
B = Function('B')(r)

# Spherically symmetric static ansatz
coords = [symbols('t'), r, theta, symbols('phi')]
metric = diag(-A, B, r**2, r**2 * sin(theta)**2)

st = Spacetime(coords, metric)
```

### Computing tensors

```python
# All returned as sympy.tensor.array.ImmutableDenseNDimArray
christoffel = st.christoffel()       # Γ^σ_μν, shape (4,4,4)
riemann     = st.riemann()           # R^σ_μνρ, shape (4,4,4,4)
ricci       = st.ricci()             # R_μν,    shape (4,4)
ricci_sc    = st.ricci_scalar()      # R,       scalar
einstein    = st.einstein()          # G_μν,    shape (4,4)
```

### Extracting independent equations

```python
from sym_gr.core.system import field_equations

# Vacuum EFE: G_μν = 0
eqs = field_equations(st.einstein(), condition=0)
# Returns list of sympy.Eq objects for independent non-trivial components
```

### Adding user constraints

```python
from sym_gr.core.constraints import apply_constraints
from sympy import Eq

# User-specified: e.g. off-diagonal metric components vanish
constraints = [
    Eq(st.metric[0, 1], 0),
    Eq(st.metric[0, 2], 0),
]

reduced = apply_constraints(eqs, constraints)
```

### LaTeX output

Every SymPy expression converts directly:

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

**Milestone 1 — Minkowski** (fast, ~1s):
```bash
python -m examples.minkowski
```

**Milestone 2 — Schwarzschild** (slow, ~60–90s — symbolic derivatives over a 4D metric):
```bash
python -m examples.schwarzschild
```

### Run the tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

All 10 tests should pass in under 2 seconds.

### Running the UI (coming in Milestone 3)

```bash
pip install -e ".[ui]"
streamlit run app.py
```

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
│   ├── spacetime.py          # Spacetime class: coordinates + metric
│   ├── tensors.py            # Christoffel, Riemann, Ricci, Einstein
│   ├── system.py             # Extract independent field equations
│   └── constraints.py        # Apply user-defined constraints
├── ui/
│   ├── input_metric.py       # Streamlit metric/coordinate input widgets
│   ├── input_equations.py    # Streamlit equation/constraint input
│   └── display.py            # LaTeX rendering helpers (sympy.latex → st.latex)
├── examples/
│   ├── minkowski.py          # Milestone 1: flat spacetime
│   ├── schwarzschild.py      # Milestone 2: vacuum spherically symmetric
│   └── flrw.py               # Cosmological metric example
├── tests/
├── docs/
│   └── references.md         # All referenced work, tools, and prior art
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

See [`docs/references.md`](docs/references.md) for a full annotated bibliography of all prior work, tools, and mathematical references that informed this project.

---

## Acknowledgements

This project builds on SymPy's tensor and differential geometry modules, developed by the SymPy community. See the [SymPy paper](https://peerj.com/articles/cs-103/) for citation details.
