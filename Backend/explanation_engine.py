def get_medical_meaning(test_name):
    meanings = {
        "HbA1c": "HbA1c reflects average blood sugar levels over the past 3 months.",
        "TSH": "TSH measures thyroid function.",
        "Hemoglobin": "Hemoglobin measures oxygen-carrying capacity of blood.",
        "WBC": "WBC indicates immune system activity."
    }
    
    return meanings.get(test_name, "No detailed explanation available for this test.")
def generate_explanation(structured_data, age, condition, mode):
    
    findings = []
    known = []
    unclear = []
    
    abnormal_count = 0
    
    for item in structured_data:
        test = item["test"]
        value = item["value"]
        status = item["status"]
        range_val = item["range"]
        
        findings.append(f"{test} is {status} ({value}). Normal range: {range_val}.")
        
        meaning = get_medical_meaning(test)
        
        if status != "Normal":
            abnormal_count += 1
            known.append(f"{test}: {meaning}")
        else:
            unclear.append(f"{test} does not show abnormal findings.")
    
    # Confidence logic
    if abnormal_count == 0:
        confidence = "High"
    elif abnormal_count <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    # Personalization (basic)
    personalization_note = ""
    if "diabetes" in condition.lower():
        personalization_note += "Patient has diabetes history. Blood sugar markers require attention. "
    
    if age > 60:
        personalization_note += "Age above 60 may increase risk factors."
    
    explanation = {
        "Findings": findings,
        "Known": known,
        "Unclear": unclear,
        "Personalized Note": personalization_note,
        "Confidence": confidence,
        "Safety Note": "This is an AI-generated explanation. Not a medical diagnosis."
    }
    
    return explanation