import streamlit as st
import pdfplumber
from structured_extraction import extract_lab_values
from explanation_engine import generate_explanation
from rag import load_documents, create_vector_store, retrieve
from llm_generator import analyze_with_llm

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "")
    return text

st.title("Dr.MeD-AI Medical Report Analyzer")

# Sidebar for patient context
with st.sidebar:
    st.header("Patient Context")
    age = st.number_input("Age", min_value=0, max_value=120, value=45)
    condition = st.text_input("Known Conditions", value="None")
    mode = st.selectbox("Explanation Mode", ["Standard", "Detailed"])

uploaded_file = st.file_uploader("Upload Medical Report (PDF)", type=["pdf"])

if uploaded_file:
    report_text = extract_text_from_pdf(uploaded_file)
    
    structured_data = extract_lab_values(report_text)
    
    # DEMO FALLBACK: If regex fails to find data, load demo values so the UI works
    if not structured_data:
        st.warning("⚠️ Could not extract structured data from this specific PDF format. Showing **DEMO SUMMARY** instead.")
        structured_data = [
            {"test": "Hemoglobin", "value": 12.5, "range": "13.0-17.0", "status": "Low"},
            {"test": "WBC", "value": 8500, "range": "4000-11000", "status": "Normal"},
            {"test": "HbA1c", "value": 6.2, "range": "4.0-5.6", "status": "High"}
        ]

    st.subheader("Structured Findings")
    st.json(structured_data)

    # =========================================================
    # AI ANALYSIS INTEGRATION (Terminal + UI)
    # =========================================================
    patient_context = {
        "age": age,
        "condition": condition,
        "literacyLevel": mode
    }

    with st.spinner("🤖 Dr.MeD-AI is analyzing the report..."):
        ai_response = analyze_with_llm(report_text, patient_context, structured_data)

    if ai_response:
        # 1. PRINT TO TERMINAL
        print("\n" + "="*60)
        print("🧬 AI ANALYSIS REPORT SUMMARY")
        print("="*60)
        print(f"\n👤 PATIENT SUMMARY:\n{ai_response.get('patient_summary', 'N/A')}")
        print(f"\n📄 REPORT SUMMARY:\n{ai_response.get('test_report_summary', 'N/A')}")
        print(f"\n🏥 CLINICAL INTERPRETATION:\n{ai_response.get('clinical_interpretation', 'N/A')}")
        print("="*60 + "\n")

        # 2. DISPLAY IN HTML PAGE (Streamlit)
        st.markdown("---")
        st.header("🧬 AI Analysis Report")
        
        st.info(f"**Patient Summary:** {ai_response.get('patient_summary')}")
        st.success(f"**Report Summary:** {ai_response.get('test_report_summary')}")
        
        st.subheader("🏥 Clinical Interpretation")
        st.write(ai_response.get('clinical_interpretation'))
        
        if ai_response.get('recommendations'):
            st.subheader("💡 Recommendations")
            for rec in ai_response['recommendations']:
                st.warning(f"**{rec.get('title')}**: {rec.get('description')}")
    
    explanation = generate_explanation(structured_data, age, condition, mode)

    st.subheader("AI Medical Explanation")

    st.write("### Findings")
    for f in explanation["Findings"]:
        st.write("-", f)

    st.write("### Known")
    for k in explanation["Known"]:
        st.write("-", k)

    st.write("### Unclear")
    for u in explanation["Unclear"]:
        st.write("-", u)

    st.write("### Personalized Note")
    st.write(explanation["Personalized Note"])

    st.write("### Confidence Level")
    st.write(explanation["Confidence"])

    st.warning(explanation["Safety Note"])
