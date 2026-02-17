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

## Preset: FLRW (flat)

**Physics:** The **Friedmann–Lemaître–Robertson–Walker** (FLRW) metric describes a
homogeneous, isotropic, expanding (or contracting) universe. This preset uses the
**flat spatial slice** (k = 0), which is consistent with current CMB observations
to high precision.

**Coordinates:** $(t, r, \theta, \phi)$ — comoving coordinates. Galaxies sit at
fixed $(r, \theta, \phi)$; the expansion is encoded in the scale factor $a(t)$.

**Metric:**
$$
g_{\mu\nu} = \text{diag}\!\bigl(-1,\; a(t)^2,\; a(t)^2 r^2,\; a(t)^2 r^2 \sin^2\theta\bigr)
$$

**Stress-energy tensor:**
The preset fills T_μν with a **perfect fluid** at rest in comoving coordinates:
$$
T_{\mu\nu} = \text{diag}\!\bigl(\rho,\; p\,a(t)^2,\; p\,a(t)^2 r^2,\; p\,a(t)^2 r^2\sin^2\theta\bigr)
$$
where $\rho$ is the energy density and $p$ is the pressure (both SymPy symbols —
assign values or an equation of state via custom constraints).

**What to expect:**
- Non-trivial Christoffel symbols involving $\dot{a}(t) \equiv da/dt$.
- The field equations $G_{\mu\nu} = \kappa T_{\mu\nu}$ yield (after simplification)
  two independent equations — the **Friedmann equations**:
  $$H^2 = \left(\frac{\dot{a}}{a}\right)^2 = \frac{\kappa \rho}{3}$$
  $$\frac{\ddot{a}}{a} = -\frac{\kappa}{6}(\rho + 3p)$$
- The Riemann tensor is non-trivial but highly symmetric (spatial isotropy).

**Applying constraints:**
- For a **matter-dominated** universe: `p = 0` → $a(t) \propto t^{2/3}$.
- For a **radiation-dominated** universe: `p = rho/3` → $a(t) \propto t^{1/2}$.
- For **de Sitter expansion**: set `T_str = 0` and `lambda_str = Lambda` → $a(t) \propto e^{Ht}$.

**Computation time:** Similar to Schwarzschild (~60–90 s) because $a(t)$ is an
undefined function and all derivatives must be computed symbolically.

**References:**
- Friedmann, A. (1922). *Über die Krümmung des Raumes.* Z. Phys. 10, 377–386.
  First derivation of the expanding universe equations from GR.
- Friedmann, A. (1924). *Über die Möglichkeit einer Welt mit konstanter negativer Krümmung des Raumes.* Z. Phys. 21, 326–332.
- Lemaître, G. (1927). *Un Univers homogène de masse constante et de rayon croissant.* Ann. Soc. Sci. Bruxelles A47, 49–59.
- Robertson, H.P. (1935). *Kinematics and World-Structure.* ApJ 82, 284.
- Walker, A.G. (1936). *On Milne's Theory of World-Structure.* Proc. London Math. Soc. s2-42, 90–127.
- Carroll §8.2–8.3 for the standard pedagogical derivation of the Friedmann equations from the EFE.
- MTW §27 for the full cosmological application.

---

## Preset: Anti-de Sitter

**Physics:** The **Anti-de Sitter** (AdS) spacetime is the maximally symmetric vacuum
solution of the Einstein equations with a **negative cosmological constant** $\Lambda < 0$.
It is the GR analogue of a space with constant negative curvature.  The most famous
application is the **AdS/CFT correspondence** (Maldacena 1997): a gravitational theory
on AdS is dual to a conformal field theory living on its boundary.

This preset uses the **Poincaré patch** — the half-space $z > 0$ with coordinates
$(t, z, x, y)$. Here $z$ is the holographic direction; the conformal boundary
sits at $z = 0$ and the AdS "interior" at $z \to \infty$.

**Coordinates:** $(t, z, x, y)$ — Poincaré patch of AdS₄.

**Metric:**
$$
g_{\mu\nu} = \frac{L^2}{z^2}\,\text{diag}(-1,\; 1,\; 1,\; 1)
$$
where $L$ is the **AdS radius** (a free parameter; larger $L$ = weaker curvature).

**EFE setup:** $\Lambda = -3/L^2$ (negative, as required for AdS).

**What to expect:**
- The metric is conformally flat: $g_{\mu\nu} = (L/z)^2\,\eta_{\mu\nu}$.
- Einstein tensor satisfies $G_{\mu\nu} = (3/L^2)\,g_{\mu\nu}$, so the field
  equation $G_{\mu\nu} + \Lambda\,g_{\mu\nu} = G_{\mu\nu} - (3/L^2)\,g_{\mu\nu} = 0$
  is satisfied identically.
- Ricci scalar: $R = -12/L^2$ (constant, negative — the hallmark of AdS).
- No coordinate singularity or horizon (unlike de Sitter).

**Comparison with de Sitter:**

| Property | de Sitter | Anti-de Sitter |
|----------|-----------|----------------|
| $\Lambda$ | $> 0$ | $< 0$ |
| Spatial sections | positively curved or flat | negatively curved |
| Horizon | yes (at $r = \sqrt{3/\Lambda}$) | no |
| Relevant to | inflationary cosmology | AdS/CFT, holography |

**Computation time:** Fast (~5–10 s). The metric is conformally flat so all components
are rational functions of $z$ only — no unknown functions, no angular complexity.

**References:**
- Maldacena, J. (1997). *The large N limit of superconformal field theories and
  supergravity.* Int. J. Theor. Phys. 38, 1113.
  [arXiv:hep-th/9711200](https://arxiv.org/abs/hep-th/9711200)
  — The AdS/CFT conjecture; the Poincaré patch metric appears throughout.
- Aharony, O. et al. (1999). *Large N Field Theories, String Theory and Gravity.*
  Phys. Rept. 323, 183–386. [arXiv:hep-th/9905221](https://arxiv.org/abs/hep-th/9905221)
  — Comprehensive review of AdS/CFT; §1 defines the Poincaré patch coordinates.
- Carroll §3.9 and §8.1 for the AdS solution and cosmological constant.
- Hawking, S.W. & Ellis, G.F.R. (1973). *The Large Scale Structure of Space-Time.*
  Cambridge. §5.2 for the de Sitter and Anti-de Sitter solutions.

---

## Preset: Kerr

**Physics:** The **Kerr metric** (1963) is the unique vacuum solution of the Einstein
equations describing the spacetime outside a rotating, uncharged, axially-symmetric
mass. It is the physically realistic black hole metric — astrophysical black holes
are expected to be well-described by Kerr (or Kerr-Newman with charge).

**Coordinates:** $(t, r, \theta, \phi)$ — **Boyer–Lindquist coordinates** (1967).
These are the natural generalization of Schwarzschild coordinates to the rotating case.

**Parameters:**
- $M$ — mass (in geometric units $G = c = 1$)
- $a$ — **specific angular momentum** $J/M$ (spin parameter; $|a| \leq M$)
  - $a = 0$: reduces to Schwarzschild
  - $a = M$: **extremal Kerr** (maximum possible spin)

**Metric:**

Define $\Sigma \equiv r^2 + a^2\cos^2\theta$ and $\Delta \equiv r^2 - 2Mr + a^2$. Then:
$$
g_{\mu\nu} = \begin{pmatrix}
  -(1 - 2Mr/\Sigma) & 0 & 0 & -2Mar\sin^2\theta/\Sigma \\
  0 & \Sigma/\Delta & 0 & 0 \\
  0 & 0 & \Sigma & 0 \\
  -2Mar\sin^2\theta/\Sigma & 0 & 0 & (r^2+a^2+2Ma^2r\sin^2\theta/\Sigma)\sin^2\theta
\end{pmatrix}
$$

**Key features:**
- **Off-diagonal:** $g_{t\phi} = g_{\phi t} \neq 0$ — the metric mixes time and azimuthal
  directions, reflecting **frame dragging** (the Lense-Thirring effect). A gyroscope
  near a Kerr black hole precesses even when stationary.
- **Event horizons:** at $r_\pm = M \pm \sqrt{M^2 - a^2}$ (outer/inner horizon).
  The outer horizon $r_+ = M + \sqrt{M^2-a^2}$ replaces Schwarzschild's $r = 2M$.
- **Ergosphere:** the region $r_+ < r < r_\text{erg}$ where $r_\text{erg} = M + \sqrt{M^2 - a^2\cos^2\theta}$.
  Inside the ergosphere, no observer can remain stationary (even at the speed of light).
  Energy can be extracted from this region via the **Penrose process**.
- **Ring singularity** at $\Sigma = 0$, i.e. $r = 0,\ \theta = \pi/2$ — a ring of
  radius $a$ in the equatorial plane (not a point as in Schwarzschild).

**What to expect:**
- $G_{\mu\nu} = 0$ — it is a vacuum solution (all components identically zero).
- Computation is **very slow** (10–20+ minutes for the full pipeline). The metric
  components involve complex rational expressions in $r$ and $\theta$, and SymPy
  must differentiate through them symbolically without simplification.
  Tick **Simplify results** for cleaner output, but this makes it even slower.
- Use Christoffel step-by-step mode cautiously — there are 40 non-zero symbols.
- **Recommended workflow:** Load the preset, compute Christoffel symbols only,
  inspect a few components, then proceed to Riemann/Einstein when patience allows.

**Applying constraints:**
To specialize to Schwarzschild: enter `a = 0` in the Constraints box after
generating field equations. All off-diagonal terms will vanish and the metric
reduces to the standard Schwarzschild form.

**References:**
- Kerr, R.P. (1963). *Gravitational field of a spinning mass as an example of
  algebraically special metrics.* Phys. Rev. Lett. 11, 237.
  The original derivation — one of the most important exact solutions in GR.
- Boyer, R.H. & Lindquist, R.W. (1967). *Maximal analytic extension of the Kerr metric.*
  J. Math. Phys. 8, 265.
  Introduces the Boyer–Lindquist coordinate form used here.
- Chandrasekhar, S. (1983). *The Mathematical Theory of Black Holes.*
  Oxford. Part VI covers the Kerr metric in exhaustive component detail.
- Carroll §7.4 for the Boyer–Lindquist metric, horizons, and ergosphere.
- MTW §33 for the Kerr geometry and its physical interpretation.
- Visser, M. (2007). *The Kerr spacetime: A brief introduction.*
  [arXiv:0706.0622](https://arxiv.org/abs/0706.0622) — concise modern summary.

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
