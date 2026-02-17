"""
ui/export.py
------------
Export tensor results and step-by-step derivations as LaTeX or Python.

Functions that build content strings are pure (no Streamlit).
render_export_buttons() renders Streamlit download widgets.
"""

from __future__ import annotations

from sympy import latex, Integer
from sympy.tensor.array import ImmutableDenseNDimArray


# ---------------------------------------------------------------------------
# LaTeX builders
# ---------------------------------------------------------------------------

def _latex_preamble(title: str = "GR Tensor Derivation") -> str:
    return rf"""\documentclass{{article}}
\usepackage{{amsmath, amssymb}}
\title{{{title}}}
\date{{\today}}
\begin{{document}}
\maketitle
"""


def _latex_footer() -> str:
    return r"\end{document}" + "\n"


def build_latex_metric(metric, coords) -> str:
    """Return a LaTeX align block for the metric."""
    from sympy import Matrix
    m = Matrix(metric) if not isinstance(metric, Matrix) else metric
    coord_str = ", ".join(str(c) for c in coords)
    lines = [
        r"\section*{Metric}",
        rf"Coordinates: $({coord_str})$\par",
        r"\begin{equation}",
        rf"g_{{\mu\nu}} = {latex(m)}",
        r"\end{equation}",
        "",
    ]
    return "\n".join(lines)


def build_latex_metric_inverse(metric_inv, coords) -> str:
    from sympy import Matrix
    m = Matrix(metric_inv) if not isinstance(metric_inv, Matrix) else metric_inv
    lines = [
        r"\section*{Inverse Metric $g^{\mu\nu}$}",
        r"\begin{equation}",
        rf"g^{{\mu\nu}} = {latex(m)}",
        r"\end{equation}",
        "",
    ]
    return "\n".join(lines)


def build_latex_christoffel_steps(steps: dict, coords: list) -> str:
    """
    Build a full LaTeX section with every Christoffel step.

    Nonzero components get full derivations; zero components get a one-liner.
    """
    n = len(coords)
    lines = [
        r"\section*{Christoffel Symbols $\Gamma^\sigma_{\mu\nu}$}",
        r"Definition:",
        r"\begin{equation}",
        r"\Gamma^\sigma_{\mu\nu} = \frac{1}{2}\, g^{\sigma\rho}"
        r"\bigl(\partial_\mu g_{\nu\rho} + \partial_\nu g_{\mu\rho}"
        r" - \partial_\rho g_{\mu\nu}\bigr)",
        r"\end{equation}",
        "",
    ]

    for sigma in range(n):
        for mu in range(n):
            for nu in range(mu, n):
                step = steps[(sigma, mu, nu)]
                sig_tex = latex(coords[sigma])
                mu_tex  = latex(coords[mu])
                nu_tex  = latex(coords[nu])
                lhs = rf"\Gamma^{{{sig_tex}}}_{{{mu_tex}{nu_tex}}}"

                if step.is_zero:
                    lines.append(rf"\noindent ${lhs} = 0$\par")
                    lines.append("")
                else:
                    lines.append(rf"\subsection*{{${lhs}$}}")
                    lines.append(r"\begin{align*}")

                    first = True
                    for term in step.rho_terms:
                        if term.is_zero:
                            continue
                        rho_tex = latex(coords[term.rho])
                        leader = rf"{lhs} &=" if first else r"&\quad+"
                        first = False
                        lines.append(
                            rf"{leader} \tfrac{{1}}{{2}} \cdot {latex(term.g_inv)}"
                            rf"\cdot \bigl({latex(term.d1)} + {latex(term.d2)}"
                            rf" - {latex(term.d3)}\bigr)"
                            rf" \quad (\rho = {rho_tex}) \\"
                        )

                    # Close with final value
                    lines.append(rf"&= {latex(step.value)}")
                    lines.append(r"\end{align*}")
                    lines.append("")

    return "\n".join(lines)


def build_latex_rank2(tensor, coords: list, name: str, section_title: str) -> str:
    """Build a LaTeX section for a rank-2 tensor."""
    n = tensor.shape[0]
    lines = [
        rf"\section*{{{section_title}}}",
        r"\begin{align*}",
    ]
    any_nonzero = False
    for mu in range(n):
        for nu in range(mu, n):
            val = tensor[mu, nu]
            if val == Integer(0):
                continue
            any_nonzero = True
            mu_tex = latex(coords[mu])
            nu_tex = latex(coords[nu])
            lines.append(
                rf"{name}_{{{mu_tex}{nu_tex}}} &= {latex(val)} \\"
            )
    if not any_nonzero:
        lines.append(r"\text{All components are zero.} \\")
    lines.append(r"\end{align*}")
    lines.append("")
    return "\n".join(lines)


def build_latex_equations(eqs: list, section_title: str = "Field Equations") -> str:
    """Build a LaTeX section for a list of sympy.Eq."""
    lines = [
        rf"\section*{{{section_title}}}",
        r"\begin{align}",
    ]
    if not eqs:
        lines.append(r"\text{All equations satisfied (0 = 0).} \\")
    else:
        for i, eq in enumerate(eqs, start=1):
            lines.append(rf"{latex(eq.lhs)} &= {latex(eq.rhs)} \label{{eq:{i}}} \\")
    lines.append(r"\end{align}")
    lines.append("")
    return "\n".join(lines)


def build_full_latex(
    coords,
    metric,
    metric_inv,
    christoffel_steps_data: dict | None,
    riemann=None,
    ricci=None,
    ricci_scalar=None,
    einstein=None,
    field_eqs=None,
) -> str:
    """Assemble a complete LaTeX document from all available results."""
    parts = [_latex_preamble()]
    parts.append(build_latex_metric(metric, coords))
    parts.append(build_latex_metric_inverse(metric_inv, coords))

    if christoffel_steps_data is not None:
        parts.append(build_latex_christoffel_steps(christoffel_steps_data, coords))
    elif riemann is not None:
        pass  # can add later

    if riemann is not None:
        parts.append(build_latex_rank2(riemann[0], coords, "R", "Riemann (stub)"))

    if ricci is not None:
        parts.append(build_latex_rank2(ricci, coords, "R", r"Ricci Tensor $R_{\mu\nu}$"))

    if einstein is not None:
        parts.append(build_latex_rank2(einstein, coords, "G", r"Einstein Tensor $G_{\mu\nu}$"))

    if field_eqs is not None:
        parts.append(build_latex_equations(field_eqs))

    parts.append(_latex_footer())
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Python code builder
# ---------------------------------------------------------------------------

def build_python_code(
    coords,
    metric,
    lambda_str: str = "0",
    kappa_str: str = "8*pi*G",
    T_str: str = "0",
    with_field_eqs: bool = True,
) -> str:
    """
    Build a self-contained Python script that reproduces the computation.
    """
    import re

    coord_names = ", ".join(str(c) for c in coords)

    # Detect function names used in metric (e.g. A, B)
    metric_str = str(metric)
    func_names = sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', metric_str)))
    func_decls = ""
    if func_names:
        func_decls = (
            "# Unknown metric functions\n"
            + "\n".join(f"{f} = Function('{f}')" for f in func_names)
            + "\n"
        )

    from sympy import Matrix
    m = Matrix(metric) if not isinstance(metric, Matrix) else metric
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
    """Render Download .tex and Download .py buttons side by side."""
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
