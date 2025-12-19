"""Mock Healthcare API with sample patient and appointment data."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid






MOCK_PATIENTS: Dict[str, dict] = {
    "P001": {
        "resourceType": "Patient",
        "id": "P001",
        "identifier": [
            {"system": "urn:oid:hospital-mrn", "value": "MRN-2024-001"}
        ],
        "name": [{"family": "Kumar", "given": ["Ravi"]}],
        "birthDate": "1985-03-15",
        "gender": "male",
        "telecom": [
            {"system": "phone", "value": "+91-9876543210", "use": "mobile"},
            {"system": "email", "value": "ravi.kumar@email.com", "use": "home"}
        ],
        "address": [
            {"line": ["123 MG Road"], "city": "Bangalore", "state": "Karnataka", "postalCode": "560001", "country": "India"}
        ],
        "active": True
    },
    "P002": {
        "resourceType": "Patient",
        "id": "P002",
        "identifier": [
            {"system": "urn:oid:hospital-mrn", "value": "MRN-2024-002"}
        ],
        "name": [{"family": "Johnson", "given": ["Sarah", "Marie"]}],
        "birthDate": "1990-07-22",
        "gender": "female",
        "telecom": [
            {"system": "phone", "value": "+1-555-0102", "use": "mobile"},
            {"system": "email", "value": "sarah.johnson@email.com", "use": "home"}
        ],
        "address": [
            {"line": ["456 Oak Street"], "city": "Boston", "state": "MA", "postalCode": "02101", "country": "USA"}
        ],
        "active": True
    },
    "P003": {
        "resourceType": "Patient",
        "id": "P003",
        "identifier": [
            {"system": "urn:oid:hospital-mrn", "value": "MRN-2024-003"}
        ],
        "name": [{"family": "Patel", "given": ["Anita"]}],
        "birthDate": "1978-11-30",
        "gender": "female",
        "telecom": [
            {"system": "phone", "value": "+91-8765432109", "use": "mobile"}
        ],
        "address": [
            {"line": ["789 Gandhi Nagar"], "city": "Mumbai", "state": "Maharashtra", "postalCode": "400001", "country": "India"}
        ],
        "active": True
    }
}






MOCK_COVERAGES: Dict[str, dict] = {
    "P001": {
        "resourceType": "Coverage",
        "id": "COV-001",
        "status": "active",
        "beneficiary": "Patient/P001",
        "payor": ["Star Health Insurance"],
        "period": {"start": "2024-01-01", "end": "2024-12-31"},
        "planName": "Family Floater Premium",
        "copayAmount": 500.00,
        "eligibleServices": ["cardiology", "primary-care", "orthopedics", "neurology", "dermatology"]
    },
    "P002": {
        "resourceType": "Coverage",
        "id": "COV-002",
        "status": "active",
        "beneficiary": "Patient/P002",
        "payor": ["Blue Cross Blue Shield"],
        "period": {"start": "2024-01-01", "end": "2024-12-31"},
        "planName": "PPO Gold Plan",
        "copayAmount": 30.00,
        "eligibleServices": ["primary-care", "cardiology", "mental-health"]
    },
    "P003": {
        "resourceType": "Coverage",
        "id": "COV-003",
        "status": "cancelled",
        "beneficiary": "Patient/P003",
        "payor": ["ICICI Lombard"],
        "period": {"start": "2023-01-01", "end": "2023-12-31"},
        "planName": "Individual Health Plan",
        "copayAmount": 1000.00,
        "eligibleServices": []
    }
}






MOCK_PRACTITIONERS = {
    "cardiology": [
        {"id": "DR001", "name": "Dr. Suresh Reddy", "location": "City Heart Center"},
        {"id": "DR002", "name": "Dr. Emily Chen", "location": "Metro Cardiology Clinic"}
    ],
    "neurology": [
        {"id": "DR003", "name": "Dr. Amit Sharma", "location": "Brain & Spine Institute"},
        {"id": "DR004", "name": "Dr. Lisa Park", "location": "Neurology Associates"}
    ],
    "orthopedics": [
        {"id": "DR005", "name": "Dr. Rajesh Gupta", "location": "Joint Care Hospital"},
        {"id": "DR006", "name": "Dr. Michael Brown", "location": "Sports Medicine Center"}
    ],
    "primary-care": [
        {"id": "DR007", "name": "Dr. Priya Menon", "location": "Family Health Clinic"},
        {"id": "DR008", "name": "Dr. James Wilson", "location": "Community Medical Center"}
    ]
}






BOOKED_APPOINTMENTS: Dict[str, dict] = {}
BOOKED_SLOT_IDS: set = set()






class MockHealthcareAPI:
    """Mock Healthcare API simulating FHIR-compliant responses."""

    @staticmethod
    def search_patients(name: str, dob: Optional[str] = None, identifier: Optional[str] = None) -> List[dict]:
        """Search for patients matching the criteria."""
        results = []
        name_lower = name.lower()
        
        for patient_id, patient in MOCK_PATIENTS.items():
            
            name_matched = False
            for name_entry in patient.get("name", []):
                full_name = f"{' '.join(name_entry.get('given', []))} {name_entry.get('family', '')}".lower()
                family_name = name_entry.get('family', '').lower()
                given_names = [g.lower() for g in name_entry.get('given', [])]
                
                if name_lower in full_name or name_lower in family_name or name_lower in given_names:
                    name_matched = True
                    break
            
            if not name_matched:
                continue
            
            
            if dob and patient.get("birthDate") != dob:
                continue
            
            
            if identifier:
                id_matched = False
                for ident in patient.get("identifier", []):
                    if identifier.lower() in ident.get("value", "").lower():
                        id_matched = True
                        break
                if not id_matched:
                    continue
            
            results.append(patient)
        
        return results

    @staticmethod
    def get_coverage(patient_id: str, service_type: str) -> Optional[dict]:
        """Get insurance coverage for a patient."""
        coverage = MOCK_COVERAGES.get(patient_id)
        if not coverage:
            return None
        
        
        result = coverage.copy()
        result["serviceRequested"] = service_type
        result["isEligible"] = service_type.lower() in [s.lower() for s in coverage.get("eligibleServices", [])]
        
        if coverage.get("status") != "active":
            result["isEligible"] = False
            result["eligibilityReason"] = "Coverage is not active"
        elif not result["isEligible"]:
            result["eligibilityReason"] = f"Service type '{service_type}' is not covered under this plan"
        else:
            result["eligibilityReason"] = "Patient is eligible for this service"
        
        return result

    @staticmethod
    def find_slots(specialty: str, start_date: str, end_date: str, location: Optional[str] = None) -> List[dict]:
        """Find available appointment slots."""
        specialty_lower = specialty.lower()
        practitioners = MOCK_PRACTITIONERS.get(specialty_lower, [])
        
        if not practitioners:
            return []
        
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return []
        
        slots = []
        current = start
        slot_counter = 1
        
        while current <= end:
            
            if current.weekday() < 5:  
                for practitioner in practitioners:
                    
                    if location and location.lower() not in practitioner["location"].lower():
                        continue
                    
                    
                    for hour in [9, 11, 14, 16]:
                        slot_id = f"SLOT-{specialty_lower[:4].upper()}-{current.strftime('%Y%m%d')}-{slot_counter:03d}"
                        
                        
                        if slot_id in BOOKED_SLOT_IDS:
                            slot_counter += 1
                            continue
                        
                        slot_start = current.replace(hour=hour, minute=0, second=0)
                        slot_end = slot_start + timedelta(minutes=30)
                        
                        slots.append({
                            "resourceType": "Slot",
                            "id": slot_id,
                            "status": "free",
                            "start": slot_start.isoformat(),
                            "end": slot_end.isoformat(),
                            "specialty": specialty,
                            "practitionerName": practitioner["name"],
                            "practitionerId": practitioner["id"],
                            "location": practitioner["location"]
                        })
                        slot_counter += 1
            
            current += timedelta(days=1)
        
        
        return slots[:10]

    @staticmethod
    def book_slot(patient_id: str, slot_id: str, reason: str, dry_run: bool = False) -> dict:
        """Book an appointment slot."""
        
        if patient_id not in MOCK_PATIENTS:
            return {
                "success": False,
                "error": f"Patient '{patient_id}' not found"
            }
        
        
        if slot_id in BOOKED_SLOT_IDS:
            return {
                "success": False,
                "error": f"Slot '{slot_id}' is no longer available"
            }
        
        
        parts = slot_id.split("-")
        if len(parts) < 4:
            return {
                "success": False,
                "error": f"Invalid slot ID format: '{slot_id}'"
            }
        
        specialty_code = parts[1].lower()
        specialty_map = {"card": "cardiology", "neur": "neurology", "orth": "orthopedics", "prim": "primary-care"}
        specialty = specialty_map.get(specialty_code, "general")
        
        
        practitioners = MOCK_PRACTITIONERS.get(specialty, MOCK_PRACTITIONERS.get("primary-care", []))
        practitioner = practitioners[0] if practitioners else {"name": "Dr. Unknown", "location": "Main Clinic"}
        
        
        appointment_id = f"APT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()
        
        
        try:
            date_str = parts[2]
            slot_date = datetime.strptime(date_str, "%Y%m%d")
            slot_start = slot_date.replace(hour=9, minute=0)  
            slot_end = slot_start + timedelta(minutes=30)
        except:
            slot_start = now + timedelta(days=7)
            slot_end = slot_start + timedelta(minutes=30)
        
        appointment = {
            "resourceType": "Appointment",
            "id": appointment_id,
            "status": "booked" if not dry_run else "proposed",
            "specialty": specialty,
            "reason": reason,
            "start": slot_start.isoformat(),
            "end": slot_end.isoformat(),
            "participant": [
                {"actor": f"Patient/{patient_id}", "status": "accepted"},
                {"actor": f"Practitioner/{practitioner.get('id', 'unknown')}", "status": "accepted"}
            ],
            "location": practitioner.get("location", "Main Clinic"),
            "practitionerName": practitioner.get("name", "Dr. Unknown"),
            "created": now.isoformat(),
            "comment": None
        }
        
        if dry_run:
            appointment["_dryRun"] = True
            appointment["_message"] = "This is a dry-run. Appointment was NOT actually booked."
        else:
            
            BOOKED_SLOT_IDS.add(slot_id)
            BOOKED_APPOINTMENTS[appointment_id] = appointment
        
        return {
            "success": True,
            "appointment": appointment,
            "message": "Appointment successfully booked" if not dry_run else "Dry-run validation successful"
        }



mock_api = MockHealthcareAPI()
