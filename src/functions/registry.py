"""Function registry for LLM tool calling."""

from typing import Callable, Dict, Any, Optional
import json
from pydantic import ValidationError

from .schemas import (
    FUNCTION_SCHEMAS,
    SearchPatientInput,
    CheckInsuranceInput,
    FindSlotsInput,
    BookAppointmentInput
)
from .patient import search_patient
from .insurance import check_insurance_eligibility
from .appointments import find_available_slots, book_appointment


class FunctionRegistry:
    """Registry of available functions for LLM tool calling."""
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {
            "search_patient": search_patient,
            "check_insurance_eligibility": check_insurance_eligibility,
            "find_available_slots": find_available_slots,
            "book_appointment": book_appointment,
        }
        
        self._input_schemas: Dict[str, type] = {
            "search_patient": SearchPatientInput,
            "check_insurance_eligibility": CheckInsuranceInput,
            "find_available_slots": FindSlotsInput,
            "book_appointment": BookAppointmentInput,
        }
    
    def get_schemas(self) -> list:
        """Get OpenAI-compatible function schemas for LLM."""
        return FUNCTION_SCHEMAS
    
    def get_function_names(self) -> list:
        """Get list of available function names."""
        return list(self._functions.keys())
    
    def validate_arguments(self, function_name: str, arguments: Dict[str, Any]) -> tuple:
        """
        Validate function arguments against the schema.
        
        Returns:
            tuple: (is_valid: bool, validated_args or error_message)
        """
        if function_name not in self._input_schemas:
            return False, f"Unknown function: {function_name}"
        
        schema_class = self._input_schemas[function_name]
        
        try:
            validated = schema_class(**arguments)
            return True, validated.model_dump()
        except ValidationError as e:
            return False, f"Validation error: {str(e)}"
    
    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function with the given arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments as a dictionary
        
        Returns:
            dict: Function result or error
        """
        if function_name not in self._functions:
            return {
                "error": True,
                "message": f"Unknown function: {function_name}",
                "available_functions": self.get_function_names()
            }
        
        
        is_valid, result = self.validate_arguments(function_name, arguments)
        if not is_valid:
            return {
                "error": True,
                "message": result
            }
        
        
        try:
            func = self._functions[function_name]
            return func(**result)
        except Exception as e:
            return {
                "error": True,
                "message": f"Execution error: {str(e)}"
            }
    
    def describe_function(self, function_name: str) -> Optional[dict]:
        """Get the schema description for a function."""
        for schema in FUNCTION_SCHEMAS:
            if schema["name"] == function_name:
                return schema
        return None



_registry: Optional[FunctionRegistry] = None


def get_registry() -> FunctionRegistry:
    """Get the singleton function registry instance."""
    global _registry
    if _registry is None:
        _registry = FunctionRegistry()
    return _registry
