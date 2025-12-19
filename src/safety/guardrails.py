"""Safety guardrails to prevent unsafe agent behavior."""

import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class SafetyViolationType(str, Enum):
    """Types of safety violations."""
    DIAGNOSIS_REQUEST = "diagnosis_request"
    MEDICAL_ADVICE = "medical_advice"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"
    DRUG_PRESCRIPTION = "drug_prescription"
    EMERGENCY_SITUATION = "emergency_situation"
    PERSONAL_HEALTH_QUESTION = "personal_health_question"


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    is_safe: bool
    violation_type: Optional[SafetyViolationType] = None
    reason: Optional[str] = None
    suggested_action: Optional[str] = None


class SafetyGuardrails:
    """
    Safety guardrails to ensure the agent doesn't:
    - Provide diagnosis
    - Give medical advice
    - Generate hallucinated data
    - Make hidden tool calls
    """
    
    
    DIAGNOSIS_PATTERNS = [
        r"\bwhat('s| is) wrong with\b",
        r"\bdiagnos(e|is)\b",
        r"\bwhat (do i|does .+) have\b",
        r"\bwhat (disease|condition|illness)\b",
        r"\bam i (sick|ill)\b",
        r"\bdo i have\b.*(disease|cancer|diabetes|infection)",
        r"\bcould (this|it|i) be\b",
        r"\bwhat are my symptoms of\b",
        r"\bidentify (the|my) (disease|condition|illness)\b",
    ]
    
    
    MEDICAL_ADVICE_PATTERNS = [
        r"\bshould i (take|use|stop|continue)\b",
        r"\bwhat (medication|medicine|drug|treatment) should\b",
        r"\bhow (to|do i) treat\b",
        r"\brecommend.*(treatment|medication|therapy)\b",
        r"\bwhat('s| is) the best (treatment|cure|remedy)\b",
        r"\badvice (for|on|about).*(health|medical|symptom)\b",
        r"\bis it (safe|okay|ok) to\b.*(take|use|stop)\b",
        r"\bcan i (take|use|combine)\b.*(medicine|medication|drug)\b",
        
        r"\bi have\b.*(what (to do|should i do)|help)\b",
        r"\bi('m| am) (having|feeling|experiencing)\b.*(what|help)\b",
        r"\bwhat (to do|should i do)\b.*(pain|ache|fever|cold|cough|headache|symptom)\b",
        r"\bwhat is the (remedy|cure|solution|fix)\b",
        r"\bhow (to|do i|can i) (cure|fix|heal|stop|relieve|get rid of)\b",
        r"\bremedy for\b",
        r"\bcure for\b",
        r"\btreatment for\b",
        r"\bhome (remedy|remedies|treatment)\b",
        r"\bwhat helps (with|for)\b.*(pain|ache|fever|cold|cough)\b",
        r"\bhow to (stop|relieve|reduce|ease)\b.*(pain|ache|fever|symptom)\b",
        
        r"\b(headache|pain|fever|nausea|cough|cold|flu|sick|unwell)\b.*\b(what|how|help|remedy|cure)\b",
        r"\bfeeling\b.*(sick|unwell|bad|ill)\b.*\b(what|how|help)\b",
    ]
    
    
    TREATMENT_PATTERNS = [
        r"\bprescrib(e|ption)\b",
        r"\bwhat dose\b",
        r"\bhow much.*(medicine|medication|drug)\b",
        r"\brefill (my|a) (prescription|medication)\b",
        r"\border.*(medicine|medication|drug)\b",
    ]
    
    
    EMERGENCY_PATTERNS = [
        r"\bheart attack\b",
        r"\bstroke\b",
        r"\bcan't breathe\b",
        r"\bchest pain\b",
        r"\bsuicid(e|al)\b",
        r"\bsevere bleeding\b",
        r"\bunconscious\b",
        r"\bseizure\b",
        r"\boverdos(e|ing)\b",
    ]
    
    
    VALID_ACTION_PATTERNS = [
        r"\b(schedule|book|cancel|reschedule).*(appointment|visit)\b",
        r"\b(check|verify).*(insurance|eligibility|coverage)\b",
        r"\b(find|search|look up).*(patient|slot|availability)\b",
        r"\b(available|open).*(slot|time|appointment)\b",
        r"\bfollow[- ]?up\b",
        r"\b(cardiology|neurology|orthopedics|primary[- ]care)\b",
    ]
    
    def __init__(self):
        
        self._diagnosis_re = [re.compile(p, re.IGNORECASE) for p in self.DIAGNOSIS_PATTERNS]
        self._advice_re = [re.compile(p, re.IGNORECASE) for p in self.MEDICAL_ADVICE_PATTERNS]
        self._treatment_re = [re.compile(p, re.IGNORECASE) for p in self.TREATMENT_PATTERNS]
        self._emergency_re = [re.compile(p, re.IGNORECASE) for p in self.EMERGENCY_PATTERNS]
        self._valid_re = [re.compile(p, re.IGNORECASE) for p in self.VALID_ACTION_PATTERNS]
    
    def _matches_any(self, text: str, patterns: List[re.Pattern]) -> bool:
        """Check if text matches any of the patterns."""
        return any(p.search(text) for p in patterns)
    
    def _is_valid_workflow_request(self, text: str) -> bool:
        """Check if this is a valid workflow/scheduling request."""
        return self._matches_any(text, self._valid_re)
    
    def check_request(self, user_input: str) -> SafetyCheckResult:
        """
        Check if a user request is safe for the agent to process.
        
        Args:
            user_input: The user's natural language request
        
        Returns:
            SafetyCheckResult with safety status and details
        """
        text = user_input.strip()
        
        
        if self._matches_any(text, self._emergency_re):
            return SafetyCheckResult(
                is_safe=False,
                violation_type=SafetyViolationType.EMERGENCY_SITUATION,
                reason="This appears to be a medical emergency. I cannot assist with emergency medical situations.",
                suggested_action="Please call emergency services (911) or go to the nearest emergency room immediately."
            )
        
        
        if self._matches_any(text, self._diagnosis_re):
            
            if self._is_valid_workflow_request(text):
                pass  
            else:
                return SafetyCheckResult(
                    is_safe=False,
                    violation_type=SafetyViolationType.DIAGNOSIS_REQUEST,
                    reason="I cannot provide medical diagnoses. I am a workflow automation agent, not a diagnostic tool.",
                    suggested_action="Please consult with a healthcare provider for diagnosis. I can help you schedule an appointment."
                )
        
        
        if self._matches_any(text, self._advice_re):
            if self._is_valid_workflow_request(text):
                pass  
            else:
                return SafetyCheckResult(
                    is_safe=False,
                    violation_type=SafetyViolationType.MEDICAL_ADVICE,
                    reason="I cannot provide medical advice or treatment recommendations.",
                    suggested_action="Please consult with a healthcare provider for medical advice. I can help you schedule an appointment."
                )
        
        
        if self._matches_any(text, self._treatment_re):
            return SafetyCheckResult(
                is_safe=False,
                violation_type=SafetyViolationType.DRUG_PRESCRIPTION,
                reason="I cannot prescribe medications or recommend treatments.",
                suggested_action="Please contact your healthcare provider or pharmacist for prescription-related questions."
            )
        
        
        return SafetyCheckResult(is_safe=True)
    
    def validate_function_call(self, function_name: str, arguments: dict) -> SafetyCheckResult:
        """
        Validate that a function call is appropriate and not attempting to
        bypass safety checks.
        
        Args:
            function_name: Name of the function being called
            arguments: Arguments to the function
        
        Returns:
            SafetyCheckResult with validation status
        """
        allowed_functions = {
            "search_patient",
            "check_insurance_eligibility",
            "find_available_slots",
            "book_appointment"
        }
        
        if function_name not in allowed_functions:
            return SafetyCheckResult(
                is_safe=False,
                reason=f"Function '{function_name}' is not an allowed workflow function.",
                suggested_action=f"Available functions: {', '.join(allowed_functions)}"
            )
        
        
        for key, value in arguments.items():
            if isinstance(value, str):
                
                check = self.check_request(value)
                if not check.is_safe and check.violation_type in [
                    SafetyViolationType.DIAGNOSIS_REQUEST,
                    SafetyViolationType.MEDICAL_ADVICE,
                    SafetyViolationType.DRUG_PRESCRIPTION
                ]:
                    return SafetyCheckResult(
                        is_safe=False,
                        violation_type=check.violation_type,
                        reason=f"Argument '{key}' contains unsafe content: {check.reason}",
                        suggested_action=check.suggested_action
                    )
        
        return SafetyCheckResult(is_safe=True)



_guardrails: Optional[SafetyGuardrails] = None


def get_guardrails() -> SafetyGuardrails:
    """Get the singleton guardrails instance."""
    global _guardrails
    if _guardrails is None:
        _guardrails = SafetyGuardrails()
    return _guardrails
