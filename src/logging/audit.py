"""Audit logging for compliance and traceability."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import AUDIT_LOG_PATH


class ActionType(str, Enum):
    """Types of actions that can be logged."""
    USER_REQUEST = "user_request"
    SAFETY_CHECK = "safety_check"
    SAFETY_VIOLATION = "safety_violation"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    AGENT_RESPONSE = "agent_response"
    ERROR = "error"
    DRY_RUN = "dry_run"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str
    session_id: str
    action_type: str
    action_id: str
    user_input: Optional[str] = None
    function_name: Optional[str] = None
    function_arguments: Optional[Dict[str, Any]] = None
    function_result: Optional[Dict[str, Any]] = None
    safety_check_passed: Optional[bool] = None
    safety_violation_type: Optional[str] = None
    safety_violation_reason: Optional[str] = None
    dry_run: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class AuditLogger:
    """
    Audit logger for compliance and traceability.
    
    Logs all agent actions to a JSON Lines file for audit purposes.
    Each line is a complete JSON object representing one action.
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or AUDIT_LOG_PATH
        self.session_id = str(uuid.uuid4())[:8]
        self._entries: List[AuditEntry] = []
        
        
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _generate_action_id(self) -> str:
        """Generate a unique action ID."""
        return f"{self.session_id}-{uuid.uuid4().hex[:6]}"
    
    def _write_entry(self, entry: AuditEntry):
        """Write an entry to the log file."""
        self._entries.append(entry)
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    
    def log_user_request(self, user_input: str, metadata: Optional[dict] = None) -> str:
        """Log a user request. Returns the action ID."""
        action_id = self._generate_action_id()
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            action_type=ActionType.USER_REQUEST,
            action_id=action_id,
            user_input=user_input,
            metadata=metadata
        )
        self._write_entry(entry)
        return action_id
    
    def log_safety_check(self, user_input: str, passed: bool, 
                         violation_type: Optional[str] = None,
                         violation_reason: Optional[str] = None) -> str:
        """Log a safety check result."""
        action_id = self._generate_action_id()
        action_type = ActionType.SAFETY_CHECK if passed else ActionType.SAFETY_VIOLATION
        
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            action_type=action_type,
            action_id=action_id,
            user_input=user_input,
            safety_check_passed=passed,
            safety_violation_type=violation_type,
            safety_violation_reason=violation_reason
        )
        self._write_entry(entry)
        return action_id
    
    def log_function_call(self, function_name: str, arguments: dict,
                          dry_run: bool = False) -> str:
        """Log a function call."""
        action_id = self._generate_action_id()
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            action_type=ActionType.FUNCTION_CALL if not dry_run else ActionType.DRY_RUN,
            action_id=action_id,
            function_name=function_name,
            function_arguments=arguments,
            dry_run=dry_run
        )
        self._write_entry(entry)
        return action_id
    
    def log_function_result(self, function_name: str, result: dict,
                            dry_run: bool = False) -> str:
        """Log a function result."""
        action_id = self._generate_action_id()
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            action_type=ActionType.FUNCTION_RESULT,
            action_id=action_id,
            function_name=function_name,
            function_result=result,
            dry_run=dry_run
        )
        self._write_entry(entry)
        return action_id
    
    def log_agent_response(self, response: dict, user_input: Optional[str] = None) -> str:
        """Log the final agent response."""
        action_id = self._generate_action_id()
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            action_type=ActionType.AGENT_RESPONSE,
            action_id=action_id,
            user_input=user_input,
            function_result=response
        )
        self._write_entry(entry)
        return action_id
    
    def log_error(self, error_message: str, context: Optional[dict] = None) -> str:
        """Log an error."""
        action_id = self._generate_action_id()
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            action_type=ActionType.ERROR,
            action_id=action_id,
            error_message=error_message,
            metadata=context
        )
        self._write_entry(entry)
        return action_id
    
    def get_session_entries(self) -> List[dict]:
        """Get all entries for the current session."""
        return [e.to_dict() for e in self._entries]
    
    def get_session_summary(self) -> dict:
        """Get a summary of the current session."""
        return {
            "session_id": self.session_id,
            "total_entries": len(self._entries),
            "action_counts": self._count_actions(),
            "log_path": str(self.log_path)
        }
    
    def _count_actions(self) -> dict:
        """Count actions by type."""
        counts = {}
        for entry in self._entries:
            action_type = entry.action_type
            counts[action_type] = counts.get(action_type, 0) + 1
        return counts



_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton audit logger instance."""
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger
