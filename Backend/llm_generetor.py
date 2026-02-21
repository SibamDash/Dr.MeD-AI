from transformers import pipeline

generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    max_length=512
)

def generate_llm_explanation(context, structured_data, age, condition, mode):
    
    prompt = f"""
You are a medical explanation assistant.
Only use the provided context.
Do not diagnose.
If information is missing, say 'Insufficient information'.

Context:
{context}

Report Data:
{structured_data}

Patient Age: {age}
Conditions: {condition}

Explain clearly in {mode} language.
Add:
- Findings
- Known
- Unclear
- Confidence level
- Safety note
"""

    result = generator(prompt)[0]["generated_text"]
    return result