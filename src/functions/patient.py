"""Patient search function."""

from typing import Optional, List
from ..sandbox.mock_api import mock_api
from .schemas import Patient, SearchPatientInput


def search_patient(name: str, dob: Optional[str] = None, identifier: Optional[str] = None) -> dict:
    """
    Search for a patient by name, date of birth, or identifier.
    
    Args:
        name: Patient name to search for (first name, last name, or full name)
        dob: Date of birth in YYYY-MM-DD format (optional)
        identifier: Patient identifier such as MRN or SSN (optional)
    
    Returns:
        dict: FHIR Bundle containing matching Patient resources
    """
    
    validated_input = SearchPatientInput(name=name, dob=dob, identifier=identifier)
    
    
    patients = mock_api.search_patients(
        name=validated_input.name,
        dob=validated_input.dob,
        identifier=validated_input.identifier
    )
    
    
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(patients),
        "entry": [{"resource": patient} for patient in patients]
    }
