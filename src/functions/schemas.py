"""FHIR-style JSON schemas for function parameters and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum






class AppointmentStatus(str, Enum):
    PROPOSED = "proposed"
    PENDING = "pending"
    BOOKED = "booked"
    ARRIVED = "arrived"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    NOSHOW = "noshow"


class CoverageStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    ENTERED_IN_ERROR = "entered-in-error"


class SlotStatus(str, Enum):
    BUSY = "busy"
    FREE = "free"
    BUSY_UNAVAILABLE = "busy-unavailable"
    BUSY_TENTATIVE = "busy-tentative"






class HumanName(BaseModel):
    """FHIR HumanName datatype."""
    family: str = Field(..., description="Family name (surname)")
    given: List[str] = Field(default_factory=list, description="Given names")
    prefix: Optional[List[str]] = Field(default=None, description="Name prefixes")
    suffix: Optional[List[str]] = Field(default=None, description="Name suffixes")

    def full_name(self) -> str:
        return f"{' '.join(self.given)} {self.family}"


class Identifier(BaseModel):
    """FHIR Identifier datatype."""
    system: str = Field(..., description="Namespace for the identifier")
    value: str = Field(..., description="The identifier value")


class ContactPoint(BaseModel):
    """FHIR ContactPoint datatype."""
    system: str = Field(..., description="phone | fax | email | pager | url | sms | other")
    value: str = Field(..., description="The contact point details")
    use: Optional[str] = Field(default=None, description="home | work | temp | old | mobile")


class Address(BaseModel):
    """FHIR Address datatype."""
    line: List[str] = Field(default_factory=list, description="Street address")
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = Field(default=None, alias="postalCode")
    country: Optional[str] = None






class Patient(BaseModel):
    """FHIR Patient resource."""
    resource_type: str = Field(default="Patient", alias="resourceType")
    id: str = Field(..., description="Logical id of the patient")
    identifier: List[Identifier] = Field(default_factory=list, description="Patient identifiers")
    name: List[HumanName] = Field(..., description="A name associated with the patient")
    birth_date: Optional[str] = Field(default=None, alias="birthDate", description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(default=None, description="male | female | other | unknown")
    telecom: List[ContactPoint] = Field(default_factory=list, description="Contact details")
    address: List[Address] = Field(default_factory=list, description="Addresses")
    active: bool = Field(default=True, description="Whether patient record is active")

    class Config:
        populate_by_name = True






class CoveragePeriod(BaseModel):
    """Period of coverage."""
    start: str = Field(..., description="Start date (YYYY-MM-DD)")
    end: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")


class Coverage(BaseModel):
    """FHIR Coverage resource for insurance eligibility."""
    resource_type: str = Field(default="Coverage", alias="resourceType")
    id: str = Field(..., description="Logical id of the coverage")
    status: CoverageStatus = Field(..., description="active | cancelled | draft | entered-in-error")
    beneficiary: str = Field(..., description="Reference to Patient")
    payor: List[str] = Field(..., description="Insurance providers")
    period: Optional[CoveragePeriod] = Field(default=None, description="Coverage period")
    plan_name: Optional[str] = Field(default=None, alias="planName", description="Insurance plan name")
    copay_amount: Optional[float] = Field(default=None, alias="copayAmount", description="Copay amount in USD")
    eligible_services: List[str] = Field(default_factory=list, alias="eligibleServices", description="Covered service types")

    class Config:
        populate_by_name = True






class Slot(BaseModel):
    """FHIR Slot resource for available appointment times."""
    resource_type: str = Field(default="Slot", alias="resourceType")
    id: str = Field(..., description="Logical id of the slot")
    status: SlotStatus = Field(..., description="busy | free | busy-unavailable | busy-tentative")
    start: str = Field(..., description="Start time (ISO 8601)")
    end: str = Field(..., description="End time (ISO 8601)")
    specialty: str = Field(..., description="Medical specialty")
    practitioner_name: Optional[str] = Field(default=None, alias="practitionerName", description="Provider name")
    location: Optional[str] = Field(default=None, description="Location/facility name")

    class Config:
        populate_by_name = True






class AppointmentParticipant(BaseModel):
    """Participant in an appointment."""
    actor: str = Field(..., description="Reference to Patient or Practitioner")
    status: str = Field(default="accepted", description="accepted | declined | tentative | needs-action")


class Appointment(BaseModel):
    """FHIR Appointment resource."""
    resource_type: str = Field(default="Appointment", alias="resourceType")
    id: str = Field(..., description="Logical id of the appointment")
    status: AppointmentStatus = Field(..., description="Appointment status")
    specialty: str = Field(..., description="Medical specialty")
    reason: str = Field(..., description="Reason for appointment")
    start: str = Field(..., description="Start time (ISO 8601)")
    end: str = Field(..., description="End time (ISO 8601)")
    participant: List[AppointmentParticipant] = Field(..., description="Participants")
    location: Optional[str] = Field(default=None, description="Facility location")
    practitioner_name: Optional[str] = Field(default=None, alias="practitionerName", description="Provider name")
    created: str = Field(..., description="Creation timestamp (ISO 8601)")
    comment: Optional[str] = Field(default=None, description="Additional notes")

    class Config:
        populate_by_name = True






class SearchPatientInput(BaseModel):
    """Input schema for search_patient function."""
    name: str = Field(..., description="Patient name to search for")
    dob: Optional[str] = Field(default=None, description="Date of birth (YYYY-MM-DD)")
    identifier: Optional[str] = Field(default=None, description="Patient identifier (MRN, SSN, etc.)")


class CheckInsuranceInput(BaseModel):
    """Input schema for check_insurance_eligibility function."""
    patient_id: str = Field(..., description="Patient ID to check eligibility for")
    service_type: str = Field(..., description="Type of service (e.g., 'cardiology', 'primary-care')")


class FindSlotsInput(BaseModel):
    """Input schema for find_available_slots function."""
    specialty: str = Field(..., description="Medical specialty (e.g., 'cardiology', 'neurology')")
    start_date: str = Field(..., description="Start of date range (YYYY-MM-DD)")
    end_date: str = Field(..., description="End of date range (YYYY-MM-DD)")
    location: Optional[str] = Field(default=None, description="Preferred location/facility")


class BookAppointmentInput(BaseModel):
    """Input schema for book_appointment function."""
    patient_id: str = Field(..., description="Patient ID")
    slot_id: str = Field(..., description="Slot ID to book")
    reason: str = Field(..., description="Reason for appointment")
    dry_run: bool = Field(default=False, description="If true, validate without booking")






FUNCTION_SCHEMAS = [
    {
        "name": "search_patient",
        "description": "Search for a patient by name, date of birth, or identifier. Returns matching patient records.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Patient name to search for (first name, last name, or full name)"
                },
                "dob": {
                    "type": "string",
                    "description": "Date of birth in YYYY-MM-DD format (optional)"
                },
                "identifier": {
                    "type": "string",
                    "description": "Patient identifier such as MRN or SSN (optional)"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "check_insurance_eligibility",
        "description": "Check insurance eligibility and coverage for a patient for a specific service type.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The patient's unique identifier"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of medical service (e.g., 'cardiology', 'primary-care', 'neurology')"
                }
            },
            "required": ["patient_id", "service_type"]
        }
    },
    {
        "name": "find_available_slots",
        "description": "Find available appointment slots for a given medical specialty within a date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "description": "Medical specialty (e.g., 'cardiology', 'neurology', 'orthopedics')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for availability search (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for availability search (YYYY-MM-DD)"
                },
                "location": {
                    "type": "string",
                    "description": "Preferred facility location (optional)"
                }
            },
            "required": ["specialty", "start_date", "end_date"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for a patient at a specific slot. Supports dry-run mode to validate without booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The patient's unique identifier"
                },
                "slot_id": {
                    "type": "string",
                    "description": "The slot ID to book"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the appointment"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "If true, validate the booking without actually creating it"
                }
            },
            "required": ["patient_id", "slot_id", "reason"]
        }
    }
]
