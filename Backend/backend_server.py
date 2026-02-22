from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
import glob
import pdfplumber
from structured_extraction import extract_lab_values
from llm_generator import analyze_with_llm
import webbrowser
from threading import Timer

# ─────────────────────────────────────────────────────────────────────────────
# Flask serves the HTML file directly — this eliminates CORS entirely.
# Both the page and the API live on the same origin (http://localhost:5001),
# so the browser never blocks any fetch request, regardless of backend language.
#
# HOW IT WORKS:
#   Flask serves medical-ai.html from the same folder as this Python file.
#   Open:  http://localhost:5001   ← page loads here
#   API:   http://localhost:5001/api/...  ← same origin, no CORS ever
#
# WHY THIS SOLVES CORS PERMANENTLY:
#   CORS triggers only when page origin ≠ API origin.
#   file:// vs http://localhost:5001  →  CORS blocked  ❌
#   http://localhost:5001  vs  http://localhost:5001  →  same origin ✅
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'Frontend')
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='/static')

# ── Serve medical-ai.html at the root URL ───────────────────────────────────
@app.route('/')
def serve_frontend():
    """Serve the main HTML page — open http://localhost:5001 in your browser."""
    return send_from_directory(FRONTEND_DIR, 'medical-ai.html')

@app.route('/report-summary.html')
def serve_report_summary():
    return send_from_directory(FRONTEND_DIR, 'report-summary.html')

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['DATA_FOLDER'] = 'data/'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['DATA_FOLDER'], 'uploads'), exist_ok=True)
os.makedirs(os.path.join(app.config['DATA_FOLDER'], 'analysis'), exist_ok=True)

# ==================== UTILITY FUNCTIONS ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_file_id():
    """Generate unique file ID"""
    return f"report_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

# ==================== AI MODEL INTEGRATION ====================
# TODO: Import your trained models here
# from models.nlp_model import extract_medical_entities
# from models.classifier import classify_condition
# from models.risk_model import assess_risk
# from models.rag_system import query_medical_knowledge
# from models.personalization import personalize_content
# from models.confidence import calculate_confidence

class AIModels:
    """
    Placeholder class for AI model integration
    Replace these methods with your actual trained models
    """
    
    @staticmethod
    def extract_text_from_report(file_path):
        """
        Extract text from medical report using pdfplumber
        """
        text = ""
        try:
            if file_path.lower().endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += (page.extract_text() or "")
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    from PIL import Image
                    import pytesseract
                    text = pytesseract.image_to_string(Image.open(file_path))
                except ImportError:
                    text = "[Image uploaded. To extract text from images, please install 'pytesseract' and 'Pillow' libraries.]"
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            text = "[Image uploaded but OCR failed. Tesseract-OCR is likely not installed or not in PATH. Please install Tesseract to read images.]"
        return text
    
    @staticmethod
    def nlp_extract(text):
        """
        NLP model to extract medical entities
        TODO: Implement with your NLP model (BERT, BioBERT, etc.)
        """
        # Mock extraction
        return {
            "entities": [
                {"type": "measurement", "name": "Blood Glucose", "value": 105, "unit": "mg/dL"},
                {"type": "measurement", "name": "HbA1c", "value": 6.2, "unit": "%"},
                {"type": "measurement", "name": "Total Cholesterol", "value": 215, "unit": "mg/dL"}
            ]
        }
    
    @staticmethod
    def classify_condition(features):
        """
        Classification model for medical conditions
        TODO: Implement with your classifier (Random Forest, Neural Network, etc.)
        """
        return {
            "condition": "Type 2 Diabetes",
            "confidence": 0.92,
            "severity": "mild"
        }
    
    @staticmethod
    def assess_risk(patient_data):
        """
        Risk assessment model
        TODO: Implement risk prediction model
        """
        return {
            "cardiovascular": 0.15,
            "diabetes": 0.32,
            "kidney": 0.08,
            "overall": 0.25
        }
    
    @staticmethod
    def rag_query(query, context):
        """
        RAG system for medical knowledge retrieval
        TODO: Implement RAG with vector database (Pinecone, Weaviate, etc.)
        """
        return {
            "answer": "Based on medical guidelines, this indicates...",
            "sources": [
                {"title": "Medical Reference", "url": "https://...", "relevance": 0.95}
            ]
        }
    
    @staticmethod
    def personalize_explanation(content, patient_profile):
        """
        Personalization model
        TODO: Implement personalization based on literacy level
        """
        literacy_level = patient_profile.get('literacyLevel', 'medium')
        if 'low' in literacy_level.lower():
            return "Your blood sugar is good. Keep doing what you're doing!"
        elif 'high' in literacy_level.lower():
            return "HbA1c of 6.2% indicates glycemic control within target range..."
        else:
            return "Your HbA1c is 6.2%, which means your average blood sugar is well-controlled..."
    
    @staticmethod
    def calculate_confidence(analysis, source_data):
        """
        Confidence scoring and hallucination detection
        TODO: Implement confidence calculation
        """
        return {
            "confidenceScore": 0.96,
            "hallucinationRisk": "low",
            "verifiedStatements": 45,
            "uncertainStatements": 2
        }

# ==================== API ENDPOINTS ====================

@app.route('/api/upload-report', methods=['POST'])
def upload_report():
    """Upload medical report file"""
    try:
        # Check if file is in request
        if 'report' not in request.files and 'prescription' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        files_saved = []
        file_id = generate_file_id()
        patient_data = json.loads(request.form.get('patientData', '{}'))
        
        # Handle Report
        if 'report' in request.files:
            files = request.files.getlist('report')
            for file in files:
                if file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_report_{filename}")
                    file.save(file_path)
                    files_saved.append({"type": "report", "path": file_path, "name": filename})

        # Handle Prescription
        if 'prescription' in request.files:
            files = request.files.getlist('prescription')
            for file in files:
                if file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_prescription_{filename}")
                    file.save(file_path)
                    files_saved.append({"type": "prescription", "path": file_path, "name": filename})
        
        if not files_saved:
             return jsonify({"success": False, "error": "No valid files saved"}), 400
        
        # Store metadata (in production, save to database)
        metadata = {
            "fileId": file_id,
            "files": files_saved,
            "patientData": patient_data,
            "uploadedAt": datetime.now().isoformat()
        }
        
        # Save metadata to JSON storage
        try:
            with open(os.path.join(app.config['DATA_FOLDER'], 'uploads', f"{file_id}.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save upload metadata: {e}")

        return jsonify({
            "success": True,
            "fileId": file_id,
            "files": files_saved,
            "uploadedAt": metadata["uploadedAt"],
            "message": "Files uploaded successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_report():
    """Analyze medical report using AI models"""
    try:
        data = request.json
        file_id = data.get('fileId')
        patient_context = data.get('patientContext', {})
        models_config = data.get('models', {})
        
        # Find the file using file_id
        search_pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_*")
        files = glob.glob(search_pattern)
        
        if not files:
            return jsonify({"success": False, "error": "File not found"}), 404
            
        # Step 1: Extract text from all files
        extracted_text = ""
        for file_path in files:
            extracted_text += AIModels.extract_text_from_report(file_path) + "\n"
        
        # Step 2: Extract structured data (Real Logic)
        structured_data = extract_lab_values(extracted_text)
        
        # Step 2: NLP extraction
        nlp_results = AIModels.nlp_extract(extracted_text) if models_config.get('nlp') else None
        
        # Step 3: Classification
        classification = AIModels.classify_condition(patient_context) if models_config.get('classifier') else None
        
        # Step 4: Risk assessment
        risk_scores = AIModels.assess_risk(patient_context) if models_config.get('risk') else None
        
        # Step 5: Generate findings (Map structured_data to frontend format)
        findings = []
        for item in structured_data:
            findings.append({
                "label": item['test'],
                "value": str(item['value']),
                "status": item['status'].lower(),
                "normalRange": item['range'],
                "unit": "" 
            })
            
        # Step 6: Generate AI Analysis (LLM)
        print("🤖 Sending data to Gemini AI...")
        llm_result = analyze_with_llm(extracted_text, patient_context, structured_data, file_paths=files)

        # Save last LLM result to a debug file so /api/debug-last can serve it
        try:
            debug_payload = {
                "llm_result": llm_result,
                "extracted_text_preview": extracted_text[:500],
                "structured_data": structured_data,
                "timestamp": datetime.now().isoformat()
            }
            with open(os.path.join(BASE_DIR, '_debug_last.json'), 'w') as dbf:
                json.dump(debug_payload, dbf, indent=2)
        except Exception:
            pass
        
        ai_response_data = {}
        
        if llm_result:
            # Use LLM generated content
            ai_response_data = {
                "patient_summary": llm_result.get('patient_summary', "Not available"),
                "test_report_summary": llm_result.get('test_report_summary', "Not available"),
                "clinical_interpretation": llm_result.get('clinical_interpretation', "Not available"),
                "known_information": llm_result.get('known_information', []),
                "unclear_information": llm_result.get('unclear_information', [])
            }

            # Print analysis to terminal
            print("\n" + "="*60)
            print("🧬 AI ANALYSIS REPORT SUMMARY")
            print("="*60)
            print(f"\n👤 PATIENT SUMMARY:\n{ai_response_data['patient_summary']}")
            print(f"\n📄 REPORT SUMMARY:\n{ai_response_data['test_report_summary']}")
            print(f"\n🏥 CLINICAL INTERPRETATION:\n{ai_response_data['clinical_interpretation']}")
            
            if ai_response_data['known_information']:
                print("\n✅ KNOWN INFORMATION:")
                for item in ai_response_data['known_information']:
                    print(f"  • {item}")
            
            if ai_response_data['unclear_information']:
                print("\n❓ UNCLEAR / MISSING:")
                for item in ai_response_data['unclear_information']:
                    print(f"  • {item}")
            print("="*60 + "\n")

            recommendations = llm_result.get('recommendations', [])
            uncertainties = llm_result.get('unclear_information', [])
            confidence_score = 0.98 # High confidence when LLM works
        else:
            # Fallback if API fails (Demo Mode)
            print("⚠️ Using Fallback/Demo Data")
            personalized_analysis = "Based on the analysis of your report, we detected several key values. Please verify with your doctor."
            recommendations = [
                {"title": "Consult Doctor", "description": "Please review these findings with a specialist.", "icon": "👨‍⚕️", "priority": "high"}
            ]
            ai_response_data = {
                "patient_summary": "Patient data extracted (Demo Mode)",
                "test_report_summary": "Report analysis unavailable (Demo Mode)",
                "clinical_interpretation": personalized_analysis,
                "known_information": ["Analysis run in demo mode", "AI model not connected"],
                "unclear_information": ["Full context unavailable"]
            }
            uncertainties = ["Unable to verify specific context without AI connection"]
            confidence_score = 0.85
        
        # Compile response
        response = {
            "success": True,
            "analysisId": f"analysis_{uuid.uuid4().hex[:8]}",
            "confidence": int(confidence_score * 100),
            "aiResponse": ai_response_data,
            "findings": findings,
            "analysis": ai_response_data.get('clinical_interpretation', ''),
            "recommendations": recommendations,
            "uncertainties": uncertainties,
            "riskScore": risk_scores or {"overall": 0.25},
            "classification": classification,
            "processedAt": datetime.now().isoformat()
        }
        
        # Save analysis to JSON storage
        try:
            analysis_record = {
                "analysisId": response["analysisId"],
                "fileId": file_id,
                "patientContext": patient_context,
                "result": response,
                "timestamp": datetime.now().isoformat()
            }
            with open(os.path.join(app.config['DATA_FOLDER'], 'analysis', f"{response['analysisId']}.json"), 'w') as f:
                json.dump(analysis_record, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save analysis record: {e}")

        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/patient/history', methods=['GET'])
def get_patient_history():
    """Get patient's medical history"""
    try:
        patient_id = request.args.get('patientId')
        
        # Fetch from JSON storage
        history = []
        analysis_path = os.path.join(app.config['DATA_FOLDER'], 'analysis')
        if os.path.exists(analysis_path):
            files = glob.glob(os.path.join(analysis_path, "*.json"))
            for f_path in files:
                try:
                    with open(f_path, 'r') as f:
                        record = json.load(f)
                        # In a real app, filter by patient_id here
                        history.append({
                            "date": record['timestamp'].split('T')[0],
                            "reportType": "Medical Report",
                            "analysisId": record['analysisId'],
                            "summary": record['result'].get('analysis', '')[:100] + "..."
                        })
                except:
                    continue
        
        # Sort by date descending
        history.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            "success": True,
            "patientId": patient_id,
            "history": history
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/doctor/verify', methods=['POST'])
def verify_analysis():
    """Doctor verification of AI analysis"""
    try:
        data = request.json
        
        # TODO: Save verification to database
        verification = {
            "success": True,
            "verificationId": f"verify_{uuid.uuid4().hex[:6]}",
            "verifiedAt": datetime.now().isoformat(),
            "doctorInfo": {
                "name": "Dr. Sarah Johnson, MD",
                "specialty": "Endocrinologist",
                "experience": "15 years",
                "licenseNo": "MD-456789"
            }
        }
        
        return jsonify(verification), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get personalized recommendations"""
    try:
        analysis_id = request.args.get('analysisId')
        
        # TODO: Generate recommendations based on analysis
        recommendations = [
            {
                "category": "diet",
                "title": "Dietary Adjustments",
                "description": "Increase fiber intake...",
                "icon": "🥗",
                "priority": "high"
            }
        ]
        
        return jsonify({
            "success": True,
            "recommendations": recommendations
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analysis/save', methods=['POST'])
def save_analysis():
    """Save analysis to database"""
    try:
        data = request.json
        
        # TODO: Save to database
        return jsonify({
            "success": True,
            "savedAt": datetime.now().isoformat(),
            "recordId": f"record_{uuid.uuid4().hex[:8]}"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== AI MODEL ENDPOINTS ====================

@app.route('/api/models/nlp/extract', methods=['POST'])
def nlp_extract():
    """NLP text extraction endpoint"""
    try:
        data = request.json
        text = data.get('text', '')
        
        result = AIModels.nlp_extract(text)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/classify', methods=['POST'])
def classify():
    """Classification endpoint"""
    try:
        data = request.json
        features = data.get('features', {})
        
        result = AIModels.classify_condition(features)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/risk-assessment', methods=['POST'])
def risk_assessment():
    """Risk assessment endpoint"""
    try:
        data = request.json
        
        result = AIModels.assess_risk(data)
        return jsonify({"riskScores": result}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    """RAG system query endpoint"""
    try:
        data = request.json
        query = data.get('query', '')
        context = data.get('context', '')
        
        result = AIModels.rag_query(query, context)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/personalize', methods=['POST'])
def personalize():
    """Personalization endpoint"""
    try:
        data = request.json
        content = data.get('content', '')
        profile = data.get('patientProfile', {})
        
        result = AIModels.personalize_explanation(content, profile)
        return jsonify({"personalizedContent": result}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/confidence', methods=['POST'])
def confidence_score():
    """Confidence scoring endpoint"""
    try:
        data = request.json
        
        result = AIModels.calculate_confidence(
            data.get('analysis', ''),
            data.get('sourceData', {})
        )
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }), 200

# ==================== DEBUG: LAST LLM RESPONSE ====================

@app.route('/api/debug-last', methods=['GET'])
def debug_last():
    """
    Returns the raw LLM result from the most recent /api/analyze call.
    Open http://localhost:5001/api/debug-last in your browser to inspect
    exactly what Gemini returned — useful when HTML display is blank.
    """
    path = os.path.join(BASE_DIR, '_debug_last.json')
    if not os.path.exists(path):
        return jsonify({"message": "No analysis run yet. Call /api/analyze first."}), 404
    with open(path, 'r') as f:
        return jsonify(json.load(f)), 200

# ==================== TEST CONNECTION (Frontend Debug) ====================

@app.route('/api/test-connection', methods=['GET', 'POST'])
def test_connection():
    """
    Returns a full mock analysis response — used by the frontend
    'Test Connection' button to verify the HTML rendering pipeline
    works end-to-end without needing a real file upload.
    """
    mock_response = {
        "success": True,
        "analysisId": "test_analysis_001",
        "confidence": 96,
        "aiResponse": {
            "patient_summary": "Patient is a 45-year-old male with Type 2 Diabetes under active management. Overall health indicators are trending positively based on the latest lab results.",
            "test_report_summary": "Complete Blood Count (CBC) and Metabolic Panel results show well-controlled glucose levels (HbA1c 6.2%), slightly elevated total cholesterol (215 mg/dL), and normal kidney function (eGFR 95 mL/min). Blood pressure is within normal range at 120/80 mmHg.",
            "clinical_interpretation": "The patient's glycemic control is excellent with HbA1c at 6.2%, indicating average blood sugar levels within target range for a diabetic patient. The mild elevation in Total Cholesterol warrants dietary intervention and follow-up lipid panel in 3 months. All other metabolic markers are within normal clinical limits. Continue current medication regimen and lifestyle modifications.",
            "known_information": [
                "HbA1c 6.2% — well within target range for diabetic patients (ADA guideline: <7%)",
                "Fasting blood glucose 105 mg/dL — normal/borderline (70–100 mg/dL is optimal)",
                "eGFR 95 mL/min — normal kidney function, no CKD indicated",
                "Blood pressure 120/80 mmHg — optimal cardiovascular reading",
                "CBC values all within normal ranges — no signs of anemia or infection"
            ],
            "unclear_information": [
                "LDL and HDL breakdown not available — full lipid panel recommended",
                "Vitamin D and B12 levels not tested in current report",
                "Liver enzyme (ALT/AST) values borderline — follow-up in 6 weeks advised",
                "Medication adherence history not available for full context"
            ]
        },
        "findings": [
            {"label": "Blood Glucose (Fasting)", "value": "105 mg/dL", "status": "normal", "normalRange": "70–100 mg/dL"},
            {"label": "HbA1c", "value": "6.2%", "status": "normal", "normalRange": "< 7% (diabetic target)"},
            {"label": "Total Cholesterol", "value": "215 mg/dL", "status": "high", "normalRange": "< 200 mg/dL"},
            {"label": "Blood Pressure", "value": "120/80 mmHg", "status": "normal", "normalRange": "< 130/80 mmHg"},
            {"label": "Kidney Function (eGFR)", "value": "95 mL/min", "status": "normal", "normalRange": "> 60 mL/min"},
            {"label": "Hemoglobin", "value": "14.2 g/dL", "status": "normal", "normalRange": "13.5–17.5 g/dL"},
            {"label": "ALT (Liver)", "value": "42 U/L", "status": "warning", "normalRange": "7–40 U/L"},
            {"label": "TSH (Thyroid)", "value": "2.1 mIU/L", "status": "normal", "normalRange": "0.4–4.0 mIU/L"}
        ],
        "analysis": "The patient shows good overall health with excellent diabetic control. Mild cholesterol elevation and borderline liver enzyme need monitoring.",
        "recommendations": [
            {"title": "Dietary Adjustments", "description": "Increase fiber intake and reduce saturated fats. Focus on omega-3 rich foods (salmon, walnuts, flaxseeds) to help manage cholesterol.", "icon": "🥗", "priority": "high"},
            {"title": "Physical Activity", "description": "Maintain current exercise routine. Add 2 days of resistance training per week to further improve insulin sensitivity and lipid profile.", "icon": "🏃", "priority": "medium"},
            {"title": "Medication Review", "description": "Current diabetes medication appears effective. Discuss cholesterol management (statin therapy) with your doctor at next visit.", "icon": "💊", "priority": "high"},
            {"title": "Follow-up Tests", "description": "Schedule full lipid panel (LDL/HDL breakdown) and liver enzyme retest in 6 weeks. Next HbA1c check in 3 months.", "icon": "📅", "priority": "high"}
        ],
        "uncertainties": [
            "LDL/HDL breakdown needed for complete cardiovascular risk picture",
            "Liver enzymes slightly elevated — rule out medication side effect",
            "Vitamin D deficiency common in diabetic patients — recommend testing"
        ],
        "riskScore": {"cardiovascular": 0.15, "diabetes": 0.12, "kidney": 0.05, "overall": 0.14},
        "processedAt": datetime.now().isoformat()
    }
    return jsonify(mock_response), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "FILE_TOO_LARGE",
            "message": "File size exceeds 10MB limit"
        }
    }), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "Endpoint not found"
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Internal server error"
        }
    }), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("  Dr.MeD Backend Server")
    print("=" * 60)
    print("")
    print("  ✅  Open the app in your browser:")
    print("      👉  http://localhost:5001")
    print("")
    print("  The HTML is served by Flask — no CORS issues ever.")
    print("  Do NOT open medical-ai.html by double-clicking it.")
    print("")
    print("  API endpoints:")
    print("    GET   /              → serves medical-ai.html")
    print("    POST  /api/upload-report")
    print("    POST  /api/analyze")
    print("    GET   /api/health")
    print("=" * 60)
    
    # Allow port to be set via environment variable (Terminal input)
    port = int(os.environ.get('PORT', 5001))
    
    def open_browser():
        if not os.environ.get("WERKZEUG_RUN_MAIN"):
            webbrowser.open_new(f'http://localhost:{port}')
            
    Timer(1.5, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=port)