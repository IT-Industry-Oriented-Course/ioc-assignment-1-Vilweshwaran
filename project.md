Design and Build a Function-Calling LLM Agent for Clinical Workflow Automation
________________________________________
Industry Context (Why this matters)
Healthcare is drowning in unstructured data (clinical notes, discharge summaries) while its operational systems are rigid, API-driven, and regulated. Humans currently act as glue between these worlds. That’s expensive, slow, and error-prone.
Your job is to build an LLM agent that acts as an intelligent coordinator, not a hallucinating oracle.
________________________________________
Core Learning Objective
By completing this assignment, the student will demonstrate the ability to:
●	Design function schemas aligned with real healthcare APIs
●	Implement deterministic tool execution via function calling
●	Enforce safety, validation, and auditability
●	Build an agent that reasons, then acts, not one that freewheels text
________________________________________
High-Level Problem Statement
Build a function-calling LLM agent that interprets natural-language clinical or operational requests and safely interacts with external healthcare APIs to perform validated actions.
The agent must not directly answer medical questions.
It must act as a workflow orchestrator.
________________________________________
Functional Requirements (Non-Negotiable)
The agent must:
1.	Accept natural language input from a clinician or admin
2.	Decide which function(s) to call (no human intervention)
3.	Validate inputs against schemas (FHIR-style objects)
4.	Call external APIs (real or sandbox)
5.	Return structured, auditable outputs
6.	Log every action for compliance
________________________________________
What the Agent Is NOT Allowed To Do
●	No diagnosis
●	No medical advice
●	No free-text hallucinated data
●	No hidden tool calls
If the agent cannot act safely, it must refuse with justification.
________________________________________
POC: Clinical Appointment & Care Coordination Agent
Problem
Clinicians waste time juggling appointment systems, patient eligibility, and follow-ups.
Agent Capabilities
●	Parse requests like:
“Schedule a cardiology follow-up for patient Ravi Kumar next week and check insurance eligibility”
●	Call external functions:
○	search_patient()
○	check_insurance_eligibility()
○	find_available_slots()
○	book_appointment()
●	Return a confirmed appointment object, not prose
________________________________________
Technology Constraints
●	Must use function calling
●	Must expose JSON schemas
●	Must integrate at least one external APIs
●	Must support dry-run mode
●	Must be reproducible locally