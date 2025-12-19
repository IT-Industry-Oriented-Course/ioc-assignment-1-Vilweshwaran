"""Insurance eligibility checking function."""

from ..sandbox.mock_api import mock_api
from .schemas import CheckInsuranceInput


def check_insurance_eligibility(patient_id: str, service_type: str) -> dict:
    """
    Check insurance eligibility and coverage for a patient for a specific service type.
    
    Args:
        patient_id: The patient's unique identifier
        service_type: Type of medical service (e.g., 'cardiology', 'primary-care')
    
    Returns:
        dict: FHIR Coverage resource with eligibility information
    """
    
    validated_input = CheckInsuranceInput(patient_id=patient_id, service_type=service_type)
    
    
    coverage = mock_api.get_coverage(
        patient_id=validated_input.patient_id,
        service_type=validated_input.service_type
    )
    
    if coverage is None:
        return {
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "not-found",
                "diagnostics": f"No insurance coverage found for patient '{patient_id}'"
            }]
        }
    
    return coverage
