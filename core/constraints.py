"""
core/constraints.py
-------------------
Apply user-defined constraint equations to a system of field equations.

No physical constraints are hardcoded here. The caller supplies all
constraints — Bianchi identities, symmetry conditions, gauge choices,
or any other algebraic relations — as SymPy Eq objects.

Example
-------
>>> from sympy import symbols, Function, Eq
>>> from core.constraints import apply_constraints
>>>
>>> r, M = symbols('r M')
>>> A = Function('A')(r)
>>> B = Function('B')(r)
>>>
>>> # Tell the system: use the known Schwarzschild solution
>>> constraints = [
...     Eq(A, 1 - 2*M/r),
...     Eq(B, 1 / (1 - 2*M/r)),
... ]
>>> reduced = apply_constraints(field_eqs, constraints)
"""

from __future__ import annotations

from itertools import product as iproduct

from sympy import Eq, Expr, simplify
from sympy.core.function import AppliedUndef
from sympy.tensor.array import ImmutableDenseNDimArray


def _function_subs(expr: Expr, substitutions: dict) -> Expr:
    """
    Substitute function calls into an expression, correctly handling derivatives.

    Standard ``expr.subs({A(r): val})`` does NOT substitute ``A(r)`` inside
    ``Derivative(A(r), r)`` — SymPy blocks this to avoid creating nonsensical
    expressions.  This helper uses ``expr.replace(A.func, lambda x: val)``
    for any key that is an unevaluated function application (like ``A(r)``),
    which correctly propagates through derivatives via the chain rule.

    Scalar substitutions (symbols, plain expressions) fall through to
    standard ``subs``.

    Parameters
    ----------
    expr : sympy.Expr
        The expression to substitute into.
    substitutions : dict
        Mapping from key to replacement value.  Keys may be unevaluated
        function calls like ``A(r)`` or plain symbols.

    Returns
    -------
    sympy.Expr
        Expression with all substitutions applied.
    """
    result = expr
    plain: dict = {}

    for key, val in substitutions.items():
        # Unevaluated function application: A(r), B(r), f(x, y), etc.
        if isinstance(key, AppliedUndef) and len(key.args) == 1:
            arg = key.args[0]          # e.g. r
            f_class = key.func         # e.g. Function('A')
            # replace() applies the lambda to each occurrence of f_class,
            # automatically differentiating val when inside a Derivative.
            result = result.replace(
                f_class, lambda x, _v=val, _a=arg: _v.subs(_a, x)
            )
        else:
            plain[key] = val

    if plain:
        result = result.subs(plain)

    # Evaluate any Derivative(concrete_expr, x) objects created by replace().
    # replace() substitutes functions inside Derivative nodes but leaves the
    # result unevaluated, e.g. Derivative(1 - 2*M/r, r).  doit() computes them.
    return result.doit()


def apply_constraints(
    equations: list[Eq],
    constraints: list[Eq],
    auto_simplify: bool = False,
) -> list[Eq]:
    """
    Substitute constraint equations into a list of field equations.

    Each constraint ``Eq(lhs, rhs)`` is used as the substitution
    ``lhs → rhs`` inside every field equation. Equations that become
    trivially ``0 = 0`` after substitution are removed.

    For constraints whose left-hand side is a function application (e.g.
    ``Eq(A(r), 1 - 2*M/r)``), the substitution is correctly applied inside
    derivative terms as well — see ``_function_subs`` for details.

    Parameters
    ----------
    equations : list of sympy.Eq
        The field equations to reduce (e.g. from ``field_equations()``).
    constraints : list of sympy.Eq
        User-supplied relations. Each must have the form ``Eq(expr, value)``
        where *expr* is the symbol or expression being constrained.
        The left-hand side is used as the substitution key.
    auto_simplify : bool, default False
        If True, apply ``sympy.simplify`` to each equation after
        substitution. This can be slow but often reveals cancellations.

    Returns
    -------
    list of sympy.Eq
        The reduced system, with trivial equations removed.

    Notes
    -----
    Substitutions are applied in the order given. If constraints depend
    on each other (e.g. defining B in terms of A, then substituting A),
    pass them in the correct order.
    """
    subs_dict = {eq.lhs: eq.rhs for eq in constraints}

    result: list[Eq] = []
    for eq in equations:
        new_lhs = _function_subs(eq.lhs, subs_dict)
        new_rhs = _function_subs(eq.rhs, subs_dict)
        if auto_simplify:
            new_lhs = simplify(new_lhs)
            new_rhs = simplify(new_rhs)
        if new_lhs != new_rhs:
            result.append(Eq(new_lhs, new_rhs))

    return result


def simplify_equation_steps(eq: Eq) -> list[tuple[str, "Expr"]]:
    """
    Run a staged simplification on a single equation and return each step.

    Works on the difference ``lhs - rhs``.  Applies the following
    transformations in order, recording each stage that changes the expression:

    1. ``cancel``  — cancel common polynomial factors in rational expressions.
    2. ``trigsimp`` — apply trigonometric identities.
    3. ``simplify`` — general black-box simplification.

    Stops early if the expression reaches zero.

    Parameters
    ----------
    eq : sympy.Eq

    Returns
    -------
    list of (label, expr) pairs
        Each pair contains a human-readable step name and the expression
        ``lhs - rhs`` after that step.  Only steps that change the expression
        are included.  If the expression is already zero, returns an empty list.
    """
    from sympy import cancel, trigsimp, simplify as sp_simplify, Integer

    diff = eq.lhs - eq.rhs
    if diff == Integer(0):
        return []

    steps: list[tuple[str, Expr]] = []
    current = diff

    for label, fn in [
        ("cancel", cancel),
        ("trigsimp", trigsimp),
        ("simplify", sp_simplify),
    ]:
        result = fn(current)
        if result != current:
            steps.append((label, result))
            current = result
        if current == Integer(0):
            break

    return steps


def filter_trivial(equations: list[Eq]) -> list[Eq]:
    """
    Remove equations of the form expr = expr (trivially satisfied).

    Parameters
    ----------
    equations : list of sympy.Eq

    Returns
    -------
    list of sympy.Eq
    """
    return [eq for eq in equations if eq.lhs != eq.rhs]


def constrain_tensor(
    tensor: ImmutableDenseNDimArray,
    constraints: list[Eq],
) -> ImmutableDenseNDimArray:
    """
    Substitute constraints directly into a tensor's components.

    Useful for inserting a known solution into a computed tensor to
    verify that it satisfies the field equations (all components → 0).

    Correctly handles function-valued constraints such as
    ``Eq(A(r), 1 - 2*M/r)`` — derivatives of ``A(r)`` inside tensor
    components are substituted via the chain rule.

    Parameters
    ----------
    tensor : ImmutableDenseNDimArray
        Input tensor (any rank).
    constraints : list of sympy.Eq
        Substitution rules as ``Eq(lhs, rhs)``.

    Returns
    -------
    ImmutableDenseNDimArray
        Tensor with substitutions applied component-wise.
    """
    subs_dict = {eq.lhs: eq.rhs for eq in constraints}

    # Iterate over every scalar component via explicit multi-index enumeration.
    # ImmutableDenseNDimArray iteration yields sub-arrays for rank > 1, so
    # we must use index tuples to reach scalar elements.
    flat = [
        _function_subs(tensor[idx], subs_dict)
        for idx in iproduct(*[range(d) for d in tensor.shape])
    ]
    return ImmutableDenseNDimArray(flat).reshape(*tensor.shape)
