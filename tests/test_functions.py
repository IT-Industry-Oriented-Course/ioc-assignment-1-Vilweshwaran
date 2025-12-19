"""Tests for healthcare functions."""

import pytest
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.functions import (
    search_patient,
    check_insurance_eligibility,
    find_available_slots,
    book_appointment
)


class TestSearchPatient:
    """Tests for search_patient function."""
    
    def test_search_by_full_name(self):
        """Test searching for a patient by full name."""
        result = search_patient("Ravi Kumar")
        
        assert result["resourceType"] == "Bundle"
        assert result["total"] >= 1
        assert len(result["entry"]) >= 1
        
        patient = result["entry"][0]["resource"]
        assert patient["id"] == "P001"
        assert patient["name"][0]["family"] == "Kumar"
    
    def test_search_by_first_name(self):
        """Test searching for a patient by first name."""
        result = search_patient("Ravi")
        
        assert result["total"] >= 1
        patient = result["entry"][0]["resource"]
        assert "Ravi" in patient["name"][0]["given"]
    
    def test_search_by_last_name(self):
        """Test searching for a patient by last name."""
        result = search_patient("Johnson")
        
        assert result["total"] >= 1
        patient = result["entry"][0]["resource"]
        assert patient["name"][0]["family"] == "Johnson"
    
    def test_search_no_results(self):
        """Test searching for a non-existent patient."""
        result = search_patient("NonexistentPatient12345")
        
        assert result["resourceType"] == "Bundle"
        assert result["total"] == 0
        assert len(result["entry"]) == 0


class TestCheckInsuranceEligibility:
    """Tests for check_insurance_eligibility function."""
    
    def test_eligible_patient(self):
        """Test checking eligibility for an eligible patient."""
        result = check_insurance_eligibility("P001", "cardiology")
        
        assert result["resourceType"] == "Coverage"
        assert result["status"] == "active"
        assert result["isEligible"] == True
        assert "cardiology" in result["eligibleServices"]
    
    def test_ineligible_service(self):
        """Test checking eligibility for a non-covered service."""
        result = check_insurance_eligibility("P002", "dermatology")
        
        assert result["isEligible"] == False
        assert "not covered" in result["eligibilityReason"].lower()
    
    def test_cancelled_coverage(self):
        """Test checking eligibility for patient with cancelled coverage."""
        result = check_insurance_eligibility("P003", "cardiology")
        
        assert result["status"] == "cancelled"
        assert result["isEligible"] == False
    
    def test_nonexistent_patient(self):
        """Test checking eligibility for a non-existent patient."""
        result = check_insurance_eligibility("INVALID", "cardiology")
        
        assert result["resourceType"] == "OperationOutcome"
        assert result["issue"][0]["severity"] == "error"


class TestFindAvailableSlots:
    """Tests for find_available_slots function."""
    
    def test_find_cardiology_slots(self):
        """Test finding available cardiology slots."""
        result = find_available_slots(
            specialty="cardiology",
            start_date="2024-12-23",
            end_date="2024-12-27"
        )
        
        assert result["resourceType"] == "Bundle"
        assert result["total"] > 0
        
        slot = result["entry"][0]["resource"]
        assert slot["resourceType"] == "Slot"
        assert slot["status"] == "free"
        assert "cardiology" in slot["specialty"].lower()
    
    def test_find_slots_with_location(self):
        """Test finding slots filtered by location."""
        result = find_available_slots(
            specialty="cardiology",
            start_date="2024-12-23",
            end_date="2024-12-27",
            location="Heart Center"
        )
        
        assert result["resourceType"] == "Bundle"
        if result["total"] > 0:
            slot = result["entry"][0]["resource"]
            assert "heart" in slot["location"].lower()
    
    def test_find_slots_unknown_specialty(self):
        """Test finding slots for unknown specialty returns empty."""
        result = find_available_slots(
            specialty="unknown_specialty_xyz",
            start_date="2024-12-23",
            end_date="2024-12-27"
        )
        
        assert result["total"] == 0


class TestBookAppointment:
    """Tests for book_appointment function."""
    
    def test_book_appointment_dry_run(self):
        """Test booking appointment in dry-run mode."""
        
        slots = find_available_slots(
            specialty="cardiology",
            start_date="2024-12-23",
            end_date="2024-12-27"
        )
        slot_id = slots["entry"][0]["resource"]["id"]
        
        
        result = book_appointment(
            patient_id="P001",
            slot_id=slot_id,
            reason="Cardiology follow-up",
            dry_run=True
        )
        
        assert result["success"] == True
        assert result["appointment"]["status"] == "proposed"
        assert result["appointment"]["_dryRun"] == True
    
    def test_book_appointment_invalid_patient(self):
        """Test booking with invalid patient ID."""
        result = book_appointment(
            patient_id="INVALID_PATIENT",
            slot_id="SLOT-CARD-20241223-001",
            reason="Follow-up"
        )
        
        assert result["resourceType"] == "OperationOutcome"
        assert result["issue"][0]["severity"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
