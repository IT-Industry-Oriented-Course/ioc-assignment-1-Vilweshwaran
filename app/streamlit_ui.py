"""
Streamlit UI for Clinical Workflow Agent

A modern web interface for the function-calling LLM agent for clinical workflow automation.
"""

import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import ClinicalWorkflowAgent
from src.functions.schemas import FUNCTION_SCHEMAS
from src.sandbox.mock_api import MOCK_PATIENTS, MOCK_COVERAGES

# Page Configuration
st.set_page_config(
    page_title="Clinical Workflow Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main { padding: 1rem; }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 { margin: 0; font-size: 2.5rem; }
    .main-header p { margin: 0.5rem 0 0 0; opacity: 0.9; }
    
    .success-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .function-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
    
    .patient-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .slot-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 10px 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = ClinicalWorkflowAgent()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'dry_run' not in st.session_state:
    st.session_state.dry_run = False


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🏥 Clinical Workflow Agent</h1>
        <p>AI-powered assistant for healthcare administrative tasks</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with settings and info."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        st.session_state.dry_run = st.toggle(
            "🧪 Dry Run Mode",
            value=st.session_state.dry_run,
            help="When enabled, operations are simulated without making actual changes"
        )
        
        if st.session_state.dry_run:
            st.warning("Dry run mode is ON - no actual bookings will be made")
        
        st.divider()
        
        st.markdown("## 🛠️ Available Functions")
        for func in FUNCTION_SCHEMAS:
            with st.expander(f"📋 {func['name']}", expanded=False):
                st.markdown(f"**Description:** {func['description']}")
                st.markdown("**Parameters:**")
                for param, details in func['parameters']['properties'].items():
                    required = "✅" if param in func['parameters'].get('required', []) else "❌"
                    st.markdown(f"- `{param}` {required}: {details.get('description', 'N/A')}")
        
        st.divider()
        
        st.markdown("## 👥 Sample Patients")
        for patient_id, patient in MOCK_PATIENTS.items():
            name = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
            status = "🟢 Active" if patient['active'] else "🔴 Inactive"
            st.markdown(f"**{name}** ({patient_id})")
            st.caption(f"{status} | DOB: {patient.get('birthDate', 'N/A')}")
        
        st.divider()
        
        st.markdown("## 🛡️ Safety Rules")
        st.info("This agent **cannot**:\n- ❌ Provide diagnosis\n- ❌ Give medical advice\n- ❌ Prescribe medications")
        
        st.divider()
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


def format_patient_result(patient):
    """Format patient search result."""
    name = f"{' '.join(patient['name'][0].get('given', []))} {patient['name'][0].get('family', '')}"
    return f"""<div class="patient-card">
    <strong>👤 {name}</strong><br>
    <small>ID: {patient.get('id', 'N/A')} | DOB: {patient.get('birthDate', 'N/A')} | Gender: {patient.get('gender', 'N/A')}</small>
</div>"""


def format_coverage_result(coverage):
    """Format insurance coverage result."""
    is_eligible = coverage.get('isEligible', False)
    status_class = "success" if is_eligible else "error"
    status_text = "✅ ELIGIBLE" if is_eligible else "❌ NOT ELIGIBLE"
    
    return f"""<div class="{status_class}-box">
    <strong>🏥 Insurance Status: {status_text}</strong><br>
    <small>
        Plan: {coverage.get('planName', 'N/A')}<br>
        Payor: {', '.join(coverage.get('payor', []))}<br>
        Copay: ${coverage.get('copayAmount', 'N/A')}<br>
        Reason: {coverage.get('eligibilityReason', 'N/A')}
    </small>
</div>"""


def format_slot_result(slots):
    """Format available slots result."""
    if not slots:
        return "<p>No slots available</p>"
    
    html = "<div>"
    for i, slot in enumerate(slots[:5]):
        html += f"""<div class="slot-card">
    <strong>🕐 Slot {i+1}: {slot.get('id', 'N/A')}</strong><br>
    <small>
        Time: {slot.get('start', 'N/A')}<br>
        Provider: {slot.get('practitionerName', 'N/A')}<br>
        Location: {slot.get('location', 'N/A')}
    </small>
</div>"""
    html += "</div>"
    return html


def format_appointment_result(appointment):
    """Format appointment booking result."""
    is_dry_run = appointment.get('_dryRun', False)
    
    return f"""
    <div class="success-box">
        <strong>📅 Appointment {'(DRY RUN)' if is_dry_run else 'Booked!'}</strong><br>
        <small>
            ID: {appointment.get('id', 'N/A')}<br>
            Status: {appointment.get('status', 'N/A')}<br>
            Specialty: {appointment.get('specialty', 'N/A')}<br>
            Provider: {appointment.get('practitionerName', 'N/A')}<br>
            Location: {appointment.get('location', 'N/A')}<br>
            Time: {appointment.get('start', 'N/A')}<br>
            Reason: {appointment.get('reason', 'N/A')}
        </small>
    </div>
    """


def process_and_display_response(response):
    """Process agent response and display results."""
    
    if response.safety_refused:
        st.markdown(f"""
        <div class="warning-box">
            <strong>⚠️ Request Refused</strong><br>
            {response.message}<br><br>
            <strong>Suggested Action:</strong> {response.data.get('suggested_action', 'Please consult a healthcare provider.')}
        </div>
        """, unsafe_allow_html=True)
        return
    
    if not response.success:
        st.error(f"❌ {response.message}")
        return
    
    st.success(f"✅ {response.message}")
    
    if response.function_calls:
        st.markdown("**Functions Called:**")
        badges = " ".join([f'<span class="function-badge">{fc["name"]}</span>' for fc in response.function_calls])
        st.markdown(badges, unsafe_allow_html=True)
    
    if response.data and 'results' in response.data:
        for result in response.data['results']:
            func_name = result.get('function', '')
            func_result = result.get('result', {})
            
            with st.expander(f"📋 {func_name} Result", expanded=True):
                if func_name == 'search_patient':
                    entries = func_result.get('entry', [])
                    if entries:
                        for entry in entries:
                            st.markdown(format_patient_result(entry.get('resource', {})), unsafe_allow_html=True)
                    else:
                        st.info("No patients found")
                
                elif func_name == 'check_insurance_eligibility':
                    if func_result.get('resourceType') == 'Coverage':
                        st.markdown(format_coverage_result(func_result), unsafe_allow_html=True)
                    else:
                        st.warning("Could not check insurance eligibility")
                
                elif func_name == 'find_available_slots':
                    entries = func_result.get('entry', [])
                    slots = [e.get('resource', {}) for e in entries]
                    st.markdown(format_slot_result(slots), unsafe_allow_html=True)
                
                elif func_name == 'book_appointment':
                    if func_result.get('success'):
                        st.markdown(format_appointment_result(func_result.get('appointment', {})), unsafe_allow_html=True)
                    else:
                        # Handle OperationOutcome or simple error
                        error_msg = func_result.get('message')
                        if not error_msg and func_result.get('resourceType') == 'OperationOutcome':
                            issues = func_result.get('issue', [])
                            if issues:
                                error_msg = issues[0].get('diagnostics', 'Unknown error')
                        
                        st.error(f"Booking failed: {error_msg or 'Unknown error'}")
                
                else:
                    st.json(func_result)


def render_chat_interface():
    """Render the main chat interface."""
    
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            with st.chat_message("user", avatar="👤"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                if 'response' in message:
                    process_and_display_response(message['response'])
                else:
                    st.write(message['content'])
    
    user_input = st.chat_input("Ask me to schedule appointments, check insurance, search patients...")
    
    if user_input:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        with st.spinner("Processing your request..."):
            response = st.session_state.agent.process_request(
                user_input, 
                dry_run=st.session_state.dry_run
            )
        
        st.session_state.chat_history.append({
            'role': 'assistant',
            'response': response
        })
        
        st.rerun()


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Search Ravi Kumar", use_container_width=True):
            process_quick_action("Search for patient Ravi Kumar")
    
    with col2:
        if st.button("🏥 Check Insurance P001", use_container_width=True):
            process_quick_action("Check insurance eligibility for patient P001 for cardiology")
    
    with col3:
        if st.button("📅 Find Cardiology Slots", use_container_width=True):
            process_quick_action("Find available cardiology appointments for next week")
    
    with col4:
        if st.button("📝 Full Booking Flow", use_container_width=True):
            process_quick_action("Schedule a cardiology follow-up for patient Ravi Kumar next week")


def process_quick_action(request: str):
    """Process a quick action request."""
    st.session_state.chat_history.append({
        'role': 'user',
        'content': request
    })
    response = st.session_state.agent.process_request(
        request,
        dry_run=st.session_state.dry_run
    )
    st.session_state.chat_history.append({
        'role': 'assistant',
        'response': response
    })
    st.rerun()


def render_example_prompts():
    """Show example prompts."""
    with st.expander("💡 Example Prompts", expanded=False):
        st.markdown("""
        **Patient Search:**
        - "Search for patient Ravi Kumar"
        - "Find patient Sarah Johnson"
        
        **Insurance Check:**
        - "Check insurance eligibility for patient P001 for cardiology"
        - "I am Ravi Kumar, check my insurance status"
        
        **Appointment Slots:**
        - "Find available cardiology appointments for next week"
        
        **Full Booking:**
        - "Schedule a cardiology follow-up for patient Ravi Kumar next week"
        - "I am Ravi Kumar, book an appointment for cardiology"
        
        **Safety Test (will be refused):**
        - "What medication should I take for headache?"
        """)


def main():
    """Main application."""
    render_header()
    render_sidebar()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        render_quick_actions()
        st.divider()
        render_chat_interface()
    
    with col2:
        render_example_prompts()
        
        with st.expander("📊 Session Info", expanded=False):
            summary = st.session_state.agent.get_audit_summary()
            st.json(summary)


if __name__ == "__main__":
    main()
