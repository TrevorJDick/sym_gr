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

```math
g_{\mu\nu} = \text{diag}(-1, 1, 1, 1)
```

**What to expect:**
- All Christoffel symbols vanish (the coordinate basis is geodesic).
- Riemann tensor = 0 (flat spacetime by definition).
- Einstein tensor $G_{\mu\nu} = 0$.
- Field equations are satisfied trivially: $0 = 0$.

**How the metric is derived:**
The Minkowski metric is not derived from an ansatz — it is the *definition* of flat
spacetime in orthonormal Cartesian coordinates. The form $\text{diag}(-1,1,1,1)$ is
the unique (up to signature convention) solution to $R^\rho{}_{\sigma\mu\nu} = 0$
in coordinates where all metric components are constant. The negative sign on the
time component follows from the mostly-plus signature choice.

**Use case:**
Sanity check. Also useful as a starting point to verify that the computation
pipeline works before moving to a curved spacetime.

**References:**
- Minkowski, H. (1908). *Raum und Zeit.* Address to the 80th Assembly of German
  Natural Scientists and Physicians, Cologne. Reprinted in Lorentz, Einstein,
  Minkowski & Weyl (1952). *The Principle of Relativity.* Dover. — the original
  four-dimensional spacetime formulation.
- Einstein, A. (1905). *Zur Elektrodynamik bewegter Körper.* Ann. Phys. 322(10),
  891–921. — special relativity, whose arena Minkowski space is.
- Carroll §1 (Special Relativity and Flat Spacetime) for sign conventions and
  the Minkowski metric in various coordinate systems.
- MTW §6 for flat spacetime, the equivalence principle, and locally inertial
  frames.

---

## Preset: Schwarzschild ansatz

**Physics:** The unique spherically-symmetric vacuum solution of GR, describing
the exterior gravitational field of any non-rotating, spherically-symmetric
mass (a star, black hole, etc.). Named after Karl Schwarzschild (1916).

**Coordinates:** $(t, r, \theta, \phi)$ — Schwarzschild (curvature) coordinates.

**Metric ansatz:**

```math
g_{\mu\nu} = \text{diag}(-A(r),\; B(r),\; r^2,\; r^2 \sin^2\theta)
```

Here $A(r)$ and $B(r)$ are unknown functions of $r$ only — the preset does **not**
assume the Schwarzschild solution; it lets you derive it.

**What to expect:**
- Non-trivial Christoffel symbols and Riemann components (all in terms of
  $A(r)$, $B(r)$, and their derivatives).
- Two independent field equations (vacuum: $G_{\mu\nu} = 0$), relating
  $A$, $B$, and their $r$-derivatives.
- Solving those equations (with asymptotic flatness $A, B \to 1$ as $r \to \infty$)
  yields the **Schwarzschild solution**:

```math
A(r) = 1 - \frac{2M}{r}, \qquad B(r) = \frac{1}{1 - 2M/r}
```

where $M$ is the mass (in geometric units).

**How the ansatz is derived — step by step:**

This preset loads a *general ansatz* and pre-populates five derivation steps,
mirroring the textbook reduction from the most general metric to the Schwarzschild
form. The steps are visible and editable in the **Ansatz steps** panel of the app.

Start: a fully general symmetric 4×4 metric with 10 independent component symbols
$g_{tt}, g_{tr}, g_{t\theta}, g_{t\phi}, g_{rr}, \ldots$

**Step 1 — Static metric** (time-reversal symmetry $t \to -t$):
A static spacetime is unchanged under time reversal. Because $dt$ is odd under
$t \to -t$ while $dr, d\theta, d\phi$ are even, any cross term $g_{ti}\,dt\,dx^i$
would change sign — violating the symmetry. Therefore:
$$g_{tr} = g_{t\theta} = g_{t\phi} = 0$$
This removes three off-diagonal components, leaving seven.

**Step 2 — Spherical symmetry** (no radial-angular or angle-angle mixing):
Spherical symmetry ($SO(3)$ acting on the angular coordinates) forbids any
coupling between the $r$-direction and the angular directions, and between
different angular directions. Therefore:
$$g_{r\theta} = g_{r\phi} = g_{\theta\phi} = 0$$
This leaves four diagonal components: $g_{tt}(r), g_{rr}(r), g_{\theta\theta}(r), g_{\phi\phi}(r,\theta)$.

**Step 3 — SO(3) invariance** (angular block must be a round sphere):
The restriction of the metric to a surface of constant $t$ and $r$ must be
proportional to the round-sphere metric $d\theta^2 + \sin^2\theta\,d\phi^2$.
Therefore:
$$g_{\phi\phi} = \sin^2\theta \cdot g_{\theta\theta}$$
This reduces the two free angular components to one: $g_{\theta\theta}(r)$.

**Step 4 — Coordinate choice** (define $r$ as the areal radius):
We are still free to relabel the radial coordinate. We choose $r$ so that the
area of a $t = \text{const},\, r = \text{const}$ 2-sphere is $4\pi r^2$,
which means:
$$g_{\theta\theta} = r^2$$
This is a gauge choice, not a physical assumption. It fixes the remaining
angular component and leaves two free functions $g_{tt}(r)$ and $g_{rr}(r)$.

**Step 5 — Rename free functions:**
For clarity, introduce named functions:
$$g_{tt} = -A(r), \qquad g_{rr} = B(r)$$

**Result:**

```math
g_{\mu\nu} = \text{diag}(-A(r),\; B(r),\; r^2,\; r^2\sin^2\theta)
```

Solving the vacuum field equations $G_{\mu\nu} = 0$ for $A(r)$ and $B(r)$
(with boundary conditions $A, B \to 1$ as $r \to \infty$) yields the
Schwarzschild solution.

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

**References:**
- Schwarzschild, K. (1916). *Über das Gravitationsfeld eines Massenpunktes nach
  der Einsteinschen Theorie.* Sitzungsber. Preuss. Akad. Wiss., 189–196.
  [arXiv:physics/9905030](https://arxiv.org/abs/physics/9905030) — the original
  derivation of the exterior vacuum metric.
- Birkhoff, G.D. (1923). *Relativity and Modern Physics.* Harvard University
  Press. — Birkhoff's theorem: every spherically-symmetric vacuum solution is
  static and isometric to Schwarzschild, guaranteeing the uniqueness of the
  result this preset derives.
- Carroll §7.2 — standard pedagogical derivation from the spherically-symmetric
  ansatz to the Schwarzschild metric.
- MTW §31 — full component-by-component derivation and detailed physical
  interpretation.

---

## Preset: de Sitter

**Physics:** The maximally-symmetric solution of the Einstein equations with a
**positive cosmological constant** $\Lambda > 0$ and no matter ($T_{\mu\nu} = 0$).
Describes an exponentially expanding universe — relevant for inflationary
cosmology and the accelerating expansion of the present universe.

**Coordinates:** $(t, r, \theta, \phi)$ — static patch coordinates.

**Metric ansatz** (after symmetry reduction, before solving the EFE):

```math
g_{\mu\nu} = \text{diag}(-f(r),\; h(r),\; r^2,\; r^2 \sin^2\theta)
```

**Solved metric** (apply $f(r) = 1 - \Lambda r^2/3$, $h(r) = (1 - \Lambda r^2/3)^{-1}$ as constraints after generating field equations):

```math
g_{\mu\nu} = \text{diag}\!\left(-1 + \frac{\Lambda r^2}{3},\; \left(1 - \frac{\Lambda r^2}{3}\right)^{-1},\; r^2,\; r^2 \sin^2\theta\right)
```

Here $\Lambda$ is the cosmological constant (a symbol; set a numerical value in
Section 1 if desired).

**What to expect:**
- Applying all five ansatz steps gives $\text{diag}(-f(r), h(r), r^2, r^2\sin^2\theta)$.
- Generating field equations with $\Lambda \neq 0$ yields equations for $f(r)$ and $h(r)$.
- Applying constraints `f(r) = 1 - Lambda*r**2/3` and `h(r) = (1 - Lambda*r**2/3)**(-1)`
  reduces all field equations to $0 = 0$, confirming the solution.
- The metric has a coordinate singularity at $r = \sqrt{3/\Lambda}$, the
  **de Sitter horizon** (analogous to the Schwarzschild horizon).
- The Ricci scalar is constant: $R = 4\Lambda$.

**How the ansatz is derived — step by step:**

The de Sitter static patch is both static and spherically symmetric, so it
undergoes the same five-step symmetry reduction as the Schwarzschild ansatz.
The steps are identical; only the function names and the non-zero $\Lambda$
distinguish the two derivations.

Start: a fully general symmetric 4×4 metric with 10 independent component
symbols $g_{tt}, g_{tr}, g_{t\theta}, g_{t\phi}, g_{rr}, \ldots$

**Step 1 — Static metric** (time-reversal symmetry $t \to -t$):
$$g_{tr} = g_{t\theta} = g_{t\phi} = 0$$
Same reasoning as Schwarzschild: cross terms $g_{ti}\,dt\,dx^i$ would break
time-reversal symmetry. Removes three off-diagonal components.

**Step 2 — Spherical symmetry** (no radial-angular or angle-angle mixing):
$$g_{r\theta} = g_{r\phi} = g_{\theta\phi} = 0$$
$SO(3)$ symmetry forbids coupling between the radial and angular sectors.
Leaves four diagonal components.

**Step 3 — SO(3) invariance** (angular block must be a round sphere):
$$g_{\phi\phi} = \sin^2\theta \cdot g_{\theta\theta}$$
The angular part of the metric at fixed $(t, r)$ must be proportional to
the round-sphere line element.

**Step 4 — Coordinate choice** (define $r$ as the areal radius):
$$g_{\theta\theta} = r^2$$
This is a gauge choice that defines $r$ so that the area of a 2-sphere at
radius $r$ is exactly $4\pi r^2$. Leaves two free functions $g_{tt}(r)$
and $g_{rr}(r)$.

**Step 5 — Rename free functions:**
$$g_{tt} = -f(r), \qquad g_{rr} = h(r)$$

**Result:**

```math
g_{\mu\nu} = \text{diag}(-f(r),\; h(r),\; r^2,\; r^2\sin^2\theta)
```

**Solving the field equations:**
With $\Lambda \neq 0$ and $T_{\mu\nu} = 0$, the EFE $G_{\mu\nu} + \Lambda g_{\mu\nu} = 0$
yields a coupled ODE system for $f(r)$ and $h(r)$. The unique solution satisfying
$f, h \to 1$ as $r \to 0$ (local flatness near the origin) is:

```math
f(r) = 1 - \frac{\Lambda r^2}{3}, \qquad h(r) = \left(1 - \frac{\Lambda r^2}{3}\right)^{-1}
```

Note that $f \cdot h = 1$ — a structural property shared with Schwarzschild
($A \cdot B = 1$ there too). This is a general consequence of spherical symmetry
plus the contracted Bianchi identity.

Enter these as constraints in the "Apply constraints" box after generating field
equations to verify the residuals reduce to $0 = 0$:
```
f(r) = 1 - Lambda*r**2/3
h(r) = (1 - Lambda*r**2/3)**(-1)
```

**EFE setup:** Λ is set to `Lambda` (a symbol). κ remains `8*pi*G`. T_μν = 0.

**References:**
- de Sitter, W. (1917). *On the relativity of inertia. Remarks concerning
  Einstein's latest hypothesis.* Proc. Acad. Sci. Amsterdam 19, 1217–1225. —
  the original de Sitter solution.
- Carroll §8.1 — the de Sitter solution, static-patch coordinates, and its
  relationship to the cosmological constant.
- Hawking, S.W. & Ellis, G.F.R. (1973). *The Large Scale Structure of
  Space-Time.* Cambridge University Press. §5.2 for the maximally-symmetric
  vacuum solutions (de Sitter and Anti-de Sitter).

---

## Preset: Flat polar

**Physics:** Ordinary flat (Minkowski) space expressed in **spherical coordinates**
$(t, r, \theta, \phi)$ rather than Cartesian. No curvature — this is purely a
coordinate effect.

**Coordinates:** $(t, r, \theta, \phi)$.

**Metric:**

```math
g_{\mu\nu} = \text{diag}(-1,\; 1,\; r^2,\; r^2 \sin^2\theta)
```

**What to expect:**
- Non-trivial Christoffel symbols even though spacetime is flat — these arise
  from the curvature of the coordinate lines, not from gravitational curvature.
- Riemann tensor = 0 (the space is flat).
- Einstein tensor = 0.

**How the metric is derived:**
This is Minkowski space written in spherical coordinates — no new physics, just
a coordinate transformation. Starting from Cartesian coordinates $(t, x, y, z)$
with metric $\text{diag}(-1,1,1,1)$, apply:

$$x = r\sin\theta\cos\phi, \quad y = r\sin\theta\sin\phi, \quad z = r\cos\theta$$

The spatial line element $dx^2 + dy^2 + dz^2$ becomes $dr^2 + r^2 d\theta^2 + r^2\sin^2\theta\,d\phi^2$,
giving the metric directly. No symmetry reduction or equation solving is involved.

**Use case:**
- Demonstrates the distinction between **coordinate singularities** (the metric
  is degenerate at $r = 0$ and $\theta = 0, \pi$) and **physical curvature**.
- Good introduction to non-Cartesian coordinate computation before tackling
  the Schwarzschild ansatz.
- The non-zero Christoffel symbols here are the familiar **connection
  coefficients** of spherical coordinates that appear in vector calculus
  (e.g., in the expression for the Laplacian in spherical coordinates).

**References:**
- No original paper: this is Minkowski space expressed in spherical coordinates —
  a coordinate transformation, not a new geometry.
- Carroll §1.4 — the Minkowski metric in curvilinear coordinates, and the
  distinction between coordinate and physical singularities.
- MTW §6 — flat spacetime in spherical coordinates; how non-zero Christoffel
  symbols arise from coordinate curvature without any physical gravitational
  field.

---

## Preset: FLRW (flat)

**Physics:** The **Friedmann–Lemaître–Robertson–Walker** (FLRW) metric describes a
homogeneous, isotropic, expanding (or contracting) universe. This preset uses the
**flat spatial slice** (k = 0), which is consistent with current CMB observations
to high precision.

**Coordinates:** $(t, r, \theta, \phi)$ — comoving coordinates. Galaxies sit at
fixed $(r, \theta, \phi)$; the expansion is encoded in the scale factor $a(t)$.

**Metric ansatz** (after all six steps are applied):

```math
g_{\mu\nu} = \text{diag}(-1,\; a(t)^2,\; a(t)^2 r^2,\; a(t)^2 r^2 \sin^2\theta)
```

**Stress-energy tensor:**
The preset fills T_μν with a **perfect fluid** at rest in comoving coordinates:

```math
T_{\mu\nu} = \text{diag}(\rho,\; p\,a(t)^2,\; p\,a(t)^2 r^2,\; p\,a(t)^2 r^2\sin^2\theta)
```

where $\rho$ is the energy density and $p$ is the pressure (both SymPy symbols —
assign values or an equation of state via custom constraints).

**What to expect:**
- Applying all six ansatz steps yields $\text{diag}(-1, a(t)^2, a(t)^2 r^2, a(t)^2 r^2\sin^2\theta)$.
- Non-trivial Christoffel symbols involving $\dot{a}(t) \equiv da/dt$.
- The field equations $G_{\mu\nu} = \kappa T_{\mu\nu}$ yield (after simplification)
  two independent equations — the **Friedmann equations**:

```math
H^2 = \left(\frac{\dot{a}}{a}\right)^2 = \frac{\kappa \rho}{3}
```

```math
\frac{\ddot{a}}{a} = -\frac{\kappa}{6}(\rho + 3p)
```

- The Riemann tensor is non-trivial but highly symmetric (spatial isotropy).

**Applying constraints:**
- For a **matter-dominated** universe: `p = 0` → $a(t) \propto t^{2/3}$.
- For a **radiation-dominated** universe: `p = rho/3` → $a(t) \propto t^{1/2}$.
- For **de Sitter expansion**: set `T_str = 0` and `lambda_str = Lambda` → $a(t) \propto e^{Ht}$.

**How the ansatz is derived — step by step:**

The FLRW metric follows from the **cosmological principle**: the universe is
spatially homogeneous (the same everywhere) and isotropic (the same in every
direction). This preset loads a *general ansatz* and pre-populates six derivation
steps that reduce the 10-component general metric to the FLRW form.

The spatial curvature parameter $k$ labels three possibilities:
- $k = +1$: positively curved (3-sphere)
- $k = 0$: flat (Euclidean) — this preset
- $k = -1$: negatively curved (hyperbolic)

Start: a fully general symmetric 4×4 metric with 10 independent component symbols
$g_{tt}, g_{tr}, g_{t\theta}, g_{t\phi}, g_{rr}, \ldots$

**Step 1 — Comoving gauge** (homogeneity kills time-space cross terms):
In comoving coordinates the 4-velocity of matter is $u^\mu = (1,0,0,0)$ — galaxies
sit at fixed spatial coordinates and only move through time. Homogeneity requires
the metric to look the same to all comoving observers, which forces the mixed
time-space components to vanish:
$$g_{tr} = g_{t\theta} = g_{t\phi} = 0$$
This removes three off-diagonal components, leaving seven.

**Step 2 — Spatial isotropy** (no off-diagonal spatial terms):
Isotropy means no preferred spatial direction. Any off-diagonal spatial term like
$g_{r\theta}$ would distinguish the $r$ and $\theta$ directions, breaking isotropy:
$$g_{r\theta} = g_{r\phi} = g_{\theta\phi} = 0$$
This leaves four diagonal components: $g_{tt}(t), g_{rr}(t,r), g_{\theta\theta}(t,r), g_{\phi\phi}(t,r,\theta)$.

**Step 3 — SO(3) invariance** (angular block must be a round sphere):
Isotropy in the angular directions requires that the metric restricted to a
$t,r = \text{const}$ 2-surface is proportional to the round-sphere metric
$d\theta^2 + \sin^2\theta\,d\phi^2$. Therefore:
$$g_{\phi\phi} = \sin^2\theta \cdot g_{\theta\theta}$$
This reduces to three free components: $g_{tt}(t), g_{rr}(t,r), g_{\theta\theta}(t,r)$.

**Step 4 — Flat spatial slices** ($k=0$, angular metric is $r^2$ times radial metric):
For flat ($k=0$) spatial sections the 3D spatial metric at any fixed $t$ must
be conformally equivalent to flat Euclidean space. In spherical coordinates this
means the angular metric at radius $r$ is $r^2$ times the radial metric:
$$g_{\theta\theta} = r^2\, g_{rr}$$
This eliminates one more free component, leaving $g_{tt}(t)$ and $g_{rr}(t)$.

**Step 5 — Cosmic time gauge** (normalize the lapse to $-1$):
We are free to reparametrize the time coordinate so that the 4D line element reads
$ds^2 = -dt^2 + \ldots$. This is the *cosmic time* gauge. It fixes:
$$g_{tt} = -1$$
One free component remains: $g_{rr}(t)$.

**Step 6 — Introduce the scale factor** $a(t)$:
The single remaining unknown, the overall spatial scale, is named the *scale factor*
$a(t)$:
$$g_{rr} = a(t)^2$$

**Result:**

```math
g_{\mu\nu} = \text{diag}(-1,\; a(t)^2,\; a(t)^2 r^2,\; a(t)^2 r^2 \sin^2\theta)
```

**The stress-energy tensor** for a perfect fluid at rest in comoving
coordinates takes the diagonal form $T_{\mu\nu} = \text{diag}(\rho, p\,g_{rr}, p\,g_{\theta\theta}, p\,g_{\phi\phi})$,
where $\rho$ is energy density and $p$ is pressure. Both are treated as
free symbols until an equation of state is specified.

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

**Metric ansatz** (after all five steps are applied):

```math
g_{\mu\nu} = \text{diag}(-f(z),\; f(z),\; f(z),\; f(z))
```

**Solved metric** (apply $f(z) = L^2/z^2$ as a constraint after generating field equations):

```math
g_{\mu\nu} = \frac{L^2}{z^2}\,\text{diag}(-1,\; 1,\; 1,\; 1)
```

**EFE setup:** $\Lambda = -3/L^2$ (negative, as required for AdS). $L$ is the **AdS radius**
(a free parameter; larger $L$ = weaker curvature).

**What to expect:**
- Applying all five ansatz steps yields $\text{diag}(-f(z), f(z), f(z), f(z))$.
- The solved metric is conformally flat: $g_{\mu\nu} = (L/z)^2\,\eta_{\mu\nu}$.
- Einstein tensor satisfies $G_{\mu\nu} = (3/L^2)\,g_{\mu\nu}$, so the field
  equation $G_{\mu\nu} + \Lambda\,g_{\mu\nu} = G_{\mu\nu} - (3/L^2)\,g_{\mu\nu} = 0$
  is satisfied identically.
- Ricci scalar: $R = -12/L^2$ (constant, negative — the hallmark of AdS).
- No coordinate singularity or horizon (unlike de Sitter).
- **Computation time:** Fast once steps are applied (~5–10 s). All metric components
  are rational functions of $z$ only — no unknown functions except $f(z)$.

**Comparison with de Sitter:**

| Property | de Sitter | Anti-de Sitter |
|----------|-----------|----------------|
| $\Lambda$ | $> 0$ | $< 0$ |
| Spatial sections | positively curved or flat | negatively curved |
| Horizon | yes (at $r = \sqrt{3/\Lambda}$) | no |
| Relevant to | inflationary cosmology | AdS/CFT, holography |

**How the ansatz is derived — step by step:**

Anti-de Sitter space can be described in several coordinate patches. The Poincaré
patch used here is derived by requiring translational symmetry in the boundary
directions $(t, x, y)$ and conformal flatness in $z$. This preset loads a
*general ansatz* and pre-populates five derivation steps.

Start: a fully general symmetric 4×4 metric with 10 independent component symbols
$g_{tt}, g_{tz}, g_{tx}, g_{ty}, g_{zz}, \ldots$ in coordinates $(t, z, x, y)$.

Here $z > 0$ is the **holographic (bulk) direction** — the conformal boundary of
AdS sits at $z = 0$. The coordinates $t, x, y$ are the **boundary directions**
in which the Poincaré patch has translational symmetry.

**Step 1 — Boundary translational symmetry** (no bulk-direction time cross terms):
The metric must be independent of $t$ (stationarity in the boundary sense).
Time-reversal symmetry $t \to -t$ kills the mixed terms between the time direction
and all spatial directions:
$$g_{tz} = g_{tx} = g_{ty} = 0$$
This removes three off-diagonal components.

**Step 2 — No bulk-boundary spatial mixing:**
Translational symmetry in $x$ and $y$ — the metric is independent of these
coordinates — combined with the absence of any preferred boundary spatial direction
forces all remaining off-diagonal terms to zero:
$$g_{zx} = g_{zy} = g_{xy} = 0$$
The metric is now diagonal: $g_{tt}(z),\, g_{zz}(z),\, g_{xx}(z),\, g_{yy}(z)$.

**Step 3 — Boundary spatial isotropy** (SO(2) rotational symmetry in $x$-$y$ plane):
The Poincaré patch metric is invariant under rotations in the boundary $(x,y)$
plane. This requires the two boundary spatial components to be equal:
$$g_{yy} = g_{xx}$$
Three free components remain: $g_{tt}(z),\, g_{zz}(z),\, g_{xx}(z)$.

**Step 4 — Conformal flatness** (bulk spatial component equals boundary spatial):
The Poincaré patch metric is conformally flat — it is proportional to the
Minkowski metric $\eta_{\mu\nu}$ with a $z$-dependent conformal factor. This
means the bulk direction $z$ and the boundary spatial directions $x, y$ must
enter symmetrically:
$$g_{zz} = g_{xx}$$
Two free components remain: $g_{tt}(z)$ and $g_{xx}(z)$.

**Step 5 — Introduce the conformal factor** $f(z)$:
The two remaining free functions are related by the Minkowski signature
($g_{tt}$ is negative, spatial components positive). Name the single scale:
$$g_{tt} = -f(z), \qquad g_{xx} = f(z)$$

**Result:**

```math
g_{\mu\nu} = \text{diag}(-f(z),\; f(z),\; f(z),\; f(z))
```

Solving the field equations $G_{\mu\nu} + \Lambda g_{\mu\nu} = 0$ with $\Lambda = -3/L^2$
yields the unique solution with the correct boundary behaviour at $z \to 0$:

```math
f(z) = \frac{L^2}{z^2}
```

**Applying constraints:**
After generating field equations, enter in the constraints box:
```
f(z) = L**2/z**2
```
The residuals should reduce to $0 = 0$.

The Poincaré patch only covers half of the full AdS manifold. The boundary of
the patch at $z = 0$ is where the dual CFT lives in AdS/CFT.


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

```math
g_{\mu\nu} = \begin{pmatrix}
  -(1 - 2Mr/\Sigma) & 0 & 0 & -2Mar\sin^2\theta/\Sigma \\
  0 & \Sigma/\Delta & 0 & 0 \\
  0 & 0 & \Sigma & 0 \\
  -2Mar\sin^2\theta/\Sigma & 0 & 0 & (r^2+a^2+2Ma^2r\sin^2\theta/\Sigma)\sin^2\theta
\end{pmatrix}
```

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

**How the metric is derived:**
The Kerr metric is the unique stationary, axially-symmetric vacuum solution of
the Einstein equations. The derivation starts from a **general stationary
axisymmetric ansatz** — a metric that:

1. Is **stationary**: independent of $t$ (admits a timelike Killing vector $\partial_t$).
2. Is **axially symmetric**: independent of $\phi$ (admits a spacelike Killing
   vector $\partial_\phi$).
3. Allows **frame dragging**: an off-diagonal $g_{t\phi} \neq 0$ term, which
   couples the time and azimuthal directions. This is the key structural
   difference from Schwarzschild.

The metric components are therefore functions of $(r, \theta)$ only. Kerr's
original 1963 derivation exploited the **Petrov classification** — the vacuum
equations with the algebraically-special (Petrov type D) constraint reduce to
a tractable system. Boyer and Lindquist (1967) then introduced the coordinate
choice $\Delta = r^2 - 2Mr + a^2$ that simplifies the $g_{rr}$ and $g_{\theta\theta}$
components, eliminating the off-diagonal $g_{r\theta}$ term.

Defining $\Sigma \equiv r^2 + a^2\cos^2\theta$ and $\Delta \equiv r^2 - 2Mr + a^2$,
the resulting Boyer-Lindquist metric is an exact vacuum solution — not an ansatz
to be solved, but the closed-form result of Kerr's derivation. The preset loads
it directly.

**Note:** The full derivation of the Kerr metric from first principles is one
of the hardest calculations in classical GR. The app loads the known solution
and verifies $G_{\mu\nu} = 0$ numerically via SymPy.

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

## Preset: Milton — modified Schwarzschild

**Physics:** The analytic closed-form solution derived by Milton (2020, arXiv:2003.11587)
for a spherically-symmetric spacetime with a subluminal torsion vector field.  The
torsion introduces a new integration parameter $\alpha$ that deforms the Schwarzschild
geometry at large $r$ while recovering it near the black hole.  At galactic scales
the deformation can mimic a dark-matter-like gravitational effect without any new
matter content.

**Coordinates:** $(t, r, \theta, \phi)$ — Schwarzschild coordinates.

**Connection mode:** Levi-Civita.  The metric already encodes the effect of the torsion
vector; no separate torsion tensor is entered in this preset.  Use it to inspect and
verify the deformed solution directly.

**Parameters:**
- $m$ — mass (geometric units, plays the role of $M$ in Schwarzschild)
- $\alpha$ — torsion parameter (units of inverse length; $\alpha \to 0$ recovers Schwarzschild)

**Metric** (Milton §9, eq. 9.13–9.14 with $\alpha = \beta$):

Define $f(r) \equiv 1 - \dfrac{2m\sqrt{1 - \alpha^2 r^2}}{r}$.  Then:

```math
g_{\mu\nu} = \mathrm{diag}\!\left(-f(r),\;\frac{1}{f(r)\,(1-\alpha^2 r^2)},\;r^2,\;r^2\sin^2\theta\right)
```

As $\alpha \to 0$: $f(r) \to 1 - 2m/r$, and the metric reduces to the standard
Schwarzschild solution with $A(r) = B(r)^{-1} = 1 - 2m/r$.

**What to expect:**
- Computing $G_{\mu\nu}$ with the Levi-Civita connection should return a non-zero
  result — this is *not* a vacuum GR solution.  The Einstein tensor encodes the
  effective stress-energy sourced by the torsion field.
- The effective stress-energy (eq. 5.5 of the paper) takes the form
  $T_{\mu\nu}^{\text{eff}} = [g_{\mu\nu}\,g^{\rho\sigma}N_\rho N_\sigma - 2N_\mu N_\nu]/\kappa$
  where $N_\mu$ is the torsion covector.
- For the subluminal case ($N^r = N^\theta = N^\phi = 0$, only $N^t \neq 0$) the
  effective energy density is positive and the pressure is negative — consistent with
  a dark-energy-like equation of state.
- Computation time: moderate (~2–5 min) because $\sqrt{1-\alpha^2 r^2}$ generates
  non-trivial derivative chains.

**Applying constraints:**
To recover Schwarzschild set `alpha = 0` in the Constraints box.  All torsion
corrections vanish and $G_{\mu\nu} = 0$.

**References:**
- Milton, G.W. (2020). *A possible explanation of dark matter and dark energy
  involving a vector torsion field.* arXiv preprint.
  [arXiv:2003.11587](https://arxiv.org/abs/2003.11587) [gr-qc].
  §9, eq. 9.13–9.14 for the explicit subluminal solution.

---

## Preset: Milton — subluminal torsion (spherical)

**Physics:** The starting point for Milton's (2020) spherically-symmetric vacuum
field equations in the **subluminal regime**: the torsion vector field has only a
time component $N^0(r) \neq 0$ (all spatial components zero).  The metric and
the torsion field are left as unknowns to be solved for simultaneously.

Unlike the "modified Schwarzschild" preset above, this preset does **not** load a
closed-form solution — it sets up the coupled system of ODEs in $A(r)$, $B(r)$,
and $N^0(r)$ that Milton solves analytically in his paper.  The field equations
generated here are those ODEs.

**Coordinates:** $(t, r, \theta, \phi)$.  The coordinate index order is
$0 = t,\ 1 = r,\ 2 = \theta,\ 3 = \phi$.

**Connection mode:** Torsion (Mode 2).  The connection is
$\Gamma^\sigma{}_{\mu\nu} = \mathring{\Gamma}^\sigma{}_{\mu\nu} + K^\sigma{}_{\mu\nu}$
where $\mathring{\Gamma}$ is the Levi-Civita part and $K$ is the contorsion
derived automatically from the pre-filled $T^\sigma{}_{\mu\nu}$.

**Metric ansatz** (five Schwarzschild symmetry steps, same as the Schwarzschild preset):

```math
g_{\mu\nu} = \mathrm{diag}(-A(r),\; B(r),\; r^2,\; r^2\sin^2\theta)
```

**Stress-energy tensor:** $T_{\mu\nu} = 0$ (vacuum; the torsion contribution enters
through the modified connection, not through $T_{\mu\nu}$).

### Why the torsion components contain $A(r)$ and $B(r)$

Milton's key result (§3, eq. 3.9) is that the requirement "geodesics = autoparallels"
forces the torsion to be **completely antisymmetric** in all three indices when
fully lowered: $T_{\lambda\mu\nu} = T_{[\lambda\mu\nu]}$.  In 4D, any completely
antisymmetric rank-3 tensor is dual to a single contravariant 4-vector $N^k$:

```math
T^\sigma{}_{\mu\nu} = 2\,g^{\sigma\rho}\,\varepsilon_{\rho\mu\nu\kappa}\,N^\kappa\,\sqrt{-g}
```

Here $\varepsilon_{\rho\mu\nu\kappa}$ is the Levi-Civita symbol ($\varepsilon_{0123} = +1$),
and $\sqrt{-g}$ is the square root of the metric determinant — which for our diagonal
ansatz is:

```math
\sqrt{-g} = \sqrt{A(r)\,B(r)}\,r^2\sin\theta
```

The factor $g^{\sigma\rho}$ also brings in the metric inverse.  **This is why
$A(r)$ and $B(r)$ appear inside the torsion components**: the torsion is
constructed from $N^k$ plus the metric, so expressing $T^\sigma{}_{\mu\nu}$
requires the metric functions even before any equations are solved.

This is not circular.  The field equations come out as a coupled nonlinear ODE
system in $A(r)$, $B(r)$, and $N^0(r)$ simultaneously — analogous to how the
FLRW preset has $T_{\mu\nu}$ containing $a(t)$ while $a(t)$ is the unknown being
solved for.  SymPy treats $A(r)$, $B(r)$, $N^0(r)$ as abstract functions and
carries their derivatives through the full Riemann pipeline symbolically.

### Pre-filled torsion components

For the subluminal case $N^k = (N^0(r), 0, 0, 0)$ only the following upper-triangle
entries of $T^\sigma{}_{\mu\nu}$ are non-zero (the lower triangle follows from
antisymmetry $T^\sigma{}_{\mu\nu} = -T^\sigma{}_{\nu\mu}$):

| $(\sigma,\,\mu,\,\nu)$ | Component | Derivation |
|---|---|---|
| $(1,\,2,\,3)$ | $-2r^2\sin\theta\,\sqrt{AB}/B \cdot N^0$ | $\varepsilon_{1230} = -1$, $g^{11} = 1/B$ |
| $(2,\,1,\,3)$ | $+2\sin\theta\,\sqrt{AB} \cdot N^0$ | $\varepsilon_{2130} = +1$, $g^{22} = 1/r^2$ |
| $(3,\,1,\,2)$ | $-2\sqrt{AB}/\sin\theta \cdot N^0$ | $\varepsilon_{3120} = -1$, $g^{33} = 1/(r^2\sin^2\theta)$ |

The signs come from the permutation parity of $\varepsilon_{ρμν0}$:
$\varepsilon_{1230} = -1$ (3 inversions in $[1,2,3,0]$),
$\varepsilon_{2130} = +1$ (4 inversions in $[2,1,3,0]$),
$\varepsilon_{3120} = -1$ (5 inversions in $[3,1,2,0]$).

One can verify complete antisymmetry of the lowered tensor by checking
$T_{123} = T_{231} = T_{312} = -2r^2\sin\theta\,\sqrt{AB}\,N^0$ (all equal,
confirming it is totally antisymmetric under cyclic permutations). ✓

### What to expect

- The field equations $G_{\mu\nu} = 0$ (from the full torsion connection) will be
  a system of ODEs in $A(r)$, $B(r)$, $N^0(r)$.
- This is equivalent to Milton's eq. 9.3, written as $R_{\mu\nu} = 0$ for the
  full (torsion) connection — since $R = 0$ from the trace, $G = R - \frac{1}{2}gR = R$.
- The vacuum field equations have the analytic solution (eq. 9.13–9.14):
  $A(r) = 1/[f(r)(1-\alpha^2 r^2)]$, $B(r) = f(r) = 1 - 2m\sqrt{1-\alpha^2 r^2}/r$,
  with $(N^0)^2 = \alpha^2/(\kappa b)$.
- Apply these as constraints to verify the residuals reduce to $0 = 0$.
- **Computation time:** Expect 5–15 min.  The torsion terms add extra algebraic
  complexity compared to the Schwarzschild ansatz alone.

**References:**
- Milton, G.W. (2020). *A possible explanation of dark matter and dark energy
  involving a vector torsion field.* arXiv preprint.
  [arXiv:2003.11587](https://arxiv.org/abs/2003.11587) [gr-qc].
  §3 (complete antisymmetry condition, eq. 3.9), §5 (field equations), §9 (spherical solutions).
- Hehl, F.W., McCrea, J.D., Mielke, E.W., & Ne'eman, Y. (1995).
  *Metric-affine gauge theory of gravity: Field equations, Noether identities,
  world spinors, and breaking of dilation invariance.*
  Physics Reports, 258(1–2), 1–171. — general framework for torsion and contorsion.
- See also `docs/connections.md` in this repository for the contorsion construction
  ($K^\sigma{}_{\mu\nu}$ from $T^\sigma{}_{\mu\nu}$) used by Mode 2.

---

## Preset: Milton — superluminal torsion (spherical)

**Physics:** The spherically-symmetric, superluminal-regime companion to the subluminal
preset above.  Here the torsion vector field has only a **radial** component
$N^1(r) \neq 0$ (time and angular components zero).  This corresponds to Milton's
Case B (§9), which does not have a simple closed-form solution — the field equations
form a nonlinear ODE system that must be solved numerically.  The paper reports
"black hole"-type behaviour with $b(r) \to \infty$ as $r \to \infty$, suggesting a
divergent effective mass at large distances — a possible dark-matter signal.

**Coordinates:** $(t, r, \theta, \phi)$, same as the subluminal preset.

**Connection mode:** Torsion (Mode 2), same pipeline.

**Metric ansatz:** Identical five-step Schwarzschild symmetry reduction:

```math
g_{\mu\nu} = \mathrm{diag}(-A(r),\; B(r),\; r^2,\; r^2\sin^2\theta)
```

**Stress-energy tensor:** $T_{\mu\nu} = 0$ (vacuum).

### Pre-filled torsion components

For the superluminal case $N^k = (0, N^1(r), 0, 0)$, the formula becomes
$T^\sigma{}_{\mu\nu} = 2\,g^{\sigma\rho}\,\varepsilon_{\rho\mu\nu 1}\,N^1\,\sqrt{-g}$.
Non-zero upper-triangle entries:

| $(\sigma,\,\mu,\,\nu)$ | Component | Derivation |
|---|---|---|
| $(0,\,2,\,3)$ | $-2r^2\sin\theta\,\sqrt{AB}/A \cdot N^1$ | $\varepsilon_{0231} = +1$, $g^{00} = -1/A$ |
| $(2,\,0,\,3)$ | $-2\sin\theta\,\sqrt{AB} \cdot N^1$ | $\varepsilon_{2031} = -1$, $g^{22} = 1/r^2$ |
| $(3,\,0,\,2)$ | $+2\sqrt{AB}/\sin\theta \cdot N^1$ | $\varepsilon_{3021} = +1$, $g^{33} = 1/(r^2\sin^2\theta)$ |

The sign derivations:
$\varepsilon_{0231}$: $[0,2,3,1]$ has 2 inversions → $+1$.
$\varepsilon_{2031}$: $[2,0,3,1]$ has 3 inversions → $-1$.
$\varepsilon_{3021}$: $[3,0,2,1]$ has 4 inversions → $+1$.

Note the structural parallel with the subluminal table: everywhere $A$ (the
$g_{tt}$ function) appeared in the subluminal case, $B$ appears in the superluminal
case and vice versa.  This reflects the swap $N^0 \leftrightarrow N^1$ under the
causal structure change ($k = (N^0)^2 - (N^1)^2$ changes sign).

### What to expect

- Field equations are a coupled ODE system in $A(r)$, $B(r)$, $N^1(r)$.
- No closed-form analytic solution is known; Milton integrates them numerically
  (§9, Case B) and finds singularity-like behaviour at finite $r$ and
  $b(r) \to \infty$ as $r \to \infty$.
- The field equations generated here are the starting point for that numerical
  analysis.
- **Computation time:** Same order as the subluminal preset (~5–15 min).

**Causal note:** The terminology "superluminal" refers to the torsion vector $N^k$
being spacelike ($g_{\mu\nu}N^\mu N^\nu > 0$), not to any observable signal
propagating faster than light.  The geodesic structure of the spacetime is
modified by the torsion, but causality is preserved in the usual GR sense.

**References:**
- Milton, G.W. (2020). *A possible explanation of dark matter and dark energy
  involving a vector torsion field.* arXiv preprint.
  [arXiv:2003.11587](https://arxiv.org/abs/2003.11587) [gr-qc].
  §9, Case B (superluminal spherical solution, numerical analysis).
- Hehl, F.W., McCrea, J.D., Mielke, E.W., & Ne'eman, Y. (1995).
  *Metric-affine gauge theory of gravity: Field equations, Noether identities,
  world spinors, and breaking of dilation invariance.*
  Physics Reports, 258(1–2), 1–171. — general framework for metric-affine theories
  and the geometric origin of torsion.
- See also `docs/connections.md` in this repository for the contorsion construction.

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
