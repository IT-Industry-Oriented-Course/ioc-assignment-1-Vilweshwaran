"""Tests for safety guardrails."""

import pytest
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.safety.guardrails import SafetyGuardrails, SafetyViolationType


class TestSafetyGuardrails:
    """Tests for safety guardrail system."""
    
    @pytest.fixture
    def guardrails(self):
        return SafetyGuardrails()
    
    
    
    def test_scheduling_request_is_safe(self, guardrails):
        """Test that scheduling requests are allowed."""
        result = guardrails.check_request(
            "Schedule a cardiology follow-up for patient Ravi Kumar next week"
        )
        assert result.is_safe == True
    
    def test_search_patient_is_safe(self, guardrails):
        """Test that patient search is allowed."""
        result = guardrails.check_request("Search for patient John Smith")
        assert result.is_safe == True
    
    def test_insurance_check_is_safe(self, guardrails):
        """Test that insurance eligibility check is allowed."""
        result = guardrails.check_request(
            "Check insurance eligibility for patient P001 for cardiology"
        )
        assert result.is_safe == True
    
    def test_find_slots_is_safe(self, guardrails):
        """Test that finding appointment slots is allowed."""
        result = guardrails.check_request(
            "Find available cardiology appointments for next week"
        )
        assert result.is_safe == True
    
    
    
    def test_diagnosis_request_blocked(self, guardrails):
        """Test that diagnosis requests are blocked."""
        result = guardrails.check_request("What's wrong with me?")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.DIAGNOSIS_REQUEST
    
    def test_diagnose_keyword_blocked(self, guardrails):
        """Test that 'diagnose' keyword triggers safety block."""
        result = guardrails.check_request("Can you diagnose my symptoms?")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.DIAGNOSIS_REQUEST
    
    def test_what_disease_blocked(self, guardrails):
        """Test that disease identification requests are blocked."""
        result = guardrails.check_request("What disease do I have?")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.DIAGNOSIS_REQUEST
    
    
    
    def test_medication_advice_blocked(self, guardrails):
        """Test that medication advice is blocked."""
        result = guardrails.check_request("Should I take aspirin for my headache?")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.MEDICAL_ADVICE
    
    def test_treatment_recommendation_blocked(self, guardrails):
        """Test that treatment recommendations are blocked."""
        result = guardrails.check_request(
            "What's the best treatment for diabetes?"
        )
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.MEDICAL_ADVICE
    
    def test_how_to_treat_blocked(self, guardrails):
        """Test that 'how to treat' requests are blocked."""
        result = guardrails.check_request("How do I treat high blood pressure?")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.MEDICAL_ADVICE
    
    
    
    def test_prescription_request_blocked(self, guardrails):
        """Test that prescription requests are blocked."""
        result = guardrails.check_request("Prescribe me some antibiotics")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.DRUG_PRESCRIPTION
    
    def test_dosage_question_blocked(self, guardrails):
        """Test that dosage questions are blocked."""
        result = guardrails.check_request(
            "What dose of ibuprofen should I take?"
        )
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.DRUG_PRESCRIPTION
    
    
    
    def test_chest_pain_emergency(self, guardrails):
        """Test that chest pain triggers emergency response."""
        result = guardrails.check_request("I'm having chest pain")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.EMERGENCY_SITUATION
        assert "emergency" in result.suggested_action.lower()
    
    def test_heart_attack_emergency(self, guardrails):
        """Test that heart attack triggers emergency response."""
        result = guardrails.check_request("I think I'm having a heart attack")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.EMERGENCY_SITUATION
    
    def test_stroke_emergency(self, guardrails):
        """Test that stroke triggers emergency response."""
        result = guardrails.check_request("My father is having a stroke")
        assert result.is_safe == False
        assert result.violation_type == SafetyViolationType.EMERGENCY_SITUATION
    
    
    
    def test_scheduling_with_specialty_is_safe(self, guardrails):
        """Test that scheduling with medical specialty is safe."""
        result = guardrails.check_request(
            "Book a neurology appointment for patient with headaches"
        )
        assert result.is_safe == True
    
    
    
    def test_valid_function_call(self, guardrails):
        """Test that valid function calls pass."""
        result = guardrails.validate_function_call(
            "search_patient",
            {"name": "John Smith"}
        )
        assert result.is_safe == True
    
    def test_invalid_function_blocked(self, guardrails):
        """Test that unknown functions are blocked."""
        result = guardrails.validate_function_call(
            "prescribe_medication",
            {"drug": "aspirin"}
        )
        assert result.is_safe == False
    
    def test_function_with_unsafe_argument(self, guardrails):
        """Test that unsafe content in arguments is blocked."""
        result = guardrails.validate_function_call(
            "book_appointment",
            {"reason": "prescribe me some medication for pain"}
        )
        assert result.is_safe == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
