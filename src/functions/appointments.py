"""Appointment slot finding and booking functions."""

from typing import Optional, List
from ..sandbox.mock_api import mock_api
from .schemas import FindSlotsInput, BookAppointmentInput


def find_available_slots(
    specialty: str, 
    start_date: str, 
    end_date: str, 
    location: Optional[str] = None
) -> dict:
    """
    Find available appointment slots for a given medical specialty within a date range.
    
    Args:
        specialty: Medical specialty (e.g., 'cardiology', 'neurology')
        start_date: Start date for availability search (YYYY-MM-DD)
        end_date: End date for availability search (YYYY-MM-DD)
        location: Preferred facility location (optional)
    
    Returns:
        dict: FHIR Bundle containing available Slot resources
    """
    
    validated_input = FindSlotsInput(
        specialty=specialty,
        start_date=start_date,
        end_date=end_date,
        location=location
    )
    
    
    slots = mock_api.find_slots(
        specialty=validated_input.specialty,
        start_date=validated_input.start_date,
        end_date=validated_input.end_date,
        location=validated_input.location
    )
    
    if not slots:
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 0,
            "entry": [],
            "message": f"No available slots found for {specialty} between {start_date} and {end_date}"
        }
    
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(slots),
        "entry": [{"resource": slot} for slot in slots]
    }


def book_appointment(
    patient_id: str, 
    slot_id: str, 
    reason: str, 
    dry_run: bool = False
) -> dict:
    """
    Book an appointment for a patient at a specific slot.
    
    Args:
        patient_id: The patient's unique identifier
        slot_id: The slot ID to book
        reason: Reason for the appointment
        dry_run: If true, validate the booking without actually creating it
    
    Returns:
        dict: FHIR Appointment resource or OperationOutcome on error
    """
    
    validated_input = BookAppointmentInput(
        patient_id=patient_id,
        slot_id=slot_id,
        reason=reason,
        dry_run=dry_run
    )
    
    
    result = mock_api.book_slot(
        patient_id=validated_input.patient_id,
        slot_id=validated_input.slot_id,
        reason=validated_input.reason,
        dry_run=validated_input.dry_run
    )
    
    if not result.get("success"):
        return {
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "business-rule",
                "diagnostics": result.get("error", "Unknown error occurred")
            }]
        }
    
    return result
