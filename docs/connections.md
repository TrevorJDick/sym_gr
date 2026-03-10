# Affine Connections and Torsion

This document explains the three connection modes available in sym_gr, the
mathematics behind each one, and exactly which tensor components are affected
at each stage of the computation pipeline.

---

## Background: What is a Connection?

In general relativity, a **connection** defines how to transport vectors along
curves — in other words, how to take derivatives of tensor fields in a curved
spacetime.  The connection coefficients Γ^σ_μν (sometimes called Christoffel
symbols in the torsion-free case) encode this information.

The connection enters every downstream tensor through the same formula for the
**Riemann curvature tensor**:

```
R^ρ_σμν = ∂_μ Γ^ρ_νσ − ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ − Γ^ρ_νλ Γ^λ_μσ
```

This formula is **valid for any affine connection** — it does not assume the
connection is symmetric or metric-compatible.  Ricci, Einstein, and field
equations all follow from this single formula, so changing the connection
propagates through the entire pipeline automatically.

---

## The Three Modes

### Mode 1 — Levi-Civita (default)

**What it is:** The unique connection that is simultaneously

- **Torsion-free:** Γ^σ_μν = Γ^σ_νμ (symmetric in lower indices)
- **Metric-compatible:** ∇_ρ g_μν = 0 (the metric is covariantly constant)

**How it is computed:**

```
Γ^σ_μν = ½ g^σρ (∂_μ g_νρ + ∂_ν g_μρ − ∂_ρ g_μν)
```

This is entirely determined by the metric.  No additional input is required.

**What components are free:**
For an n-dimensional spacetime the connection has n³ components in principle,
but the symmetry Γ^σ_μν = Γ^σ_νμ reduces the independent components to
n²(n+1)/2.  In 4D this is 40.

**What is zero:**
The torsion tensor T^σ_μν = Γ^σ_μν − Γ^σ_νμ vanishes identically.

**Use when:**
Standard GR.  Schwarzschild, FLRW, Anti-de Sitter, any classical spacetime.

---

### Mode 2 — Metric + Torsion Tensor

**What it is:** A metric-compatible connection that allows non-zero torsion.
The researcher supplies the torsion tensor T^σ_μν directly; the full connection
is assembled automatically.

**The torsion tensor**

T^σ_μν is a rank-(1,2) tensor defined as the antisymmetric part of the
connection:

```
T^σ_μν = Γ^σ_μν − Γ^σ_νμ
```

It must be antisymmetric in its last two indices by definition:

```
T^σ_μν = −T^σ_νμ
```

In 4D this gives 4 × 6 = 24 independent components (4 choices of σ, and 6
antisymmetric pairs of (μ, ν)).  Diagonal entries T^σ_μμ are always zero.

**The contorsion tensor**

Before writing the formula, a word on notation — because the same symbol Γ
is about to mean two different things, and the bookkeeping matters.

In standard GR (Mode 1) the Christoffel symbols *are* the Levi-Civita
connection.  There is only one connection and one Γ; no distinction is needed.

In a torsion theory we introduce a *new*, more general affine connection that
is no longer symmetric in its lower indices.  It is still called Γ^σ_μν in
most of the literature — same letter, different object.  To tell the two apart
we write Γ̊^σ_μν (Gamma with a ring) for the original metric-derived
Levi-Civita connection, reserving the plain Γ^σ_μν for the new general one.
This is purely bookkeeping: different authors use different conventions
({^σ_μν}, ˜Γ, °Γ, etc.) and any of them is fine as long as the distinction is
clear.

With that in hand, the decomposition is simply:

```
Γ^σ_μν = Γ̊^σ_μν + K^σ_μν
```

Read this as: the new general connection equals the old LC connection plus a
correction term K^σ_μν called the contorsion.  The contorsion carries all the
torsion information and is chosen specifically so that metric compatibility
(∇_ρ g_μν = 0) is preserved despite the connection being non-symmetric.

K is computed in three steps:

**Step 1** — Lower the first index of the torsion:

```
t_λμν = g_λσ T^σ_μν
```

This gives the fully covariant torsion.  It is still antisymmetric in (μ, ν).

**Step 2** — Build the covariant contorsion:

```
K_λμν = ½ (t_λμν − t_μλν − t_νλμ)
```

Note: K_λμν is antisymmetric in its **first two** indices (K_λμν = −K_μλν).
This is what guarantees metric compatibility: the antisymmetry ensures
∇_ρ g_μν = 0.

**Step 3** — Raise the first index:

```
K^σ_μν = g^σλ K_λμν
```

**What components are affected:**

| Tensor | Effect |
|--------|--------|
| Connection Γ^σ_μν | No longer symmetric in (μ, ν): Γ^σ_μν ≠ Γ^σ_νμ in general |
| Torsion T^σ_μν | Non-zero; set by the researcher |
| Riemann R^ρ_σμν | Modified because Γ changes; symmetries R_ρσμν = R_μνρσ and R_ρσμν = −R_σρμν may be broken |
| Ricci R_μν | No longer guaranteed to be symmetric |
| Einstein G_μν | No longer guaranteed to be symmetric |
| Bianchi identity ∇_λ G^λ_ν = 0 | Not guaranteed to hold with a non-LC connection |

**Use when:**
Einstein-Cartan gravity, teleparallel gravity, models with spin-torsion
coupling, the Milton (2020) torsion dark matter/energy model, or any theory
where torsion is a physical degree of freedom.

---

### Mode 3 — Full Connection (direct specification)

**What it is:** The most general mode.  The researcher specifies all n³
connection coefficients Γ^σ_μν directly as symbolic expressions.  No symmetry
is assumed and no metric-compatibility condition is imposed.

In 4D this is 4 × 4 × 4 = 64 independent components, entered as four 4×4
matrices (one per upper index σ).

**Relationship between full and torsion modes:**
Any full connection can be decomposed as:

```
Γ^σ_μν = Γ̊^σ_μν + K^σ_μν + L^σ_μν
```

where:
- Γ̊^σ_μν is the LC connection (metric-compatible, torsion-free part)
- K^σ_μν is the contorsion (metric-compatible torsion contribution)
- L^σ_μν is the **disformation** (metric-incompatible part, also called the non-metricity contribution)

Mode 2 sets L = 0 (metric-compatible + torsion).
Mode 3 allows L ≠ 0 as well.

**What the app computes from a full connection:**

The torsion T^σ_μν is always computed from the antisymmetric part:

```
T^σ_μν = Γ^σ_μν − Γ^σ_νμ
```

This is displayed in the Torsion section of the results.  The symmetric part
{Γ^σ_μν + Γ^σ_νμ}/2 contains both the LC contribution and any non-metricity.

**What components are affected:**

| Tensor | Effect |
|--------|--------|
| Connection Γ^σ_μν | Fully specified by the researcher; no constraints |
| Torsion T^σ_μν | Computed as antisymmetric part; generally non-zero |
| Non-metricity Q_ρμν = ∇_ρ g_μν | May be non-zero (not directly displayed but encoded in the symmetric part of Γ) |
| Riemann R^ρ_σμν | Computed from the given Γ; no symmetry guaranteed |
| Ricci R_μν | Generally asymmetric |
| Einstein G_μν | Generally asymmetric |

**Use when:**
Weitzenböck geometry (teleparallel equivalent of GR), metric-affine gravity
(MAG), non-metricity theories (f(Q) gravity), exploring exotic affine
structures, or any theory where you want complete control over the connection
independent of the metric.

---

## Pipeline Summary

The computation pipeline is the same for all three modes:

```
User input
    │
    ▼
Γ^σ_μν  (connection coefficients, shape n×n×n)
    │
    ├──► T^σ_μν = Γ^σ_μν − Γ^σ_νμ          (Torsion tensor)
    │
    ▼
R^ρ_σμν = ∂_μ Γ^ρ_νσ − ∂_ν Γ^ρ_μσ          (Riemann tensor)
          + Γ^ρ_μλ Γ^λ_νσ − Γ^ρ_νλ Γ^λ_μσ
    │
    ▼
R_μν = R^ρ_μρν                               (Ricci tensor, contract 1st & 3rd)
    │
    ├──► R = g^μν R_μν                        (Ricci scalar)
    │
    ▼
G_μν = R_μν − ½ R g_μν                       (Einstein tensor)
    │
    ▼
G_μν = κ T_μν − Λ g_μν                       (Field equations)
```

The only step that differs between modes is how Γ^σ_μν is obtained.
Everything from Riemann onward is mode-agnostic.

---

## Symmetry Properties by Mode

| Property | Levi-Civita | Torsion | Full |
|----------|:-----------:|:-------:|:----:|
| Γ^σ_μν = Γ^σ_νμ | ✓ | ✗ | ✗ |
| T^σ_μν = 0 | ✓ | ✗ | ✗ |
| ∇_ρ g_μν = 0 | ✓ | ✓ | ✗ |
| R_μν = R_νμ | ✓ | ✗ in general | ✗ |
| G_μν = G_νμ | ✓ | ✗ in general | ✗ |
| ∇_λ G^λ_ν = 0 | ✓ | ✗ in general | ✗ |

---

## References

- Carroll, S. (2004). *Spacetime and Geometry*. §3 (Levi-Civita connection, Riemann tensor)
- Hehl, F. W. et al. (1995). Metric-affine gauge theory of gravity. *Physics Reports*, 258(1–2).
- Milton, G. W. (2020). A possible explanation of dark matter and dark energy involving a vector torsion field. arXiv:2003.11587
- Nakahara, M. (2003). *Geometry, Topology and Physics*. §7 (connections, torsion, curvature)
