"""
ui/export.py
------------
Export tensor results and step-by-step derivations as LaTeX or Python.

Functions that build content strings are pure (no Streamlit).
render_export_buttons() renders Streamlit download widgets.
"""

from __future__ import annotations

import re
from sympy import latex, Integer, Matrix


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_diagonal(m: Matrix) -> bool:
    n = m.shape[0]
    return all(m[i, j] == Integer(0) for i in range(n) for j in range(n) if i != j)


def _matrix_latex(m: Matrix) -> str:
    """
    Render a matrix as LaTeX.
    Diagonal matrices use \\operatorname{diag}(...) to stay narrow.
    General matrices use the standard pmatrix.
    """
    if _is_diagonal(m):
        entries = ", ".join(latex(m[i, i]) for i in range(m.shape[0]))
        return rf"\operatorname{{diag}}\!\left({entries}\right)"
    return latex(m)


def _efe_lhs_latex(lambda_str: str) -> str:
    lam = lambda_str.strip()
    if lam in ("0", ""):
        return r"G_{\mu\nu}"
    return r"G_{\mu\nu} + \Lambda\, g_{\mu\nu}"


def _efe_rhs_latex(T_str: str, kappa_str: str) -> str:
    T = T_str.strip()
    if T in ("0", ""):
        return "0"
    kap = kappa_str.strip() or r"\kappa"
    return rf"{latex_scalar(kap)}\, T_{{\mu\nu}}"


def latex_scalar(s: str) -> str:
    """Best-effort conversion of a scalar string to LaTeX."""
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import symbols, pi
    try:
        expr = parse_expr(s, local_dict={"pi": pi, "G": symbols("G"), "c": symbols("c")})
        return latex(expr)
    except Exception:
        return s


def _unknown_functions(metric: Matrix) -> list[str]:
    """Return any unknown function names in the metric (e.g. A, B)."""
    return sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', str(metric))))


def _count_nonzero(tensor, rank: int, n: int) -> int:
    """Count non-zero independent components of a symmetric rank-2 tensor."""
    if rank == 2:
        return sum(
            1 for mu in range(n) for nu in range(mu, n)
            if tensor[mu, nu] != Integer(0)
        )
    return 0


# ---------------------------------------------------------------------------
# Preamble / footer
# ---------------------------------------------------------------------------

def _latex_preamble(title: str, subtitle: str = "") -> str:
    sub_line = rf"\large {subtitle}\\" if subtitle else ""
    return rf"""\documentclass{{article}}
\usepackage{{amsmath, amssymb, mathtools}}
\usepackage[margin=2.5cm]{{geometry}}
\usepackage{{parskip}}
\allowdisplaybreaks
\title{{{title}}}
\author{{sym\_gr --- symbolic GR}}
\date{{\today}}
\begin{{document}}
\maketitle
"""


def _latex_footer() -> str:
    return r"\end{document}" + "\n"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _sec_intro(
    coords,
    metric: Matrix,
    lambda_str: str,
    kappa_str: str,
    T_str: str,
    signature: str,
) -> str:
    coord_str = ", ".join(str(c) for c in coords)
    efe_lhs = _efe_lhs_latex(lambda_str)
    efe_rhs = _efe_rhs_latex(T_str, kappa_str)
    sig_note = (
        "mostly-plus $(-,+,+,+)$" if signature == "-+++"
        else "mostly-minus $(+,-,-,-)$"
    )
    lam = lambda_str.strip()
    T   = T_str.strip()
    if lam in ("0","") and T in ("0",""):
        phys = "This is a \\textbf{vacuum} computation ($T_{\\mu\\nu} = 0$, $\\Lambda = 0$)."
    elif lam not in ("0","") and T in ("0",""):
        phys = (
            "This computation includes a \\textbf{cosmological constant} "
            f"$\\Lambda = {latex_scalar(lam)}$ with vanishing stress-energy ($T_{{\\mu\\nu}} = 0$)."
        )
    else:
        phys = "This computation includes a non-trivial stress-energy tensor $T_{\\mu\\nu}$."

    funcs = _unknown_functions(metric)
    if funcs:
        func_str = ", ".join(f"${f}$" for f in funcs)
        ansatz_note = (
            f"The metric is an \\textit{{ansatz}} with unknown function(s) {func_str} "
            "to be determined by solving the field equations."
        )
    else:
        ansatz_note = "The metric has no free functions --- it is fully specified."

    return rf"""
\section*{{Overview}}

We work in coordinates $({coord_str})$ with signature {sig_note}.
The Einstein field equations take the form
\begin{{equation}}
  {efe_lhs} = {efe_rhs}.
\end{{equation}}
{phys}
{ansatz_note}

The following sections present: the metric and its inverse, the
Christoffel symbols (with full derivations where available), the Riemann
and Ricci tensors, the Ricci scalar, the Einstein tensor, and the
resulting field equations.

"""


def _sec_metric(metric: Matrix, coords) -> str:
    coord_str = ", ".join(str(c) for c in coords)
    return rf"""
\section*{{Metric Ansatz $g_{{\mu\nu}}$}}

The covariant metric tensor in coordinates $({coord_str})$:
\begin{{equation}}
  g_{{\mu\nu}} = {_matrix_latex(metric)}.
\end{{equation}}

"""


def _sec_metric_inv(metric_inv: Matrix) -> str:
    return rf"""
\section*{{Inverse Metric $g^{{\mu\nu}}$}}

The contravariant metric $g^{{\mu\nu}}$ satisfies $g^{{\mu\rho}} g_{{\rho\nu}} = \delta^\mu_{{\,\nu}}$:
\begin{{equation}}
  g^{{\mu\nu}} = {_matrix_latex(metric_inv)}.
\end{{equation}}

"""


def _sec_christoffel(steps: dict, coords: list) -> str:
    n = len(coords)
    nonzero_count = sum(
        1 for sigma in range(n)
        for mu in range(n)
        for nu in range(mu, n)
        if not steps[(sigma, mu, nu)].is_zero
    )

    if nonzero_count == 0:
        summary = (
            r"All Christoffel symbols vanish identically. "
            r"The coordinate frame is \textbf{geodesic} --- "
            r"the connection is flat in these coordinates."
        )
    else:
        summary = (
            rf"There are \textbf{{{nonzero_count}}} non-vanishing independent "
            r"Christoffel components (showing $\mu \leq \nu$ only; "
            r"$\Gamma^\sigma_{\mu\nu} = \Gamma^\sigma_{\nu\mu}$ by symmetry)."
        )

    lines = [
        r"\section*{Christoffel Symbols $\Gamma^\sigma_{\mu\nu}$}",
        "",
        r"The Christoffel symbols of the second kind are defined by",
        r"\begin{equation}",
        r"  \Gamma^\sigma_{\mu\nu} = \frac{1}{2}\,g^{\sigma\rho}"
        r"\bigl(\partial_\mu g_{\nu\rho} + \partial_\nu g_{\mu\rho}"
        r" - \partial_\rho g_{\mu\nu}\bigr).",
        r"\end{equation}",
        "",
        summary,
        "",
    ]

    # Zero components — compact list
    zero_labels = []
    for sigma in range(n):
        for mu in range(n):
            for nu in range(mu, n):
                step = steps[(sigma, mu, nu)]
                if step.is_zero:
                    sig_t = latex(coords[sigma])
                    mu_t  = latex(coords[mu])
                    nu_t  = latex(coords[nu])
                    zero_labels.append(
                        rf"\Gamma^{{{sig_t}}}_{{{mu_t}{nu_t}}} = 0"
                    )
    if zero_labels:
        lines.append(r"\paragraph*{Vanishing components:}")
        # Render in groups of 4 per line to avoid horizontal overflow
        groups = [zero_labels[i:i+4] for i in range(0, len(zero_labels), 4)]
        for group in groups:
            lines.append(r"$" + r", \quad ".join(group) + r"$\par")
        lines.append("")

    # Nonzero components — full derivation
    for sigma in range(n):
        for mu in range(n):
            for nu in range(mu, n):
                step = steps[(sigma, mu, nu)]
                if step.is_zero:
                    continue
                sig_t = latex(coords[sigma])
                mu_t  = latex(coords[mu])
                nu_t  = latex(coords[nu])
                lhs   = rf"\Gamma^{{{sig_t}}}_{{{mu_t}{nu_t}}}"

                lines.append(rf"\paragraph*{{${lhs}$:}}")
                lines.append(r"\begin{align*}")
                first = True
                for term in step.rho_terms:
                    if term.is_zero:
                        continue
                    rho_t  = latex(coords[term.rho])
                    leader = rf"  {lhs} &=" if first else r"  &\quad +"
                    first  = False
                    lines.append(
                        rf"{leader} \tfrac{{1}}{{2}} \cdot {latex(term.g_inv)}"
                        rf" \cdot \bigl({latex(term.d1)} + {latex(term.d2)}"
                        rf" - {latex(term.d3)}\bigr)"
                        rf" && (\rho = {rho_t}) \\"
                    )
                lines.append(rf"  &= {latex(step.value)}")
                lines.append(r"\end{align*}")
                lines.append("")

    return "\n".join(lines) + "\n"


def _sec_riemann(riemann, coords: list) -> str:
    n = len(coords)
    nonzero_count = sum(
        1 for rho in range(n) for sigma in range(n)
        for mu in range(n) for nu in range(mu+1, n)
        if riemann[rho, sigma, mu, nu] != Integer(0)
    )

    if nonzero_count == 0:
        body = (
            r"All components vanish. The spacetime is \textbf{flat}: "
            r"$R^\rho{}_{\sigma\mu\nu} = 0$."
        )
        return rf"""
\section*{{Riemann Curvature Tensor $R^\rho{{}}_{{\sigma\mu\nu}}$}}

The Riemann tensor measures tidal forces and intrinsic curvature:
\begin{{equation}}
  R^\rho{{}}_{{\sigma\mu\nu}} =
    \partial_\mu\Gamma^\rho_{{\nu\sigma}}
  - \partial_\nu\Gamma^\rho_{{\mu\sigma}}
  + \Gamma^\rho_{{\mu\lambda}}\Gamma^\lambda_{{\nu\sigma}}
  - \Gamma^\rho_{{\nu\lambda}}\Gamma^\lambda_{{\mu\sigma}}.
\end{{equation}}
{body}

"""

    lines = [
        r"\section*{Riemann Curvature Tensor $R^\rho{}_{\sigma\mu\nu}$}",
        "",
        r"The Riemann tensor measures tidal forces and intrinsic curvature:",
        r"\begin{equation}",
        r"  R^\rho{}_{\sigma\mu\nu} =",
        r"    \partial_\mu\Gamma^\rho_{\nu\sigma}",
        r"  - \partial_\nu\Gamma^\rho_{\mu\sigma}",
        r"  + \Gamma^\rho_{\mu\lambda}\Gamma^\lambda_{\nu\sigma}",
        r"  - \Gamma^\rho_{\nu\lambda}\Gamma^\lambda_{\mu\sigma}.",
        r"\end{equation}",
        rf"Non-zero independent components ($\mu < \nu$, "
        rf"\textbf{{{nonzero_count}}} total):",
        r"\begin{align*}",
    ]
    for rho in range(n):
        for sigma in range(n):
            for mu in range(n):
                for nu in range(mu+1, n):
                    val = riemann[rho, sigma, mu, nu]
                    if val == Integer(0):
                        continue
                    rho_t = latex(coords[rho])
                    sig_t = latex(coords[sigma])
                    mu_t  = latex(coords[mu])
                    nu_t  = latex(coords[nu])
                    lines.append(
                        rf"  R^{{{rho_t}}}_{{{sig_t}{mu_t}{nu_t}}} &= {latex(val)} \\"
                    )
    lines += [r"\end{align*}", ""]
    return "\n".join(lines) + "\n"


def _sec_ricci(ricci, coords: list) -> str:
    n = ricci.shape[0]
    nonzero = _count_nonzero(ricci, 2, n)
    if nonzero == 0:
        body = r"All components vanish: $R_{\mu\nu} = 0$."
        return rf"""
\section*{{Ricci Tensor $R_{{\mu\nu}}$}}

Obtained by contracting the first and third Riemann indices:
$R_{{\mu\nu}} = R^\rho{{}}_{{\mu\rho\nu}}$.
{body}

"""

    lines = [
        r"\section*{Ricci Tensor $R_{\mu\nu}$}",
        "",
        r"Obtained by contracting the first and third Riemann indices: "
        r"$R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}$.",
        r"\begin{align*}",
    ]
    for mu in range(n):
        for nu in range(mu, n):
            val = ricci[mu, nu]
            if val == Integer(0):
                continue
            mu_t = latex(coords[mu])
            nu_t = latex(coords[nu])
            lines.append(rf"  R_{{{mu_t}{nu_t}}} &= {latex(val)} \\")
    lines += [r"\end{align*}", ""]
    return "\n".join(lines) + "\n"


def _sec_ricci_scalar(ricci_scalar, coords: list) -> str:
    return rf"""
\section*{{Ricci Scalar $R$}}

The Ricci scalar $R = g^{{\mu\nu}} R_{{\mu\nu}}$:
\begin{{equation}}
  R = {latex(ricci_scalar)}.
\end{{equation}}

"""


def _sec_einstein(einstein, coords: list) -> str:
    n = einstein.shape[0]
    nonzero = _count_nonzero(einstein, 2, n)
    if nonzero == 0:
        body = r"All components vanish: $G_{\mu\nu} = 0$."
        return rf"""
\section*{{Einstein Tensor $G_{{\mu\nu}}$}}

$G_{{\mu\nu}} = R_{{\mu\nu}} - \tfrac{{1}}{{2}} R\, g_{{\mu\nu}}$.
{body}

"""

    lines = [
        r"\section*{Einstein Tensor $G_{\mu\nu}$}",
        "",
        r"$G_{\mu\nu} = R_{\mu\nu} - \tfrac{1}{2} R\, g_{\mu\nu}$.",
        r"\begin{align*}",
    ]
    for mu in range(n):
        for nu in range(mu, n):
            val = einstein[mu, nu]
            if val == Integer(0):
                continue
            mu_t = latex(coords[mu])
            nu_t = latex(coords[nu])
            lines.append(rf"  G_{{{mu_t}{nu_t}}} &= {latex(val)} \\")
    lines += [r"\end{align*}", ""]
    return "\n".join(lines) + "\n"


def _sec_field_equations(eqs: list, lambda_str: str, kappa_str: str, T_str: str) -> str:
    efe_lhs = _efe_lhs_latex(lambda_str)
    efe_rhs = _efe_rhs_latex(T_str, kappa_str)

    if not eqs:
        return rf"""
\section*{{Field Equations}}

Setting ${efe_lhs} = {efe_rhs}$, all independent equations are satisfied
identically ($0 = 0$).  The metric ansatz is a valid exact solution of
the configured Einstein field equations.

"""

    lines = [
        r"\section*{Field Equations}",
        "",
        rf"Setting ${efe_lhs} = {efe_rhs}$, the independent component equations are:",
        r"\begin{align}",
    ]
    for i, eq in enumerate(eqs, start=1):
        lines.append(rf"  {latex(eq.lhs)} &= {latex(eq.rhs)} \label{{eq:{i}}} \\")
    lines += [r"\end{align}", ""]
    return "\n".join(lines) + "\n"


def _sec_next_steps(metric: Matrix, eqs: list | None) -> str:
    funcs = _unknown_functions(metric)
    if not funcs:
        return ""

    func_str = ", ".join(f"${f}(\\cdot)$" for f in funcs)
    n_eqs = len(eqs) if eqs else "?"

    return rf"""
\section*{{Next Steps}}

The field equations above constitute a system of \textbf{{{n_eqs}}} equations
for the unknown metric function(s) {func_str}.
To obtain the explicit metric:
\begin{{enumerate}}
  \item Solve the system (analytically or numerically) subject to appropriate
        boundary conditions (e.g.\ asymptotic flatness: metric $\to$ Minkowski
        as $r \to \infty$).
  \item Verify the solution by substituting back and confirming $G_{{\mu\nu}}$
        matches the right-hand side.
  \item Apply additional physical constraints (symmetry, regularity at the
        origin, matching conditions) to fix integration constants.
\end{{enumerate}}

"""


# ---------------------------------------------------------------------------
# Main assembler
# ---------------------------------------------------------------------------

def build_full_latex(
    coords,
    metric,
    metric_inv,
    christoffel_steps_data: dict | None = None,
    riemann=None,
    ricci=None,
    ricci_scalar=None,
    einstein=None,
    field_eqs=None,
    lambda_str: str = "0",
    kappa_str: str = "8*pi*G",
    T_str: str = "0",
    signature: str = "-+++",
) -> str:
    """Assemble a complete, narrative LaTeX document."""
    from sympy import Matrix as SMatrix
    m  = SMatrix(metric) if not isinstance(metric, SMatrix) else metric
    mi = SMatrix(metric_inv) if not isinstance(metric_inv, SMatrix) else metric_inv

    coord_str = ", ".join(str(c) for c in coords)
    funcs = _unknown_functions(m)
    if funcs:
        subtitle = f"Spacetime: ansatz in $({coord_str})$ with unknowns " + \
                   ", ".join(f"${f}$" for f in funcs)
    else:
        subtitle = f"Spacetime in coordinates $({coord_str})$"

    parts = [_latex_preamble("GR Tensor Derivation", subtitle)]
    parts.append(_sec_intro(coords, m, lambda_str, kappa_str, T_str, signature))
    parts.append(_sec_metric(m, coords))
    parts.append(_sec_metric_inv(mi))

    if christoffel_steps_data is not None:
        parts.append(_sec_christoffel(christoffel_steps_data, coords))

    if riemann is not None:
        parts.append(_sec_riemann(riemann, coords))

    if ricci is not None:
        parts.append(_sec_ricci(ricci, coords))

    if ricci_scalar is not None:
        parts.append(_sec_ricci_scalar(ricci_scalar, coords))

    if einstein is not None:
        parts.append(_sec_einstein(einstein, coords))

    if field_eqs is not None:
        parts.append(_sec_field_equations(field_eqs, lambda_str, kappa_str, T_str))
        parts.append(_sec_next_steps(m, field_eqs))

    parts.append(_latex_footer())
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Python code builder (unchanged)
# ---------------------------------------------------------------------------

def build_python_code(
    coords,
    metric,
    lambda_str: str = "0",
    kappa_str: str = "8*pi*G",
    T_str: str = "0",
    with_field_eqs: bool = True,
) -> str:
    coord_names = ", ".join(str(c) for c in coords)
    func_names = sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', str(metric))))
    func_decls = ""
    if func_names:
        func_decls = (
            "# Unknown metric functions\n"
            + "\n".join(f"{f} = Function('{f}')" for f in func_names)
            + "\n"
        )

    from sympy import Matrix as SMatrix
    m = SMatrix(metric) if not isinstance(metric, SMatrix) else metric
    metric_repr = repr(m)

    rhs_section = ""
    if lambda_str.strip() not in ("0", "") or T_str.strip() not in ("0", ""):
        rhs_section = f"""
# EFE right-hand side configuration
lambda_val = sympify('{lambda_str}')
kappa_val  = sympify('{kappa_str}')
T_str      = '''{T_str}'''
"""

    field_eq_section = ""
    if with_field_eqs:
        field_eq_section = """
# Field equations
eqs = field_equations(einstein_tensor)
for i, eq in enumerate(eqs, 1):
    print(f"  ({i})", eq)
"""

    return f"""\
\"\"\"
Auto-generated by sym_gr
Reproduces the tensor computation for the configured spacetime.
\"\"\"

from sympy import symbols, Function, Matrix, diag, sin, cos, pi, sqrt, sympify
from sympy import exp, log

from core.spacetime import Spacetime
from core.system import field_equations

# Coordinates
{coord_names} = symbols('{coord_names}')

{func_decls}
# Metric ansatz
metric = {metric_repr}

# Build spacetime
st = Spacetime([{coord_names}], metric)

# Compute tensors
print("Christoffel symbols:")
christoffel = st.christoffel()
print(christoffel)

print("\\nRiemann tensor:")
riemann = st.riemann()
print(riemann)

print("\\nRicci tensor:")
ricci = st.ricci()
print(ricci)

print("\\nRicci scalar:")
R = st.ricci_scalar()
print(R)

print("\\nEinstein tensor:")
einstein_tensor = st.einstein()
print(einstein_tensor)
{rhs_section}{field_eq_section}
"""


# ---------------------------------------------------------------------------
# Streamlit download buttons
# ---------------------------------------------------------------------------

def render_export_buttons(
    latex_content: str | None = None,
    python_content: str | None = None,
    key_prefix: str = "export",
) -> None:
    import streamlit as st
    cols = st.columns([1, 1, 4])
    if latex_content is not None:
        with cols[0]:
            st.download_button(
                label="Download .tex",
                data=latex_content,
                file_name="derivation.tex",
                mime="text/plain",
                key=f"{key_prefix}_tex",
            )
    if python_content is not None:
        with cols[1]:
            st.download_button(
                label="Download .py",
                data=python_content,
                file_name="computation.py",
                mime="text/plain",
                key=f"{key_prefix}_py",
            )
