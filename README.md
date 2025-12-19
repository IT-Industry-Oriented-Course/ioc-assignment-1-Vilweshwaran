# Clinical Workflow Agent

A function-calling LLM agent for clinical workflow automation. This agent interprets natural-language clinical requests and safely interacts with healthcare APIs to perform validated actions.

## 📁 Project Structure

```
Ioc-1911/
├── app/                          # Application Entry Points
│   ├── __init__.py
│   ├── cli.py                    # Command Line Interface
│   └── streamlit_ui.py           # Streamlit Web Interface
│
├── src/                          # Core Source Code
│   ├── __init__.py
│   ├── agent.py                  # Main LLM Agent
│   │
│   ├── functions/                # Healthcare Functions
│   │   ├── __init__.py
│   │   ├── schemas.py            # FHIR-style JSON Schemas
│   │   ├── registry.py           # Function Registry
│   │   ├── patient.py            # search_patient()
│   │   ├── insurance.py          # check_insurance_eligibility()
│   │   └── appointments.py       # find_available_slots(), book_appointment()
│   │
│   ├── sandbox/                  # Mock Healthcare API
│   │   ├── __init__.py
│   │   └── mock_api.py           # Sample Data & API Simulation
│   │
│   ├── safety/                   # Safety Guardrails
│   │   ├── __init__.py
│   │   ├── guardrails.py         # Request Safety Checks
│   │   └── validators.py         # Input Validation
│   │
│   └── logging/                  # Audit Logging
│       ├── __init__.py
│       └── audit.py              # Compliance Logging
│
├── config/                       # Configuration
│   ├── __init__.py
│   └── settings.py               # Environment Settings
│
├── tests/                        # Test Suite
│   ├── __init__.py
│   ├── test_functions.py         # Function Unit Tests
│   ├── test_safety.py            # Safety Guardrail Tests
│   └── test_agent.py             # Integration Tests
│
├── logs/                         # Audit Logs (auto-created)
│   └── audit.jsonl
│
├── run.py                        # 🚀 Main Entry Point
├── main.py                       # Legacy CLI (backward compatible)
├── app.py                        # Legacy Streamlit (backward compatible)
├── requirements.txt              # Python Dependencies
├── .env.example                  # Environment Template
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd Ioc-1911

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Running the Application

#### Option 1: Unified Entry Point (Recommended)

```bash
# CLI Mode - Single request
python run.py "Schedule a cardiology follow-up for patient Ravi Kumar"

# CLI Mode - Interactive
python run.py --interactive

# Web Mode - Streamlit UI
python run.py --mode web
```

#### Option 2: Direct Module Execution

```bash
# CLI
python -m app.cli "Search for patient Ravi Kumar"
python -m app.cli --interactive

# Streamlit Web UI
python -m streamlit run app/streamlit_ui.py
```

#### Option 3: Legacy Entry Points (Backward Compatible)

```bash
python main.py "Search for patient Ravi Kumar"
python -m streamlit run app.py
```

## 🛠️ Available Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `search_patient` | Search for patients by name | `name`, `dob?`, `identifier?` |
| `check_insurance_eligibility` | Check coverage for a service | `patient_id`, `service_type` |
| `find_available_slots` | Find open appointment slots | `specialty`, `start_date`, `end_date`, `location?` |
| `book_appointment` | Book an appointment | `patient_id`, `slot_id`, `reason`, `dry_run?` |

## 🛡️ Safety Features

The agent **cannot** and **will not**:
- ❌ Provide medical diagnoses
- ❌ Give medical advice or treatment recommendations
- ❌ Prescribe medications
- ❌ Generate hallucinated medical data

## 📊 Sample Patients

| ID | Name | Insurance Status |
|----|------|------------------|
| P001 | Ravi Kumar | Active (Star Health) |
| P002 | Sarah Johnson | Active (BCBS) |
| P003 | Anita Patel | Cancelled |

## 🧪 Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test files
python -m pytest tests/test_functions.py -v
python -m pytest tests/test_safety.py -v
python -m pytest tests/test_agent.py -v
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_API_TOKEN` | Hugging Face API token | (optional) |
| `HF_MODEL` | Model to use | `mistralai/Mistral-7B-Instruct-v0.2` |
| `DRY_RUN_MODE` | Default dry-run setting | `false` |
| `AUDIT_LOG_PATH` | Path to audit log | `logs/audit.jsonl` |

## ❓ Troubleshooting

### Common Issues

**1. `NameError: name 'appointments' is not defined`**
- This issue has been resolved in the latest version. Please ensure you have the latest `app.py`.

**2. Streamlit UI shows raw HTML code**
- This was a rendering issue that has been fixed. Refresh your browser or restart the app.

**3. "Appointment not booked" / "Not Eligible"**
- If you see "Not Eligible" for insurance, it might be because the mock patient (e.g., P003) has inactive insurance.
- Try using **Ravi Kumar (P001)** or **Sarah Johnson (P002)** for successful bookings.

**4. `HF_API_TOKEN` errors**
- Ensure you have a valid Hugging Face token in your `.env` file.
- If you don't have a token, you can run in **Dry Run Mode** or the agent will fall back to rule-based parsing (limited functionality).

## 📝 License

This project is for educational purposes as part of a healthcare AI assignment.
