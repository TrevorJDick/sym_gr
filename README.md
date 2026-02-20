# sym_gr

**Symbolic General Relativity with SymPy**

A Python toolkit for symbolic tensor computation in General Relativity. Built for researchers, educators, and students who want a transparent, fully scriptable pipeline — from metric ansatz to field equations — using only standard scientific Python.

**License:** MIT

> **Note:** This repository was built with the assistance of AI tooling, but is being as carefully and transparently guided by human knowledge and creative thinking.

---

## Table of Contents

1. [What this is](#what-this-is)
2. [Three ways to use it](#three-ways-to-use-it)
3. [Installation](#installation)
4. [The Streamlit app](#the-streamlit-app)
5. [The Python API](#the-python-api)
6. [The command-line examples](#the-command-line-examples)
7. [Running the tests](#running-the-tests)
8. [Repository structure](#repository-structure)
9. [Index conventions](#index-conventions)
10. [References](#references)

---

## What this is

`sym_gr` computes GR tensor quantities symbolically. You provide a metric and a coordinate system; the library computes the Christoffel symbols, Riemann tensor, Ricci tensor, Ricci scalar, and Einstein tensor as exact SymPy expressions. You can then extract the vacuum or matter field equations, apply constraints, and export everything to LaTeX.

**No physical assumptions are built in.** The user specifies the metric, the coordinate system, and any constraints. The library applies what you tell it to apply.

**What it does not do:** numerically solve PDEs/ODEs (though the output equations can be fed into SciPy), or work with anything beyond the Levi-Civita connection and the standard EFE.

---

## Three ways to use it

| Mode | What it is | When to use it |
|------|-----------|----------------|
| **Streamlit app** | Interactive browser UI | Exploring, learning, exporting derivations |
| **Python API** | Import `core/` directly in your own scripts | Scripted computations, batch work, embedding in research code |
| **Command-line examples** | Runnable `.py` scripts in `examples/` | Seeing complete worked examples; a starting point for your own scripts |

The three modes are completely independent. The Streamlit app is not required to use the `core/` library, and the examples are not part of the app — they are standalone Python programs that demonstrate using the `core/` API from the terminal.

---

## Installation

Requires Python 3.11+.

```bash
git clone https://github.com/TrevorJDick/sym_gr.git
cd sym_gr
```

**Core library only** (tensor math, no UI):
```bash
pip install -e .
```

**With the Streamlit UI:**
```bash
pip install -e ".[ui]"
```

**Everything (UI + dev tools):**
```bash
pip install -e ".[all]"
```

### Dependencies

| Package | Role | Install group |
|---------|------|---------------|
| `sympy >= 1.13` | All symbolic computation | core |
| `numpy >= 1.26` | Numerical array support | core |
| `streamlit >= 1.35` | Interactive UI | `.[ui]` |
| `scipy >= 1.13` | Optional ODE solving | `.[numerical]` |
| `matplotlib >= 3.9` | Optional plotting | `.[plotting]` |
| `pytest >= 8.0` | Tests | `.[dev]` |

---

## The Streamlit app

The app is a browser-based interactive front-end. It lets you configure, compute, and export a full GR derivation without writing any Python.

**Launch:**
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

### App layout

The app is a single scrolling page with five sections, worked top to bottom:

#### Section 1 — EFE Setup
Configure the Einstein field equation before any computation. Set the cosmological constant Λ, the coupling constant κ, and the stress-energy tensor T_μν. A live preview renders the actual equation (e.g. `G_μν + Λ g_μν = κ T_μν`) as you type.

#### Section 2 — Coordinate System
Choose a coordinate preset (Cartesian, Spherical, Cylindrical, Schwarzschild, etc.) or enter custom coordinate names. The coordinates defined here propagate to every section below.

#### Section 3 — Stress-Energy Tensor T_μν
Enter T_μν in the coordinate basis. Two input modes stay in sync:
- **Expression tab** — type e.g. `diag(rho, p, p, p)` or a full `Matrix([...])`
- **Grid tab** — fill an n×n interactive symmetric grid cell by cell

#### Section 4 — Metric Ansatz
Enter the metric or build it step by step:
- Type directly in the expression tab, or use the grid
- **Fill with general ansatz** generates a fully symbolic metric `g_t_t, g_t_r, …` with one symbol per independent component
- **Ansatz step log** lets you apply physical constraints (e.g. "static metric → kill time-space cross terms", "spherical symmetry → diagonal angular block") one at a time, with Undo support and a full history log

#### Section 5 — Results
Expandable panels for each tensor. Computed on demand after pressing **Compute**:

| Panel | Content |
|-------|---------|
| Christoffel Γ^σ_μν | All non-zero components; optional step-by-step derivation showing each metric partial derivative term |
| Riemann R^ρ_σμν | Non-zero components (μ < ν only by antisymmetry) |
| Ricci R_μν | Symmetric, upper triangle shown |
| Ricci scalar R | Single expression |
| Einstein G_μν | Symmetric, upper triangle; + Bianchi identity verification button |
| Field equations | Generated on demand; optional verbose trace (RHS construction, dropped 0=0 components, index labels, Bianchi redundancy count) |

**Constraint steps** (inside the Field Equations panel): apply substitution rules to the field equations sequentially, with the same step-log interface as the metric ansatz. Each step's output becomes the next step's input. Undo rolls back one step at a time.

**Export:** download a complete `.tex` file (narrative LaTeX document with all computed tensors, derivation steps, and field equations) or a `.py` script that reproduces the computation using the `core/` API.

### Sidebar

- **Preset selector** — loads a complete spacetime configuration (coords, metric, EFE terms)
- **Reset to defaults** — restarts the current preset from scratch
- **Text size slider** — scales all text 75–200%

### Built-in presets

| Preset | Coords | Physics |
|--------|--------|---------|
| Minkowski | t, x, y, z | Flat spacetime; sanity check (all tensors zero) |
| Schwarzschild ansatz | t, r, θ, φ | Static spherically symmetric vacuum; step-based derivation |
| de Sitter | t, r, θ, φ | Positive cosmological constant; step-based derivation |
| Flat polar | t, r, θ, φ | Flat space in spherical coordinates |
| FLRW (flat) | t, r, θ, φ | Cosmological metric with scale factor `a(t)`; perfect fluid T_μν |
| Anti-de Sitter | t, z, x, y | Poincaré patch; Λ = −3/L² |
| Kerr | t, r, θ, φ | Rotating black hole, Boyer-Lindquist (slow) |

Presets marked "step-based" load a general symbolic ansatz and pre-populate the step log with the symmetry reduction steps so you can apply them one by one and see how the metric simplifies.

---

## The Python API

The `core/` package is a pure Python/SymPy library. Import it directly in your own scripts, notebooks, or research code — no Streamlit required.

### Building a spacetime

```python
from sympy import symbols, Function, sin, diag
from core.spacetime import Spacetime

t, r, theta, phi = symbols('t r theta phi')
A = Function('A')(r)
B = Function('B')(r)

coords = [t, r, theta, phi]
metric = diag(-A, B, r**2, r**2 * sin(theta)**2)

st = Spacetime(coords, metric)
```

`Spacetime` wraps the coordinates and metric and exposes lazy-cached tensor computations. Results are computed once and cached; subsequent calls return the cached value.

### Computing tensors

```python
# All tensors are SymPy ImmutableDenseNDimArray
christoffel = st.christoffel()       # Γ^σ_μν,  shape (n, n, n)
riemann      = st.riemann()          # R^ρ_σμν, shape (n, n, n, n)
ricci        = st.ricci()            # R_μν,    shape (n, n)
ricci_scalar = st.ricci_scalar()     # R,       scalar Expr
einstein     = st.einstein()         # G_μν,    shape (n, n)
```

Pass `simplified=True` to any call to run `sympy.simplify` on every component (slow for large metrics):

```python
einstein = st.einstein(simplified=True)
```

### Accessing individual components

```python
# Components are standard SymPy expressions
print(christoffel[0, 1, 1])      # Γ^t_rr
print(einstein[0, 0])            # G_tt
```

### Verifying the Bianchi identity

```python
# Returns a list of n expressions; all should be exactly zero
residuals = st.bianchi_check()
print(all(c == 0 for c in residuals))  # True for any consistent metric
```

### Extracting field equations

```python
from core.system import field_equations, field_equations_classified

# Simple form — returns a list of sympy.Eq
eqs = field_equations(st.einstein(), condition=0)

# Classified form — also returns (μ,ν) labels and dropped index pairs
result = field_equations_classified(st.einstein(), condition=0)
print(result.equations)   # list[Eq] of non-trivial equations
print(result.labels)      # list[(mu, nu)] — which component each equation is
print(result.dropped)     # list[(mu, nu)] — components dropped as 0 = 0
```

For matter-filled or Λ ≠ 0 cases, pass a per-component RHS:

```python
# rhs_tensor has shape (n, n); field_equations sets G_μν = rhs_tensor[μ,ν]
eqs = field_equations(st.einstein(), rhs_tensor=rhs)
```

### Applying constraints

```python
from core.constraints import apply_constraints
from sympy import Eq, Function, symbols, Symbol

r = symbols('r')
M = Symbol('M', positive=True)
A, B = Function('A'), Function('B')

constraints = [
    Eq(A(r), 1 - 2*M/r),
    Eq(B(r), 1 / (1 - 2*M/r)),
]

# apply_constraints handles substitution inside derivatives correctly
reduced = apply_constraints(eqs, constraints, auto_simplify=True)
print(len(reduced))  # 0 — all equations satisfied by Schwarzschild solution
```

`apply_constraints` correctly handles functions inside `Derivative` nodes (a common SymPy pitfall — see `core/constraints._function_subs`).

### Building a metric ansatz programmatically

```python
from core.ansatz import (
    generate_metric_symbols,
    apply_metric_constraints,
    diagonal_constraints,
    stationary_constraints,
)
from sympy import Eq

# General 4×4 symmetric metric with symbols g_t_t, g_t_r, ...
metric = generate_metric_symbols(coords)

# Zero all off-diagonal components
diag_eqs = diagonal_constraints(metric, coords)
metric = apply_metric_constraints(metric, diag_eqs, coords)

# Or zero time-space cross terms only (stationary condition)
stat_eqs = stationary_constraints(metric, coords)
metric = apply_metric_constraints(metric, stat_eqs, coords)

# Or apply any custom constraint
custom = [Eq(metric[2, 2], r**2)]   # fix g_θθ = r²
metric = apply_metric_constraints(metric, custom, coords)
```

### Pretty-printing and LaTeX

```python
from sympy import latex, pprint

pprint(st.einstein())             # pretty ASCII art to terminal
print(latex(st.christoffel()))    # LaTeX string
```

---

## The command-line examples

`examples/` contains **standalone Python scripts** that use the `core/` API directly. They are not connected to the Streamlit app — they run entirely in the terminal and are the best starting point for writing your own scripts.

### `examples/minkowski.py` — flat spacetime validation

**What it does:** constructs Minkowski spacetime in Cartesian coordinates, computes every tensor in the pipeline, asserts that all components are exactly zero (the correct result for flat spacetime), and prints each result. Used as a sanity check that the pipeline is working correctly.

**Runtime:** ~1 second.

```bash
python -m examples.minkowski
```

### `examples/schwarzschild.py` — vacuum field equation derivation

**What it does:** starts from the static spherically symmetric ansatz `ds² = -A(r)dt² + B(r)dr² + r²dΩ²`, computes the Einstein tensor, extracts the vacuum field equations `G_μν = 0`, displays the resulting ODE system, and then verifies that substituting the known Schwarzschild solution `A(r) = 1 - 2M/r`, `B(r) = 1/(1 - 2M/r)` reduces all equations to `0 = 0`.

**Runtime:** 30–90 seconds (symbolic differentiation over function-valued metric components is expensive).

```bash
python -m examples.schwarzschild
```

These scripts are a useful template: copy one, change the coordinates and metric, and you have a new computation.

---

## Running the tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

10 tests, all passing, runtime under 2 seconds. The test suite covers:

- **Minkowski** — all curvature tensors vanish identically
- **2-sphere** — Ricci scalar equals `2/r²` (matches the reference in `docs/references.md`)
- **Schwarzschild** — the known solution satisfies the vacuum field equations exactly

---

## Repository structure

```
sym_gr/
├── app.py                      ← Streamlit app entry point (UI only)
│
├── core/                       ← Pure tensor math library (no Streamlit)
│   ├── tensors.py              ← Low-level tensor functions (stateless, pure)
│   ├── spacetime.py            ← Spacetime class: holds coords + metric, lazy-caches tensors
│   ├── system.py               ← Field equation extraction: field_equations(), field_equations_classified()
│   ├── constraints.py          ← Constraint application: apply_constraints(), constrain_tensor()
│   ├── ansatz.py               ← Metric ansatz tools: generate_metric_symbols(), apply_metric_constraints()
│   ├── derivation.py           ← Step-by-step derivation data structures (for UI drill-down display)
│   └── __init__.py
│
├── ui/                         ← Streamlit UI components (all require Streamlit)
│   ├── parse.py                ← Parse user-typed strings into SymPy objects
│   ├── display.py              ← LaTeX rendering helpers for tensors and equations
│   ├── efe_config.py           ← EFE Setup section: Λ/κ/T_μν controls + live equation preview
│   ├── coord_config.py         ← Coordinate System section: presets + custom coord input
│   ├── metric_grid.py          ← Metric/T_μν interactive n×n grid widget
│   ├── ansatz_steps.py         ← Ansatz step log: sequential metric constraint UI
│   ├── constraint_steps.py     ← Field-eq constraint step log: sequential substitution UI
│   ├── drill_down.py           ← Step-by-step Christoffel / Riemann display panels
│   ├── export.py               ← LaTeX document and Python script builders
│   └── __init__.py
│
├── examples/                   ← Standalone Python scripts (no Streamlit, run from terminal)
│   ├── minkowski.py            ← Flat spacetime validation (~1s)
│   ├── schwarzschild.py        ← Vacuum field equation derivation + solution check (30–90s)
│   └── __init__.py
│
├── tests/
│   ├── test_tensors.py         ← 10 unit tests: Minkowski, 2-sphere, Schwarzschild
│   └── __init__.py
│
├── docs/
│   ├── presets.md              ← Derivation notes and physics references for each built-in preset
│   └── references.md           ← Annotated bibliography
│
└── pyproject.toml              ← Package metadata and optional dependency groups
```

### What lives where and why

**`core/`** — the computation engine. Everything here is pure SymPy: no Streamlit imports, no I/O. These modules can be imported in any Python environment.

- `tensors.py` — stateless pure functions. Takes coordinates + metric (or derived tensors) as arguments, returns tensors. No classes, no side effects.
- `spacetime.py` — the `Spacetime` class. Wraps coordinates and metric; calls `tensors.py` functions on demand and caches results. This is the main entry point for API users.
- `system.py` — turns the Einstein tensor into a list of `sympy.Eq` equations. Handles symmetry reduction (upper triangle only), RHS tensors (for matter/Λ), and optional index labelling.
- `constraints.py` — applies user-supplied `Eq` substitutions to equations or tensors. Handles the SymPy gotcha where `subs()` does not reach inside `Derivative` nodes — `_function_subs()` uses `replace()` + `doit()` instead.
- `ansatz.py` — builds a general symbolic metric (`g_t_t`, `g_t_r`, …) and provides helpers for common constraint patterns (diagonal, stationary).
- `derivation.py` — data structures for the step-by-step Christoffel and Riemann derivation (used only by the UI drill-down display; not needed for pure API use).

**`ui/`** — the Streamlit layer. All files here import `streamlit` and render widgets. They call into `core/` for computation and into each other for display. Do not import `ui/` outside a Streamlit context.

- `parse.py` — converts user-typed strings (e.g. `"diag(-A, B, r**2, r**2*sin(theta)**2)"`) into SymPy objects. Auto-declares unknown functions found in the string.
- `display.py` — renders tensors and equations as LaTeX via `st.latex()`. Handles rank-2, rank-3, and rank-4 tensors; zero-dimming; equation numbering.
- `ansatz_steps.py` / `constraint_steps.py` — the step-log UI components. Each step is a dict stored in session state; applying a step calls into `core/` and stores the result.
- `export.py` — pure functions (no Streamlit calls) that assemble the full LaTeX document and Python script from computed results. `render_export_buttons()` is the only Streamlit-dependent function.

**`examples/`** — self-contained scripts demonstrating the full `core/` API. They import nothing from `ui/` and do not require Streamlit. Run them from the command line with `python -m examples.<name>` or use them as a starting template.

**`tests/`** — pytest test suite. Tests are independent of both `ui/` and `examples/`.

---

## Index conventions

All conventions follow Carroll, *Spacetime and Geometry* (2004):

| Tensor | Symbol | Array indexing | Definition |
|--------|--------|---------------|------------|
| Christoffel | Γ^σ_μν | `[σ, μ, ν]` | `½ g^σρ (∂_μ g_νρ + ∂_ν g_μρ − ∂_ρ g_μν)` |
| Riemann | R^ρ_σμν | `[ρ, σ, μ, ν]` | `∂_μ Γ^ρ_νσ − ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ − Γ^ρ_νλ Γ^λ_μσ` |
| Ricci | R_μν | `[μ, ν]` | `R^ρ_μρν` (contract 1st and 3rd Riemann indices) |
| Einstein | G_μν | `[μ, ν]` | `R_μν − ½ R g_μν` |

Default signature: (−, +, +, +). This is not enforced — set the metric signs as needed.

---

## References

See [`docs/references.md`](docs/references.md) for an annotated bibliography and [`docs/presets.md`](docs/presets.md) for derivation notes and physics references for each built-in preset.

---

## Acknowledgements

This project builds on SymPy's tensor and differential geometry modules, developed by the SymPy community. See the [SymPy paper](https://peerj.com/articles/cs-103/) for citation details.
