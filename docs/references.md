# References and Prior Art

This document catalogs the work, tools, papers, and resources that informed the design of `sym_gr`. It is intended to give users and contributors a clear picture of the intellectual and technical foundations of this project, and to credit the researchers and developers whose work made this possible.

---

## Mathematical Foundations

### General Relativity and Tensor Calculus

**Einstein, A. (1916)**
*Die Grundlage der allgemeinen Relativitätstheorie*
Annalen der Physik, 354(7), 769–822.
The original paper presenting the Einstein field equations `G_μν = 8πG T_μν`.

**Misner, C.W., Thorne, K.S., Wheeler, J.A. (1973)**
*Gravitation*
W.H. Freeman. ISBN: 978-0716703341.
The standard graduate reference. Covers the Riemann tensor, Bianchi identities, Christoffel symbols, and derivation of the Schwarzschild and other metrics in full component form. The conventions used in this project (signature `(-,+,+,+)`, index placement) follow MTW unless noted otherwise.

**Wald, R.M. (1984)**
*General Relativity*
University of Chicago Press. ISBN: 978-0226870335.
Rigorous treatment of the differential geometry underlying GR. Particularly relevant for the abstract index notation approach used in `sym_gr`'s equation entry API.

**Carroll, S. (2004)**
*Spacetime and Geometry: An Introduction to General Relativity*
Addison-Wesley. ISBN: 978-0805387322.
Accessible graduate text. Chapters 3–4 cover the geometric objects this toolkit computes. Freely available lecture notes version: https://arxiv.org/abs/gr-qc/9712019

---

## Derivations Directly Relevant to the Milestones

### Minkowski Metric (Milestone 1)

**Physics StackExchange: "Minkowski metric derivation"**
https://physics.stackexchange.com/questions/803797/minkowski-metric-derivation
Discussion of how the Minkowski metric arises from imposing flatness (`R^σ_μνρ = 0`) on a general metric ansatz. This is the direct motivation for Milestone 1: demonstrating that the `sym_gr` pipeline recovers `diag(-1, 1, 1, 1)` as the unique (up to gauge) solution to the vacuum flat-space equations.

### Schwarzschild Metric (Milestone 2)

**Schwarzschild, K. (1916)**
*Über das Gravitationsfeld eines Massenpunktes nach der Einsteinschen Theorie*
Sitzungsberichte der Königlich Preußischen Akademie der Wissenschaften, 189–196.
English translation: https://arxiv.org/abs/physics/9905030
The original derivation of the exterior vacuum metric for a spherically symmetric mass. Milestone 2 reproduces this derivation symbolically: inputting a static spherically symmetric ansatz, applying `G_μν = 0`, and solving the resulting ODE system.

**Birkhoff's Theorem**
Any spherically symmetric vacuum solution to the Einstein equations is static and isometric to Schwarzschild. This theorem is the theoretical guarantee that Milestone 2 has a unique answer, making it a clean validation target.

---

## Key Technical References

### Riemannian Geometry with SymPy Tensor Module

**Jannik (2023)**
*Curvature and Derivative on Riemannian Manifolds with SymPy Tensor*
https://jd11111.github.io/2023/06/28/RieGeoTens.html

The most directly applicable technical reference for this project's implementation. Demonstrates:
- Using `sympy.tensor.tensor` (`TensorIndexType`, `TensorHead`, `TensorSymmetry`, `PartialDerivative`) for abstract index notation
- Constructing covariant derivatives manually by expanding Christoffel contraction terms
- Using `replace_with_arrays()` to evaluate abstract tensor expressions to component arrays
- A `symmetrizer()` helper function for (anti)-symmetrization via permutations
- Derivation of Christoffel symbols, Ricci tensor, and scalar curvature for the 2-sphere (`K = 2/r²`)

This blog post is important because it demonstrates the exact gap `sym_gr` addresses: `sympy.tensor.tensor` provides the abstract algebra machinery, but covariant derivatives and Bianchi-type identities must be constructed explicitly — which is precisely what `sym_gr` does, and why user-specified constraints are essential rather than hardcoded.

### SymPy Differential Geometry Module

**SymPy Documentation: `sympy.diffgeom`**
https://docs.sympy.org/latest/modules/diffgeom.html

Provides the coordinate-based GR computation functions used in the core pipeline:
- `metric_to_Christoffel_1st(g)` — `Γ_{abc}` (lowered, 1st kind)
- `metric_to_Christoffel_2nd(g)` — `Γ^a_{bc}` (2nd kind, used in this project)
- `metric_to_Riemann_components(g)` — `R^a_{bcd}`
- `metric_to_Ricci_components(g)` — `R_{ab}`

**Known limitation:** The Einstein tensor `G_μν = R_μν - ½ R g_μν` and Ricci scalar are not provided and are computed manually in `sym_gr/core/tensors.py`. Results with function-valued metric components (e.g. `f(r)`) can require explicit `simplify()` passes. See SymPy issue [#11799](https://github.com/sympy/sympy/issues/11799).

### SymPy Abstract Tensor Module

**SymPy Documentation: `sympy.tensor.tensor`**
https://docs.sympy.org/latest/modules/tensor/tensor.html

Abstract index notation for tensors. Provides:
- `TensorIndexType` — defines an index type with optional metric for raising/lowering
- `TensorHead` — names a tensor with given symmetry
- `TensorSymmetry.riemann()` — the pair-exchange symmetry of the Riemann tensor
- `canon_bp()` — Butler-Portugal canonicalization algorithm
- `replace_with_arrays()` — evaluate abstract expressions to component arrays

**Known limitation:** Only *monoterm* symmetries are enforceable. The first Bianchi identity `R_{abcd} + R_{acdb} + R_{adbc} = 0` is a multiterm symmetry and cannot be enforced automatically. This is why `sym_gr` requires the user to enter Bianchi identities explicitly as constraints — no hidden enforcement.

### SymPy N-Dimensional Array Module

**SymPy Documentation: `sympy.tensor.array`**
https://docs.sympy.org/latest/modules/tensor/array.html

Used for component-level storage and manipulation of tensors:
- `ImmutableDenseNDimArray` — the primary container for metric and derived tensors
- `tensorproduct(A, B)` — outer product
- `tensorcontraction(A, (i, j))` — contraction over index pair
- `permutedims(A, perm)` — index permutation

### SymPy LaTeX Parser

**SymPy Documentation: `sympy.parsing.latex`**
https://docs.sympy.org/latest/modules/parsing.html

Parses a subset of mathematical LaTeX into SymPy expressions. Used for scalar expression input in the UI.

**Critical limitation for this project:** Does not handle tensor index notation. `R_{\mu\nu}` is not parsed as a rank-2 tensor — subscripts become part of symbol names. This is why `sym_gr` uses LaTeX only for *rendered display output* (`sympy.latex()` → `st.latex()`), and all computation is via the SymPy Python API directly.

---

## Existing Projects Surveyed

These projects were evaluated during the design of `sym_gr`. They are not dependencies, but informed what this project should and should not do.

### OGRePy

**Repository:** https://github.com/bshoshany/OGRePy
**Paper:** https://arxiv.org/abs/2409.03803
**Published:** Journal of Open Research Software, 2025.

Python port of the Mathematica OGRe package. Object-oriented GR tensor toolkit built on SymPy. Computes Christoffel symbols, Riemann, Ricci, Einstein tensor, geodesics. Primary interface is Jupyter notebooks. Also provides a browser-based JupyterLite instance.

*Why `sym_gr` is different:* OGRePy is Jupyter-first and does not expose a constraint/equation pipeline. `sym_gr` targets Streamlit and gives the user explicit control over which equations to apply.

### EinsteinPy

**Repository:** https://github.com/einsteinpy/einsteinpy
**Paper:** https://arxiv.org/abs/2005.11288

Combined symbolic and numerical GR. Symbolic: Christoffel, Riemann, Ricci, Weyl, Einstein tensors. Numerical: geodesics in Schwarzschild, Kerr, Kerr-Newman spacetimes.

*Status:* Last major release 2021; reduced activity since.
*Why `sym_gr` is different:* EinsteinPy focuses on known metrics and geodesics. `sym_gr` focuses on deriving metrics from field equations and constraints.

### GTRPy

**Repository:** https://github.com/camarman/GTRPy

Desktop GUI application (Linux/macOS) for GR tensor calculations. No coding required. Metric entered via form fields. Computes Christoffel, Riemann, Ricci, Einstein tensors using SymPy.

*Why `sym_gr` is different:* GTRPy is a no-code GUI with no equation/constraint entry. `sym_gr` is a scriptable API first, with a Streamlit UI layer on top.

### Cadabra2

**Website:** https://cadabra.science
**Papers:** https://arxiv.org/abs/2210.00005, https://arxiv.org/abs/1912.08839

A dedicated computer algebra system for tensor field theory, not a Python library. LaTeX-syntax input, Python scripting layer. Best available tool for Bianchi identity derivations and gravitational wave perturbation theory.

*Why `sym_gr` is different:* Cadabra2 is a full separate CAS requiring its own installation. `sym_gr` is pure Python/SymPy, installable via pip.

### SageManifolds (within SageMath)

**Website:** https://sagemanifolds.obspm.fr
**Paper:** https://arxiv.org/abs/1804.07346

The most complete differential geometry framework available in open-source Python. Full symbolic and numerical support, explicit Bianchi identity examples in the documentation, Schwarzschild and Kerr worked examples. Requires a full SageMath installation.

*Why `sym_gr` is different:* SageMath is a heavyweight dependency. `sym_gr` targets researchers who want `pip install sym_gr` and a standard Python environment.

### Pytearcat

**Repository:** https://github.com/pytearcat/pytearcat
**Paper:** https://www.sciencedirect.com/science/article/abs/pii/S221313372200018X (2022)

General tensor algebra calculator for GR. SymPy-backed, Jupyter notebook interface, LaTeX-rendered output. Computes Christoffel, Riemann, Ricci, Einstein tensors.

### GraviPy

**Repository:** https://github.com/wojciechczaja/GraviPy

Lightweight tensor calculus package for GR on top of SymPy. Teaching and quick-prototype use. Computes Christoffel symbols, Ricci tensor, Einstein tensor.

### spacetimeengine

**Repository:** https://github.com/spacetimeengineer/spacetimeengine

SymPy-based utility for analyzing metric solutions to the Einstein field equations. Useful for cross-referencing published metric solutions. Includes a library of known metrics.

### NRPyLaTeX

**Repository:** https://github.com/zachetienne/nrpylatex
**Paper:** https://arxiv.org/abs/2111.05861

LaTeX-to-SymPy parser that handles GR tensor notation including Einstein summation, Christoffel symbols, covariant derivatives. Output follows NRPy+ naming conventions and feeds into NRPy+'s C/C++ code generation pipeline.

*Relevance:* The only serious LaTeX→SymPy parser that handles tensor indices. Not used in `sym_gr` because it imposes NRPy+ naming conventions on output objects, but worth knowing for users who want to generate numerical code.

---

## SymPy Core References

**Meurer, A. et al. (2017)**
*SymPy: symbolic computing in Python*
PeerJ Computer Science 3:e103. https://doi.org/10.7717/peerj-cs.103
The primary citation for SymPy. All users of `sym_gr` who publish results should cite this paper.

**SymPy Development Team**
https://www.sympy.org

---

## UI and Rendering

**Streamlit Documentation**
https://docs.streamlit.io

Used for the interactive interface. `st.latex()` renders SymPy expressions via KaTeX. The reactive execution model (script reruns on input change) is well-suited to exploratory symbolic computation.

**KaTeX**
https://katex.org

The LaTeX rendering engine used by Streamlit. Covers all GR-relevant notation: Greek indices, tensor notation, `\nabla`, `\partial`, `\Gamma`, `\mathcal{R}`, align environments.

---

## Conventions Used in This Project

| Convention | Choice | Reference |
|------------|--------|-----------|
| Metric signature | `(-, +, +, +)` | MTW, Carroll |
| Index notation | Latin for abstract, Greek for spacetime | Standard GR |
| Riemann tensor definition | `R^ρ_{σμν} = ∂_μΓ^ρ_{νσ} - ∂_νΓ^ρ_{μσ} + ...` | MTW §11.3 |
| Ricci tensor | `R_{μν} = R^ρ_{μρν}` (first and third index contraction) | Carroll §3.4 |
| Einstein tensor | `G_{μν} = R_{μν} - ½ R g_{μν}` | Standard |
| Units | `G = c = 1` (geometrized) unless noted | Common in GR literature |
