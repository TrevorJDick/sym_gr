"""
ui/parse.py
-----------
Parse raw user-supplied strings into SymPy objects.

No Streamlit dependency — pure parsing utilities.
"""

from __future__ import annotations

from sympy import (
    Function,
    Matrix,
    Symbol,
    cos,
    diag,
    exp,
    log,
    pi,
    sin,
    sqrt,
    symbols,
)
from sympy.parsing.sympy_parser import parse_expr


def parse_coords(coords_str: str) -> list[Symbol]:
    """
    Parse a comma-separated coordinate string into a list of SymPy symbols.

    Parameters
    ----------
    coords_str : str
        E.g. ``"t, r, theta, phi"``

    Returns
    -------
    list of sympy.Symbol
    """
    names = [s.strip() for s in coords_str.split(",") if s.strip()]
    if not names:
        raise ValueError("No coordinates provided.")
    return list(symbols(" ".join(names)))


def _build_local_dict(coord_syms: list[Symbol]) -> dict:
    """Build a local_dict for parse_expr containing coords + common functions."""
    local: dict = {str(s): s for s in coord_syms}
    local.update(
        {
            "sin": sin,
            "cos": cos,
            "diag": diag,
            "Matrix": Matrix,
            "Function": Function,
            "pi": pi,
            "sqrt": sqrt,
            "exp": exp,
            "log": log,
        }
    )
    return local


def parse_metric(metric_str: str, coord_syms: list[Symbol]) -> Matrix:
    """
    Parse a metric expression string into a SymPy Matrix.

    Parameters
    ----------
    metric_str : str
        A string that evaluates to a sympy.Matrix or diag(...) call.
        E.g. ``"diag(-1, 1, 1, 1)"`` or ``"Matrix([[-A(r),0],[0,B(r)]])"``
    coord_syms : list of Symbol
        Coordinate symbols already created, included in parse scope.

    Returns
    -------
    sympy.Matrix

    Raises
    ------
    ValueError
        On parse failure or if the result is not a Matrix.
    """
    local = _build_local_dict(coord_syms)

    # Inject any Function('X')(coord) variables that appear as calls in the string
    # This allows A(r), B(r) etc. to be parsed without explicit pre-declaration.
    # We do this by adding all single-uppercase and lowercase letters as Functions.
    import re
    func_names = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', metric_str))
    for name in func_names:
        if name not in local:
            local[name] = Function(name)

    try:
        result = parse_expr(metric_str, local_dict=local, evaluate=True)
    except Exception as exc:
        raise ValueError(f"Could not parse metric: {exc}") from exc

    if isinstance(result, Matrix):
        return result
    # diag() returns MutableDenseMatrix via sympy's diag function
    try:
        return Matrix(result)
    except Exception as exc:
        raise ValueError(
            f"Metric expression did not produce a Matrix (got {type(result).__name__})."
        ) from exc


def parse_constraint(line: str, coord_syms: list[Symbol]) -> "sympy.Eq":  # noqa: F821
    """
    Parse a single constraint line of the form ``LHS = RHS`` into a SymPy Eq.

    Parameters
    ----------
    line : str
        E.g. ``"A(r) = 1 - 2*M/r"``
    coord_syms : list of Symbol

    Returns
    -------
    sympy.Eq

    Raises
    ------
    ValueError
        If the line cannot be parsed or has no ``=`` sign.
    """
    from sympy import Eq, symbols as sp_symbols

    # Split on the first '=' that is not part of '==' or '>=' or '<='
    import re
    parts = re.split(r'(?<![=<>!])=(?!=)', line, maxsplit=1)
    if len(parts) != 2:
        raise ValueError(
            f"Constraint line must contain exactly one '=': got {line!r}"
        )

    lhs_str, rhs_str = parts[0].strip(), parts[1].strip()

    local = _build_local_dict(coord_syms)

    # Inject extra symbols that appear on RHS (e.g. M, G, c)
    all_names = set(re.findall(r'\b([A-Za-z_]\w*)\b', lhs_str + " " + rhs_str))
    extra_symbols: list[str] = []
    func_names: set[str] = set()

    # First pass: identify function calls
    for name in set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', lhs_str + " " + rhs_str)):
        if name not in local:
            func_names.add(name)
            local[name] = Function(name)

    # Second pass: everything else that's not already known is a symbol
    for name in all_names:
        if name not in local and name not in func_names:
            extra_symbols.append(name)
    if extra_symbols:
        new_syms = sp_symbols(" ".join(extra_symbols))
        if not isinstance(new_syms, (list, tuple)):
            new_syms = [new_syms]
        for s in new_syms:
            local[str(s)] = s

    try:
        lhs = parse_expr(lhs_str, local_dict=local, evaluate=True)
        rhs = parse_expr(rhs_str, local_dict=local, evaluate=True)
    except Exception as exc:
        raise ValueError(f"Could not parse constraint {line!r}: {exc}") from exc

    return Eq(lhs, rhs)
