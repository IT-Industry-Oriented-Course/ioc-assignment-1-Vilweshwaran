"""
Clinical Workflow Agent - Main LLM Agent with Hugging Face.

This agent interprets natural-language clinical requests and safely 
interacts with healthcare APIs to perform validated workflow actions.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from huggingface_hub import InferenceClient

from .functions import get_registry
from .functions.schemas import FUNCTION_SCHEMAS
from .safety.guardrails import SafetyGuardrails, get_guardrails, SafetyCheckResult
from .logging.audit import AuditLogger, get_audit_logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import HF_API_TOKEN, HF_MODEL


@dataclass
class AgentResponse:
    """Response from the clinical workflow agent."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    function_calls: Optional[List[Dict[str, Any]]] = None
    safety_refused: bool = False
    dry_run: bool = False
    audit_session_id: Optional[str] = None


class ClinicalWorkflowAgent:
    """
    LLM-powered agent for clinical workflow automation.
    
    This agent:
    1. Accepts natural language input from clinicians/admins
    2. Applies safety guardrails to prevent unsafe actions
    3. Determines which functions to call using LLM
    4. Validates inputs against FHIR-style schemas
    5. Executes functions and returns structured outputs
    6. Logs all actions for compliance
    """
    
    SYSTEM_PROMPT = """You are a clinical workflow automation agent. Your role is to help healthcare staff with administrative tasks like:
- Searching for patients
- Checking insurance eligibility
- Finding available appointment slots
- Booking appointments

You are NOT allowed to:
- Provide medical diagnoses
- Give medical advice
- Recommend treatments or medications
- Make medical decisions

You MUST use the provided functions to complete tasks. Always respond with function calls when appropriate.

Available functions:
1. search_patient(name, dob?, identifier?) - Search for a patient by name
2. check_insurance_eligibility(patient_id, service_type) - Check insurance coverage
3. find_available_slots(specialty, start_date, end_date, location?) - Find open appointment slots
4. book_appointment(patient_id, slot_id, reason, dry_run?) - Book an appointment

When the user asks to schedule an appointment, you should:
1. First search for the patient
2. Check their insurance eligibility for the specialty
3. Find available slots for the requested specialty and time period
4. Book the appointment using the patient ID and a selected slot ID

Always respond with structured function calls. Never make up data - only use data returned from function calls."""

    def __init__(self, hf_token: Optional[str] = None, model: Optional[str] = None, dry_run: bool = False):
        """
        Initialize the clinical workflow agent.
        
        Args:
            hf_token: Hugging Face API token (defaults to env variable)
            model: Hugging Face model to use (defaults to Mistral-7B-Instruct)
            dry_run: If True, all operations are in dry-run mode
        """
        self.hf_token = hf_token or HF_API_TOKEN
        self.model = model or HF_MODEL
        self.dry_run = dry_run
        
        
        self.registry = get_registry()
        self.guardrails = get_guardrails()
        self.audit_logger = get_audit_logger()
        
        
        self.client = None
        if self.hf_token:
            try:
                self.client = InferenceClient(token=self.hf_token)
            except Exception as e:
                print(f"Warning: Could not initialize HF client: {e}")
    
    def _create_function_calling_prompt(self, user_input: str, context: Optional[str] = None) -> str:
        """Create a prompt for function calling."""
        functions_desc = "\n".join([
            f"- {f['name']}: {f['description']}"
            for f in FUNCTION_SCHEMAS
        ])
        
        
        today = datetime.now()
        next_week_start = today + timedelta(days=(7 - today.weekday()))
        next_week_end = next_week_start + timedelta(days=4)  
        
        prompt = f"""{self.SYSTEM_PROMPT}

Today's date: {today.strftime('%Y-%m-%d')}
Next week date range: {next_week_start.strftime('%Y-%m-%d')} to {next_week_end.strftime('%Y-%m-%d')}

Available functions:
{functions_desc}

{f"Previous context: {context}" if context else ""}

User request: {user_input}

Respond with a JSON object containing the function calls to make. Format:
{{"function_calls": [{{"name": "function_name", "arguments": {{"arg1": "value1"}}}}]}}

If you need to call multiple functions, include them all in the array in order of execution.
Only respond with the JSON object, no other text."""
        
        return prompt
    
    def _parse_function_calls(self, llm_response: str) -> List[Dict[str, Any]]:
        """Parse function calls from LLM response."""
        
        try:
            
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                parsed = json.loads(json_match.group())
                if "function_calls" in parsed:
                    return parsed["function_calls"]
                elif "name" in parsed:
                    
                    return [parsed]
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _extract_intent_without_llm(self, user_input: str) -> List[Dict[str, Any]]:
        """
        Extract function calls from user input using rule-based parsing.
        Used when LLM is not available.
        """
        user_lower = user_input.lower()
        function_calls = []
        
        
        today = datetime.now()
        next_week_start = today + timedelta(days=(7 - today.weekday()))
        next_week_end = next_week_start + timedelta(days=4)
        
        
        date_match = re.search(r'(\d{1,2})-(\d{1,2})', user_input)
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = today.year if month >= today.month else today.year + 1
            try:
                specific_date = datetime(year, month, day)
                next_week_start = specific_date
                next_week_end = specific_date + timedelta(days=1)
            except ValueError:
                pass
        
        
        patient_name = None
        
        
        name_patterns = [
            
            r"i\s+am\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
            
            r"patient\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
            
            r"for\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
            
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                
                skip_words = ["appointment", "cardiology", "neurology", "insurance", "book", "schedule", "check", "my", "an", "the", "and", "for"]
                if name.lower() not in skip_words and len(name) > 2:
                    
                    patient_name = name.title()
                    break
        
        
        if patient_name:
            
            known_patients = {
                "ravikumar": "Ravi Kumar",
                "ravi kumar": "Ravi Kumar", 
                "raviakumar": "Ravi Kumar",
                "sarahjohnson": "Sarah Johnson",
                "sarah johnson": "Sarah Johnson",
                "anitapatel": "Anita Patel",
                "anita patel": "Anita Patel",
            }
            patient_name_lower = patient_name.lower().replace(" ", "")
            for known, proper in known_patients.items():
                if known.replace(" ", "") == patient_name_lower:
                    patient_name = proper
                    break
        
        
        specialty = None
        specialties = ["cardiology", "neurology", "orthopedics", "primary-care"]
        for s in specialties:
            if s.replace("-", " ") in user_lower or s.replace("-", "") in user_lower:
                specialty = s
                break
        
        
        reason = "Follow-up appointment"
        if "follow" in user_lower and "up" in user_lower:
            reason = f"{specialty.title() if specialty else 'Medical'} follow-up"
        elif specialty:
            reason = f"{specialty.title()} consultation"
        
        
        wants_search = patient_name is not None
        wants_insurance = "insurance" in user_lower or "eligibility" in user_lower or "coverage" in user_lower or "eligible" in user_lower
        wants_slots = "schedule" in user_lower or "appointment" in user_lower or "book" in user_lower or "available" in user_lower
        wants_book = "book" in user_lower or "schedule" in user_lower or "appoint" in user_lower
        
        
        if wants_search and patient_name:
            function_calls.append({
                "name": "search_patient",
                "arguments": {"name": patient_name}
            })
        
        
        
        service_type = specialty if specialty else "primary-care"
        
        if wants_insurance or wants_book:
            function_calls.append({
                "name": "check_insurance_eligibility",
                "arguments": {
                    "patient_id": "{{patient_id}}",
                    "service_type": service_type
                }
            })
        
        
        if wants_slots or wants_book:
            function_calls.append({
                "name": "find_available_slots",
                "arguments": {
                    "specialty": service_type,
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                }
            })
        
        
        if wants_book:
            function_calls.append({
                "name": "book_appointment",
                "arguments": {
                    "patient_id": "{{patient_id}}",
                    "slot_id": "{{slot_id}}",
                    "reason": reason or f"{service_type.replace('-', ' ').title()} Consultation"
                }
            })
        
        return function_calls
    
    def _get_function_calls_from_llm(self, user_input: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.client:
            
            return self._extract_intent_without_llm(user_input)
        
        prompt = self._create_function_calling_prompt(user_input, context)
        
        try:
            response = self.client.text_generation(
                prompt,
                model=self.model,
                max_new_tokens=500,
                temperature=0.1,
                return_full_text=False
            )
            return self._parse_function_calls(response)
        except Exception as e:
            self.audit_logger.log_error(f"LLM call failed: {str(e)}")
            
            return self._extract_intent_without_llm(user_input)
    
    def process_request(self, user_input: str, dry_run: Optional[bool] = None) -> AgentResponse:
        """
        Process a natural language request from a clinician/admin.
        
        Args:
            user_input: Natural language request
            dry_run: Override agent's dry_run setting
        
        Returns:
            AgentResponse with results or refusal
        """
        use_dry_run = dry_run if dry_run is not None else self.dry_run
        
        
        self.audit_logger.log_user_request(user_input, {"dry_run": use_dry_run})
        
        
        safety_result = self.guardrails.check_request(user_input)
        self.audit_logger.log_safety_check(
            user_input,
            passed=safety_result.is_safe,
            violation_type=safety_result.violation_type.value if safety_result.violation_type else None,
            violation_reason=safety_result.reason
        )
        
        if not safety_result.is_safe:
            response = AgentResponse(
                success=False,
                message=safety_result.reason,
                safety_refused=True,
                data={
                    "violation_type": safety_result.violation_type.value if safety_result.violation_type else None,
                    "suggested_action": safety_result.suggested_action
                },
                audit_session_id=self.audit_logger.session_id
            )
            self.audit_logger.log_agent_response({"refused": True, "reason": safety_result.reason})
            return response
        
        
        function_calls = self._get_function_calls_from_llm(user_input)
        
        if not function_calls:
            response = AgentResponse(
                success=False,
                message="I couldn't determine which actions to take from your request. Please be more specific about what you'd like me to do (e.g., 'Schedule a cardiology appointment for patient John Smith next week').",
                audit_session_id=self.audit_logger.session_id
            )
            self.audit_logger.log_agent_response({"no_actions": True})
            return response
        
        
        results = []
        patient_id = None  
        slot_id = None  
        
        for fc in function_calls:
            func_name = fc.get("name")
            arguments = fc.get("arguments", {})
            
            
            if "{{patient_id}}" in str(arguments):
                if patient_id:
                    arguments = json.loads(
                        json.dumps(arguments).replace("{{patient_id}}", patient_id)
                    )
                else:
                    continue  
            
            
            if "{{slot_id}}" in str(arguments):
                if slot_id:
                    arguments = json.loads(
                        json.dumps(arguments).replace("{{slot_id}}", slot_id)
                    )
                else:
                    continue  
            
            
            if func_name == "book_appointment":
                arguments["dry_run"] = use_dry_run
            
            
            safety_check = self.guardrails.validate_function_call(func_name, arguments)
            if not safety_check.is_safe:
                self.audit_logger.log_error(f"Function call blocked: {safety_check.reason}")
                continue
            
            
            self.audit_logger.log_function_call(func_name, arguments, use_dry_run)
            
            result = self.registry.execute(func_name, arguments)
            
            self.audit_logger.log_function_result(func_name, result, use_dry_run)
            
            results.append({
                "function": func_name,
                "arguments": arguments,
                "result": result
            })
            
            
            if func_name == "search_patient" and "entry" in result:
                entries = result.get("entry", [])
                if entries:
                    patient_id = entries[0].get("resource", {}).get("id")
            
            
            if func_name == "find_available_slots" and "entry" in result:
                entries = result.get("entry", [])
                if entries:
                    slot_id = entries[0].get("resource", {}).get("id")
        
        
        response = AgentResponse(
            success=True,
            message=f"Successfully executed {len(results)} function(s)." + 
                   (" [DRY RUN - No changes made]" if use_dry_run else ""),
            data={"results": results},
            function_calls=function_calls,
            dry_run=use_dry_run,
            audit_session_id=self.audit_logger.session_id
        )
        
        self.audit_logger.log_agent_response({
            "success": True,
            "function_count": len(results),
            "dry_run": use_dry_run
        })
        
        return response
    
    def get_available_functions(self) -> List[dict]:
        """Get descriptions of available functions."""
        return FUNCTION_SCHEMAS
    
    def get_audit_summary(self) -> dict:
        """Get summary of audit log for current session."""
        return self.audit_logger.get_session_summary()
