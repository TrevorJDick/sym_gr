from .spacetime import Spacetime
from .system import field_equations, independent_equations
from .constraints import apply_constraints, filter_trivial

__all__ = [
    "Spacetime",
    "field_equations",
    "independent_equations",
    "apply_constraints",
    "filter_trivial",
]
