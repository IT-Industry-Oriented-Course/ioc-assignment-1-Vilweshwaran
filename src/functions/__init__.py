"""Healthcare function modules."""

from .patient import search_patient
from .insurance import check_insurance_eligibility
from .appointments import find_available_slots, book_appointment
from .registry import FunctionRegistry, get_registry

__all__ = [
    "search_patient",
    "check_insurance_eligibility", 
    "find_available_slots",
    "book_appointment",
    "FunctionRegistry",
    "get_registry",
]
