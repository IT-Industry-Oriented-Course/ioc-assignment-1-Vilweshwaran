"""Input validators for request processing."""

from typing import Dict, Any, Optional
from pydantic import ValidationError

from ..functions.schemas import (
    SearchPatientInput,
    CheckInsuranceInput,
    FindSlotsInput,
    BookAppointmentInput
)


def validate_request(function_name: str, arguments: Dict[str, Any]) -> tuple:
    """
    Validate function arguments against the appropriate schema.
    
    Args:
        function_name: Name of the function to validate for
        arguments: Arguments to validate
    
    Returns:
        tuple: (is_valid: bool, validated_data or error_message)
    """
    schema_map = {
        "search_patient": SearchPatientInput,
        "check_insurance_eligibility": CheckInsuranceInput,
        "find_available_slots": FindSlotsInput,
        "book_appointment": BookAppointmentInput,
    }
    
    if function_name not in schema_map:
        return False, f"Unknown function: {function_name}"
    
    schema_class = schema_map[function_name]
    
    try:
        validated = schema_class(**arguments)
        return True, validated.model_dump()
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            errors.append(f"{field}: {msg}")
        return False, "; ".join(errors)


def validate_date_format(date_string: str) -> bool:
    """Validate that a string is in YYYY-MM-DD format."""
    import re
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_string):
        return False
    
    
    try:
        from datetime import datetime
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize a string input to prevent injection attacks."""
    
    import re
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    return sanitized[:max_length].strip()
