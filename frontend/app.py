import streamlit as st
import requests
import os

INGEST_URL = os.environ.get("INGEST_URL", "http://localhost:9000")
GENERATE_URL = os.environ.get("GENERATE_URL", "http://localhost:9001")

st.set_page_config(page_title="AI Quiz Master", layout="centered")
st.title("🧠 SPE MLOps: AI Quiz Generator")

# Fetch available documents on load
@st.cache_data(ttl=5) # Cache for 5 seconds to prevent spamming the API
@st.cache_data(ttl=5)
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
st.header("🎯 Generate Assessment")

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
                else:
                    st.error("Failed to generate.")

with col2:
    st.markdown("**Option B: Full Document Quiz**")
    st.caption("Automatically generate 5 questions from the selected source.")
    if st.button("Auto-Generate 5 MCQs", use_container_width=True, type="primary"):
        with st.spinner(f"Scanning '{selected_doc}'..."):
            res = requests.post(f"{GENERATE_URL}/generate", json={"topic": "", "source_file": selected_doc, "num_questions": 5})
            if res.status_code == 200:
                st.session_state['quiz_data'] = res.json()
                st.rerun()
            else:
                st.error("Failed to generate.")

# --- 3. Interactive Quiz Display ---
if 'quiz_data' in st.session_state:
    st.divider()
    quiz_payload = st.session_state['quiz_data']
    questions_list = quiz_payload.get("questions", [])
    
    # NEW: Check if the AI returned NO_DATA
    if not questions_list or questions_list[0].get('question') == "NO_DATA":
        st.warning(f"⚠️ **Context Not Found**\n\nI could not find enough information about this topic in the selected document to generate a high-quality question. Please try a different topic or upload a more relevant document.")
    else:
        # If we have valid questions, render them as normal
        st.subheader(f"📝 Your Assessment ({len(questions_list)} Questions)")
        
        for index, q in enumerate(questions_list):
            with st.container(border=True):
                st.markdown(f"**Q{index + 1}: {q['question']}**")
                user_choice = st.radio("Select your answer:", q['options'], index=None, key=f"radio_{index}")
                
                if user_choice:
                    if user_choice == q['correct_answer']:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is: {q['correct_answer']}")
                    
                    specific_explanation = q.get('option_explanations', {}).get(user_choice, "No explanation provided.")
                    st.info(f"**Analysis:** {specific_explanation}")
                    
        with st.expander("🔍 View Raw Source Context"):
            st.caption(quiz_payload.get('source_context', 'No context available.'))