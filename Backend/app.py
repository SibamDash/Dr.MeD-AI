import streamlit as st
import pdfplumber
from structured_extraction import extract_lab_values
from explanation_engine import generate_explanation
from rag import load_documents, create_vector_store, retrieve
from llm_generator import generate_llm_explanation

if structured_data:
    query_text = " ".join([item["test"] for item in structured_data if item["status"] != "Normal"])
    
    retrieved_chunks = retrieve(query_text, index, docs)
    
    combined_context = " ".join(retrieved_chunks)
    
    explanation = generate_llm_explanation(
        combined_context,
        structured_data,
        age,
        condition,
        mode
    )
    
    st.subheader("AI Generated Explanation (RAG + LLM)")
    st.write(explanation)
documents = load_documents("data/guidelines")
index, docs = create_vector_store(documents)

if structured_data:
    query_text = " ".join([item["test"] for item in structured_data if item["status"] != "Normal"])
    
    retrieved_chunks = retrieve(query_text, index, docs)
    
    st.subheader("Retrieved Medical Context")
    for chunk in retrieved_chunks:
        st.write(chunk)
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
