# Preset Spacetimes — Reference

This document describes each built-in preset in sym_gr: the physics behind it,
the conventions used, and what to expect from the computation.

---

## Conventions used throughout

### Signature

All presets use the **mostly-plus** convention: **(−, +, +, +)**.

This means the metric of flat spacetime is $\text{diag}(-1, +1, +1, +1)$. The
time direction carries a negative sign. This is standard in GR textbooks
(Carroll, Wald, Misner–Thorne–Wheeler).

> **Note:** Some particle physics texts use the opposite convention (+, −, −, −),
> called mostly-minus. sym_gr lets you choose via the Signature selector in
> Section 2, but the presets are all set up for mostly-plus.

### Index placement

sym_gr follows Carroll's conventions:

| Tensor | Notation | Definition |
|--------|----------|------------|
| Christoffel | $\Gamma^\sigma{}_{\mu\nu}$ | $\frac{1}{2} g^{\sigma\rho}(\partial_\mu g_{\nu\rho} + \partial_\nu g_{\mu\rho} - \partial_\rho g_{\mu\nu})$ |
| Riemann | $R^\rho{}_{\sigma\mu\nu}$ | $\partial_\mu \Gamma^\rho_{\nu\sigma} - \partial_\nu \Gamma^\rho_{\mu\sigma} + \Gamma^\rho_{\mu\lambda}\Gamma^\lambda_{\nu\sigma} - \Gamma^\rho_{\nu\lambda}\Gamma^\lambda_{\mu\sigma}$ |
| Ricci | $R_{\mu\nu}$ | $R^\rho{}_{\mu\rho\nu}$ (contract index 1 with index 3 of Riemann) |
| Einstein | $G_{\mu\nu}$ | $R_{\mu\nu} - \frac{1}{2} R\, g_{\mu\nu}$ |

### κ (coupling constant)

The default κ is `8*pi*G` — this is the geometric-units form (c = 1).
In SI units: $\kappa = 8\pi G / c^4 \approx 2.07 \times 10^{-43}\ \text{s}^2/(\text{kg}\cdot\text{m})$.
Use the **κ calculator** (Section 1 expander) to convert between unit systems.

---

## Preset: Minkowski

**Physics:** Flat spacetime — the arena of Special Relativity and the
zero-curvature limit of GR.

**Coordinates:** $(t, x, y, z)$ — standard Cartesian.

**Metric:**
$$
g_{\mu\nu} = \text{diag}(-1, 1, 1, 1)
$$

**What to expect:**
- All Christoffel symbols vanish (the coordinate basis is geodesic).
- Riemann tensor = 0 (flat spacetime by definition).
- Einstein tensor $G_{\mu\nu} = 0$.
- Field equations are satisfied trivially: $0 = 0$.

**Use case:**
Sanity check. Also useful as a starting point to verify that the computation
pipeline works before moving to a curved spacetime.

---

## Preset: Schwarzschild ansatz

**Physics:** The unique spherically-symmetric vacuum solution of GR, describing
the exterior gravitational field of any non-rotating, spherically-symmetric
mass (a star, black hole, etc.). Named after Karl Schwarzschild (1916).

**Coordinates:** $(t, r, \theta, \phi)$ — Schwarzschild (curvature) coordinates.

**Metric ansatz:**
$$
g_{\mu\nu} = \text{diag}\!\bigl(-A(r),\; B(r),\; r^2,\; r^2 \sin^2\theta\bigr)
$$

Here $A(r)$ and $B(r)$ are unknown functions of $r$ only — the preset does **not**
assume the Schwarzschild solution; it lets you derive it.

**What to expect:**
- Non-trivial Christoffel symbols and Riemann components (all in terms of
  $A(r)$, $B(r)$, and their derivatives).
- Two independent field equations (vacuum: $G_{\mu\nu} = 0$), relating
  $A$, $B$, and their $r$-derivatives.
- Solving those equations (with asymptotic flatness $A, B \to 1$ as $r \to \infty$)
  yields the **Schwarzschild solution**:
  $$A(r) = 1 - \frac{2M}{r}, \qquad B(r) = \frac{1}{1 - 2M/r}$$
  where $M$ is the mass (in geometric units).

**Applying constraints:**
In the "Apply constraints" box, enter:
```
A(r) = 1 - 2*M/r
B(r) = 1/(1 - 2*M/r)
```
Tick **Simplify results** first, then generate field equations and apply constraints —
the residuals should reduce to $0 = 0$.

**Key features:**
- $r = 2M$ is the **Schwarzschild radius** (event horizon in vacuum).
- The computation can take 60–90 s for the full pipeline because SymPy must
  differentiate $A(r)$ and $B(r)$ symbolically through the 4D metric.

---

## Preset: de Sitter

**Physics:** The maximally-symmetric solution of the Einstein equations with a
**positive cosmological constant** $\Lambda > 0$ and no matter ($T_{\mu\nu} = 0$).
Describes an exponentially expanding universe — relevant for inflationary
cosmology and the accelerating expansion of the present universe.

**Coordinates:** $(t, r, \theta, \phi)$ — static patch coordinates.

**Metric:**
$$
g_{\mu\nu} = \text{diag}\!\left(-1,\; \left(1 - \frac{\Lambda r^2}{3}\right)^{-1},\; r^2,\; r^2 \sin^2\theta\right)
$$

Here $\Lambda$ is the cosmological constant (a symbol; set a numerical value in
Section 1 if desired).

**What to expect:**
- The metric has a coordinate singularity at $r = \sqrt{3/\Lambda}$, the
  **de Sitter horizon** (analogous to the Schwarzschild horizon).
- The Einstein tensor satisfies $G_{\mu\nu} = -\Lambda g_{\mu\nu}$ — this is
  the defining property of the de Sitter solution.
- Field equations: $G_{\mu\nu} + \Lambda g_{\mu\nu} = 0$, all satisfied identically.
- The Ricci scalar is constant: $R = 4\Lambda$.

**EFE setup:** Λ is set to `Lambda` (a symbol). κ remains `8*pi*G`. T_μν = 0.

---

## Preset: Flat polar

**Physics:** Ordinary flat (Minkowski) space expressed in **spherical coordinates**
$(t, r, \theta, \phi)$ rather than Cartesian. No curvature — this is purely a
coordinate effect.

**Coordinates:** $(t, r, \theta, \phi)$.

**Metric:**
$$
g_{\mu\nu} = \text{diag}(-1,\; 1,\; r^2,\; r^2 \sin^2\theta)
$$

**What to expect:**
- Non-trivial Christoffel symbols even though spacetime is flat — these arise
  from the curvature of the coordinate lines, not from gravitational curvature.
- Riemann tensor = 0 (the space is flat).
- Einstein tensor = 0.

**Use case:**
- Demonstrates the distinction between **coordinate singularities** (the metric
  is degenerate at $r = 0$ and $\theta = 0, \pi$) and **physical curvature**.
- Good introduction to non-Cartesian coordinate computation before tackling
  the Schwarzschild ansatz.
- The non-zero Christoffel symbols here are the familiar **connection
  coefficients** of spherical coordinates that appear in vector calculus
  (e.g., in the expression for the Laplacian in spherical coordinates).

---

## Adding your own spacetime

To go beyond the presets:

1. **Choose coordinates** in Section 2 (or type custom names).
2. **Enter the metric** in Section 3 — either as a `diag(...)` expression or
   using the Grid tab. Unknown functions like `f(r)` are declared automatically.
3. **Set EFE parameters** in Section 1: choose Λ, κ, and T_μν.
4. Click **Compute**.

### Useful metric expressions

| Spacetime | Metric string |
|-----------|---------------|
| FLRW (flat) | `diag(-1, a(t)**2, a(t)**2*r**2, a(t)**2*r**2*sin(theta)**2)` |
| Kerr (ansatz) | Full off-diagonal — enter via Grid tab |
| 2D sphere | `diag(R**2, R**2*sin(theta)**2)` with coords `theta, phi` |
| Rindler | `diag(-g**2*x**2, 1, 1, 1)` with coords `t, x, y, z` |

### Symbol names

SymPy parses standard mathematical names:
- Greek: `theta`, `phi`, `Lambda`, `rho`, `kappa`, `alpha`, `beta`, `sigma`
- Functions: `sin`, `cos`, `tan`, `exp`, `log`, `sqrt`
- Unknown functions: any name followed by `(...)`, e.g. `f(r)`, `A(t)`, `N(r)`
- Constants: `pi`, `E` (Euler's number), `G`, `c` (treated as symbols unless
  numerical values are applied via the κ calculator)
