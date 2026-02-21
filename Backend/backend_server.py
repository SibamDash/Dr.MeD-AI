"""
Dr.MeD - Flask Backend Server
Complete backend implementation with AI model integration endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
import glob
import pdfplumber
from structured_extraction import extract_lab_values
from llm_generator import analyze_with_llm

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "")
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
        if 'report' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['report']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Invalid file format. Only PDF, JPG, PNG allowed"
            }), 400
        
        # Get patient data
        patient_data = json.loads(request.form.get('patientData', '{}'))
        
        # Generate unique file ID
        file_id = generate_file_id()
        filename = secure_filename(file.filename)
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(file_path)
        
        # Store metadata (in production, save to database)
        metadata = {
            "fileId": file_id,
            "fileName": filename,
            "filePath": file_path,
            "patientData": patient_data,
            "uploadedAt": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "fileId": file_id,
            "fileName": filename,
            "uploadedAt": metadata["uploadedAt"],
            "message": "File uploaded successfully"
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
            
        file_path = files[0]
        
        # Step 1: Extract text from report
        extracted_text = AIModels.extract_text_from_report(file_path)
        
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
        llm_result = analyze_with_llm(extracted_text, patient_context, structured_data)
        
        if llm_result:
            # Use LLM generated content
            personalized_analysis = llm_result.get('analysis', "Analysis could not be generated.")
            recommendations = llm_result.get('recommendations', [])
            uncertainties = llm_result.get('uncertainties', [])
            confidence_score = 0.98 # High confidence when LLM works
        else:
            # Fallback if API fails (Demo Mode)
            print("⚠️ Using Fallback/Demo Data")
            personalized_analysis = "Based on the analysis of your report, we detected several key values. Please verify with your doctor."
            recommendations = [
                {"title": "Consult Doctor", "description": "Please review these findings with a specialist.", "icon": "👨‍⚕️", "priority": "high"}
            ]
            uncertainties = ["Unable to verify specific context without AI connection"]
            confidence_score = 0.85
        
        # Compile response
        response = {
            "success": True,
            "analysisId": f"analysis_{uuid.uuid4().hex[:8]}",
            "confidence": int(confidence_score * 100),
            "findings": findings,
            "analysis": personalized_analysis,
            "recommendations": recommendations,
            "uncertainties": uncertainties,
            "riskScore": risk_scores or {"overall": 0.25},
            "classification": classification,
            "processedAt": datetime.now().isoformat()
        }
        
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
        
        # TODO: Fetch from database
        history = [
            {
                "date": "2026-02-20",
                "reportType": "Blood Test",
                "analysisId": "analysis_12345",
                "summary": "Glucose control improved by 18%"
            },
            {
                "date": "2025-11-15",
                "reportType": "Blood Test",
                "analysisId": "analysis_11234",
                "summary": "Initial diabetes diagnosis"
            }
        ]
        
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
    print("=" * 50)
    print("Dr.MeD Backend Server")
    print("=" * 50)
    print("Server running at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/")
    print("\nAvailable endpoints:")
    print("  POST   /api/upload-report")
    print("  POST   /api/analyze")
    print("  GET    /api/patient/history")
    print("  POST   /api/doctor/verify")
    print("  GET    /api/recommendations")
    print("  POST   /api/analysis/save")
    print("\nAI Model endpoints:")
    print("  POST   /api/models/nlp/extract")
    print("  POST   /api/models/classify")
    print("  POST   /api/models/risk-assessment")
    print("  POST   /api/rag/query")
    print("  POST   /api/models/personalize")
    print("  POST   /api/models/confidence")
    print("\nHealth check:")
    print("  GET    /api/health")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
