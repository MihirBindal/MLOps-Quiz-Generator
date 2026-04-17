import streamlit as st
import requests
import os

INGEST_URL = os.environ.get("INGEST_URL", "http://localhost:9000")
GENERATE_URL = os.environ.get("GENERATE_URL", "http://localhost:9001")

st.set_page_config(page_title="AI Quiz Master", layout="centered")
st.title("SPE MLOps: AI Quiz Generator")

# Fetch available documents on load
@st.cache_data(ttl=5) # Cache for 5 seconds to prevent spamming the API
def get_documents():
    try:
        # Added a 2-second timeout
        res = requests.get(f"{INGEST_URL}/documents", timeout=2) 
        if res.status_code == 200:
            return res.json().get("documents", [])
        return []
    except requests.exceptions.RequestException as e:
        # Instead of hanging, print the error to the Streamlit terminal
        print(f"Failed to connect to Ingest API: {e}") 
        return []

available_docs = get_documents()

# --- 1. Sidebar ---
with st.sidebar:
    st.header("1. Upload Knowledge")
    uploaded_file = st.file_uploader("Upload PPTX, PDF, or DOCX", type=["pptx", "pdf", "docx"])
    
    if st.button("Process Document") and uploaded_file:
        with st.spinner("Pushing to Qdrant..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(f"{INGEST_URL}/upload", files=files)
                if response.status_code == 200:
                    st.success(f"Processing {uploaded_file.name}!")
                    st.cache_data.clear() # Clear cache so new doc shows up
                else:
                    st.error("Ingestion failed.")  
            except:
                st.error("Ingest Service (Port 9000) offline!")

    st.divider()
    st.header("2. Select Source")
    # Add "All Documents" as the default first option
    doc_options = ["All Documents"] + available_docs
    selected_doc = st.selectbox("Target Document:", doc_options)

# --- 2. Main Canvas ---

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Option A: Targeted MCQ**")
    topic = st.text_input("Enter a specific topic:", placeholder="e.g. 'Docker Volumes'")
    if st.button("Generate 1 Topic MCQ", use_container_width=True):
        if topic:
            with st.spinner(f"Querying '{selected_doc}'..."):
                res = requests.post(f"{GENERATE_URL}/generate", json={"topic": topic, "source_file": selected_doc, "num_questions": 1})
                if res.status_code == 200:
                    st.session_state['quiz_data'] = res.json()
                    st.rerun()
                elif res.status_code == 429:
                    error_detail = res.json().get("detail", "Rate limit reached.")
                    st.warning(f"{error_detail}")
                else:
                    st.error("Failed to generate. Please check the backend logs.")

with col2:
    st.markdown("**Option B: Full Document Quiz**")
    st.caption("Automatically generate 5 questions from the selected source.")
    if st.button("Auto-Generate 5 MCQs", use_container_width=True, type="primary"):
        with st.spinner(f"Scanning '{selected_doc}'..."):
            res = requests.post(f"{GENERATE_URL}/generate", json={"topic": "", "source_file": selected_doc, "num_questions": 5})
            if res.status_code == 200:
                st.session_state['quiz_data'] = res.json()
                st.rerun()
            elif res.status_code == 429:
                error_detail = res.json().get("detail", "Rate limit reached.")
                st.warning(f"{error_detail}")
            else:
                st.error("Failed to generate. Please check the backend logs.")

# --- 3. Interactive Quiz Display ---
if 'quiz_data' in st.session_state:
    st.divider()
    quiz_payload = st.session_state['quiz_data']
    questions_list = quiz_payload.get("questions", [])
    
    if not questions_list or questions_list[0].get('question') == "NO_DATA":
        st.warning("**Context Not Found**\n\nI could not find enough information about this topic.")
    else:
        st.subheader(f"Your Assessment ({len(questions_list)} Questions)")
        
        # Initialize session state for tracking answers if not exists
        if 'user_answers' not in st.session_state:
            st.session_state['user_answers'] = {}
        if 'quiz_submitted' not in st.session_state:
            st.session_state['quiz_submitted'] = False

        for index, q in enumerate(questions_list):
            with st.container(border=True):
                st.markdown(f"**Q{index + 1}: {q['question']}**")
                
                # Disable radio if already submitted
                user_choice = st.radio(
                    "Select your answer:", 
                    q['options'], 
                    index=None, 
                    key=f"radio_{index}",
                    disabled=st.session_state['quiz_submitted']
                )
                
                if user_choice:
                    st.session_state['user_answers'][index] = user_choice

                # Show results ONLY after submission
                if st.session_state['quiz_submitted']:
                    actual_choice = st.session_state['user_answers'].get(index)
                    if actual_choice == q['correct_answer']:
                        st.success(f"Correct!")
                    else:
                        st.error(f"Incorrect. The correct answer was: {q['correct_answer']}")
                    
                    with st.expander("View Analysis"):
                        st.info(q.get('option_explanations', {}).get(actual_choice, "No explanation available."))

        # --- Submit Logic ---
        if not st.session_state['quiz_submitted']:
            if st.button("Submit Quiz", type="primary", use_container_width=True):
                # Check if all questions are answered
                if len(st.session_state['user_answers']) < len(questions_list):
                    st.warning("Please answer all questions before submitting.")
                else:
                    st.session_state['quiz_submitted'] = True
                    
                    # Calculate Score
                    correct_count = sum(1 for i, q in enumerate(questions_list) 
                                       if st.session_state['user_answers'].get(i) == q['correct_answer'])
                    
                    # LOG THE SESSION (This will be picked up by ELK)
                    import json
                    from datetime import datetime
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "level": "INFO",
                        "service": "frontend-ui",
                        "event": "quiz_submitted",
                        "score": correct_count,
                        "total": len(questions_list),
                        "source": selected_doc,
                        "topic": topic if topic else "Auto-Generate"
                    }
                    print(json.dumps(log_entry))
                    st.rerun()

        if st.session_state['quiz_submitted']:
            correct_count = sum(1 for i, q in enumerate(questions_list) 
                               if st.session_state['user_answers'].get(i) == q['correct_answer'])
            st.balloons()
            st.metric("Your Final Score", f"{correct_count} / {len(questions_list)}")
            if st.button("Start New Quiz"):
                del st.session_state['quiz_data']
                del st.session_state['user_answers']
                st.session_state['quiz_submitted'] = False
                st.rerun()