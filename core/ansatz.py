"""
core/ansatz.py
--------------
Utilities for building a general metric ansatz from symbolic components.

Workflow
--------
1. Call ``generate_metric_symbols(coord_syms)`` to get an n×n Matrix whose
   entries are SymPy Symbols named ``g_{a}_{b}`` (one per independent
   component for the symmetric case, g_{a}_{b} == g_{b}_{a}).

2. Apply constraints one step at a time via ``apply_metric_constraints()``.
   Each constraint is a ``sympy.Eq`` of the form ``Eq(lhs, rhs)`` where
   lhs may be a plain Symbol (e.g. ``g_t_r``) or an applied function
   (e.g. ``A(r)``).  Both cases are handled correctly.

3. Inspect the resulting Matrix and pass it to the normal computation pipeline.

Helper
------
``diagonal_constraints(metric, coord_syms)`` returns the list of Eq objects
that zero out all off-diagonal components of a general metric — useful as a
one-click "diagonal ansatz" shortcut.
"""

from __future__ import annotations

from sympy import Eq, Integer, Matrix, Symbol


# ---------------------------------------------------------------------------
# Symbol generation
# ---------------------------------------------------------------------------

def generate_metric_symbols(coord_syms: list) -> Matrix:
    """
    Build an n×n symmetric Matrix of SymPy Symbols for a general metric.

    Component names follow the pattern ``g_{a}_{b}`` where *a* and *b* are
    the string representations of the coordinate symbols.  For symmetric
    off-diagonal pairs ``(i, j)`` and ``(j, i)`` the same Symbol is used.

    Parameters
    ----------
    coord_syms : list of sympy.Symbol

    Returns
    -------
    sympy.Matrix
        n×n Matrix with entries ``Symbol("g_{coord_i}_{coord_j}")``.

    Examples
    --------
    >>> from sympy import symbols
    >>> t, r = symbols('t r')
    >>> generate_metric_symbols([t, r])
    Matrix([[g_t_t, g_t_r], [g_t_r, g_r_r]])
    """
    n = len(coord_syms)
    names = [str(s) for s in coord_syms]

    # Build the symbol pool (upper triangle + diagonal)
    sym_pool: dict[tuple[int, int], Symbol] = {}
    for i in range(n):
        for j in range(i, n):
            sym_name = f"g_{names[i]}_{names[j]}"
            sym_pool[(i, j)] = Symbol(sym_name)

    mat = []
    for i in range(n):
        row = []
        for j in range(n):
            key = (min(i, j), max(i, j))
            row.append(sym_pool[key])
        mat.append(row)

    return Matrix(mat)


# ---------------------------------------------------------------------------
# Constraint application
# ---------------------------------------------------------------------------

def apply_metric_constraints(
    metric: Matrix,
    constraints: list[Eq],
    coord_syms: list,
) -> Matrix:
    """
    Substitute constraint equations into every component of a metric Matrix.

    Handles both plain-symbol constraints (e.g. ``Eq(g_t_r, 0)``) and
    function-valued constraints (e.g. ``Eq(A(r), 1 - 2*M/r)``) by
    delegating to ``core.constraints._function_subs``.

    Parameters
    ----------
    metric : sympy.Matrix
    constraints : list of sympy.Eq
    coord_syms : list of sympy.Symbol
        Coordinate symbols (used by ``_function_subs`` for chain-rule
        differentiation inside Derivative nodes).

    Returns
    -------
    sympy.Matrix
        New Matrix with all substitutions applied component-wise.
    """
    from core.constraints import _function_subs

    subs_dict = {eq.lhs: eq.rhs for eq in constraints}
    n = metric.shape[0]

    new_entries = []
    for i in range(n):
        for j in range(n):
            new_entries.append(_function_subs(metric[i, j], subs_dict))

    return Matrix(n, n, new_entries)


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def diagonal_constraints(metric: Matrix, coord_syms: list) -> list[Eq]:
    """
    Return ``Eq(component, 0)`` for every off-diagonal component of *metric*.

    Only unique off-diagonal entries are included (upper triangle).

    Parameters
    ----------
    metric : sympy.Matrix
    coord_syms : list (unused, kept for API consistency)

    Returns
    -------
    list of sympy.Eq
    """
    n = metric.shape[0]
    seen: set = set()
    result: list[Eq] = []
    for i in range(n):
        for j in range(i + 1, n):
            entry = metric[i, j]
            if entry != Integer(0) and entry not in seen:
                seen.add(entry)
                result.append(Eq(entry, Integer(0)))
    return result


def stationary_constraints(metric: Matrix, coord_syms: list) -> list[Eq]:
    """
    Return ``Eq(component, 0)`` for time–space cross terms.

    Assumes coordinate index 0 is the time coordinate.  Zeros all
    off-diagonal components in the first row/column.

    Parameters
    ----------
    metric : sympy.Matrix
    coord_syms : list (first element is assumed to be the time coordinate)

    Returns
    -------
    list of sympy.Eq
    """
    n = metric.shape[0]
    seen: set = set()
    result: list[Eq] = []
    for j in range(1, n):
        entry = metric[0, j]  # g_t_j
        if entry != Integer(0) and entry not in seen:
            seen.add(entry)
            result.append(Eq(entry, Integer(0)))
    return result
