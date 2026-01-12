"""
Pipeline 2: Medical Scan Analysis with GPT-4o Vision
Smart Medical Card System - Imagine Cup 2026

This API accepts medical scan images and returns:
- Classification (benign/malignant/normal or infected/not infected)
- Diagnostic findings
- Radiologist-style report
- Confidence assessment
"""

import os
import base64
import json
from datetime import datetime
from typing import Optional
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from openai import AzureOpenAI
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Smart Medical Card - Scan Analysis API",
    description="AI-powered medical scan analysis using GPT-4o Vision",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import httpx

# Initialize Azure OpenAI client
def get_openai_client():
    """Lazy initialization of Azure OpenAI client."""
    # 🔒 SSL Config: Defaults to True (Secure) for production. Set VERIFY_SSL=False in .env only for local debug.
    verify_ssl = os.getenv("VERIFY_SSL", "True").lower() == "true"
    http_client = httpx.Client(verify=verify_ssl)

    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        max_retries=3,
        timeout=30.0,
        http_client=http_client
    )

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-vision")


# =============================================================================
# Response Models
# =============================================================================

class ScanAnalysisResponse(BaseModel):
    success: bool
    scan_type: str
    classification: str
    confidence: str
    findings: list[str]
    report: str
    recommendations: list[str]
    timestamp: str
    disclaimer: str


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: str


# =============================================================================
# Medical Analysis Prompts
# =============================================================================

MEDICAL_ANALYSIS_PROMPT = """You are an expert medical imaging AI assistant helping radiologists analyze medical scans. 

Analyze this medical scan image and provide a structured analysis.

IMPORTANT GUIDELINES:
1. This is for educational/demonstration purposes (Imagine Cup 2026 Healthcare Track)
2. Provide analysis that would help a radiologist, not replace them
3. Always recommend professional medical consultation
4. Be specific about what you observe in the image

Based on the image, provide your analysis in the following JSON format:
{
    "scan_type": "detected type of scan (e.g., breast ultrasound, pelvic ultrasound, X-ray, MRI, CT)",
    "classification": "your assessment (e.g., benign, malignant, normal, suspicious, infected, not infected, or needs further evaluation)",
    "confidence": "low/medium/high - how confident you are in this assessment",
    "findings": [
        "Finding 1: specific observation",
        "Finding 2: specific observation",
        "Finding 3: specific observation"
    ],
    "report": "A detailed radiologist-style report paragraph describing what you observe, the characteristics of any lesions or abnormalities, their location, size estimation, and relevant features",
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ]
}

Analyze the image now and respond ONLY with the JSON object, no additional text."""


BREAST_ULTRASOUND_PROMPT = """You are an expert breast imaging radiologist AI assistant.

Analyze this breast ultrasound image using BI-RADS criteria.

Look for:
- Mass characteristics (shape, margins, orientation, echo pattern)
- Calcifications
- Architectural distortion
- Skin/nipple changes
- Lymph node appearance

Classify as:
- BENIGN: Well-defined margins, oval shape, parallel orientation, homogeneous
- MALIGNANT: Irregular margins, non-parallel orientation, posterior shadowing, microcalcifications
- NORMAL: No suspicious findings

Provide your analysis in JSON format:
{
    "scan_type": "breast ultrasound",
    "classification": "benign/malignant/normal/suspicious",
    "confidence": "low/medium/high",
    "birads_category": "0-6",
    "findings": ["finding 1", "finding 2"],
    "report": "detailed radiologist report",
    "recommendations": ["recommendation 1", "recommendation 2"]
}

Respond ONLY with JSON."""


PCOS_ULTRASOUND_PROMPT = """You are an expert gynecological imaging AI assistant.

Analyze this pelvic/ovarian ultrasound image for signs of Polycystic Ovary Syndrome (PCOS).

Look for:
- Ovarian volume (>10 mL suggests PCOS)
- Follicle count (≥12 follicles of 2-9mm suggests PCOS)
- Peripheral follicle distribution ("string of pearls" pattern)
- Stromal echogenicity
- Ovarian morphology

Classify as:
- PCOS_POSITIVE: Multiple peripheral follicles, enlarged ovary, increased stroma
- PCOS_NEGATIVE: Normal ovarian appearance
- INCONCLUSIVE: Unclear findings, needs further evaluation

Provide your analysis in JSON format:
{
    "scan_type": "pelvic ultrasound - ovarian assessment",
    "classification": "PCOS_positive/PCOS_negative/inconclusive",
    "confidence": "low/medium/high",
    "findings": ["finding 1", "finding 2"],
    "ovarian_volume_assessment": "normal/enlarged",
    "follicle_pattern": "description of follicle distribution",
    "report": "detailed radiologist report",
    "recommendations": ["recommendation 1", "recommendation 2"]
}

Respond ONLY with JSON."""


# =============================================================================
# Helper Functions
# =============================================================================

def encode_image_to_base64(image_data: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.b64encode(image_data).decode('utf-8')


def get_image_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    ext = filename.lower().split('.')[-1]
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp'
    }
    return mime_types.get(ext, 'image/jpeg')


def select_prompt(scan_type: Optional[str]) -> str:
    """Select appropriate prompt based on scan type."""
    if scan_type:
        scan_type_lower = scan_type.lower()
        if 'breast' in scan_type_lower:
            return BREAST_ULTRASOUND_PROMPT
        elif 'pcos' in scan_type_lower or 'ovarian' in scan_type_lower or 'pelvic' in scan_type_lower:
            return PCOS_ULTRASOUND_PROMPT
    return MEDICAL_ANALYSIS_PROMPT


def parse_gpt_response(response_text: str) -> dict:
    """Parse GPT response, handling potential JSON extraction."""
    # Try direct JSON parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    if '```json' in response_text:
        start = response_text.find('```json') + 7
        end = response_text.find('```', start)
        if end > start:
            try:
                return json.loads(response_text[start:end].strip())
            except json.JSONDecodeError:
                pass
    
    # Try to find JSON object in response
    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass
    
    # Return error structure if parsing fails
    return {
        "scan_type": "unknown",
        "classification": "analysis_failed",
        "confidence": "low",
        "findings": ["Unable to parse AI response"],
        "report": response_text,
        "recommendations": ["Please try again or consult a medical professional"]
    }


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Smart Medical Card - Pipeline 2",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "Medical Scan Analysis API",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/analyze", response_model=ScanAnalysisResponse)
async def analyze_scan(
    file: UploadFile = File(..., description="Medical scan image (JPEG, PNG)"),
    scan_type: Optional[str] = Form(None, description="Optional: breast_ultrasound, pcos_ultrasound, or auto-detect")
):
    """
    Analyze a medical scan image using GPT-4o Vision.
    
    - **file**: Medical scan image (JPEG, PNG, etc.)
    - **scan_type**: Optional hint for scan type (breast_ultrasound, pcos_ultrasound)
    
    Returns structured analysis with classification, findings, and recommendations.
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and encode image
        image_data = await file.read()
        
        # Validate image size (max 20MB)
        if len(image_data) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large. Max 20MB.")
        
        # Encode to base64
        base64_image = encode_image_to_base64(image_data)
        mime_type = get_image_mime_type(file.filename or "image.jpg")
        
        # Select appropriate prompt
        prompt = select_prompt(scan_type)
        
        # Call GPT-4o Vision
        client = get_openai_client()
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical imaging AI assistant. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.3  # Lower temperature for more consistent medical analysis
        )
        
        # Parse response
        result_text = response.choices[0].message.content
        analysis = parse_gpt_response(result_text)
        
        # Build response
        return ScanAnalysisResponse(
            success=True,
            scan_type=analysis.get("scan_type", "unknown"),
            classification=analysis.get("classification", "inconclusive"),
            confidence=analysis.get("confidence", "low"),
            findings=analysis.get("findings", []),
            report=analysis.get("report", "Analysis completed. Please review findings."),
            recommendations=analysis.get("recommendations", ["Consult a medical professional for definitive diagnosis"]),
            timestamp=datetime.utcnow().isoformat(),
            disclaimer="This AI analysis is for educational/demonstration purposes only. It is not a medical diagnosis. Always consult qualified healthcare professionals for medical decisions."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis Error: {str(e)}")  # Log to console
        # Check for specific connection errors
        error_msg = str(e)
        if "Connection error" in error_msg:
             error_msg = "Connection to Azure OpenAI failed. Please check your internet connection."
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error_msg}")


@app.post("/analyze/breast-ultrasound", response_model=ScanAnalysisResponse)
async def analyze_breast_ultrasound(
    file: UploadFile = File(..., description="Breast ultrasound image")
):
    """
    Specialized endpoint for breast ultrasound analysis.
    Uses BI-RADS criteria for classification.
    """
    return await analyze_scan(file=file, scan_type="breast_ultrasound")


@app.post("/analyze/pcos", response_model=ScanAnalysisResponse)
async def analyze_pcos_ultrasound(
    file: UploadFile = File(..., description="Pelvic/ovarian ultrasound image")
):
    """
    Specialized endpoint for PCOS detection from ovarian ultrasound.
    Looks for Rotterdam criteria indicators.
    """
    return await analyze_scan(file=file, scan_type="pcos_ultrasound")


@app.post("/report/generate")
async def generate_full_report(
    file: UploadFile = File(...),
    patient_id: str = Form(..., description="Patient ID for the report"),
    patient_name: str = Form(default="[REDACTED]", description="Patient name"),
    scan_type: Optional[str] = Form(None)
):
    """
    Generate a full radiologist-style report for medical records.
    """
    # First get the analysis
    analysis_response = await analyze_scan(file=file, scan_type=scan_type)
    
    # Format as full report
    report = f"""
================================================================================
                    MEDICAL IMAGING REPORT
                    Smart Medical Card System
================================================================================

PATIENT INFORMATION
-------------------
Patient ID: {patient_id}
Patient Name: {patient_name}
Report Date: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

EXAMINATION
-----------
Scan Type: {analysis_response.scan_type}

FINDINGS
--------
{chr(10).join(f"• {finding}" for finding in analysis_response.findings)}

IMPRESSION
----------
Classification: {analysis_response.classification.upper()}
Confidence Level: {analysis_response.confidence}

DETAILED REPORT
---------------
{analysis_response.report}

RECOMMENDATIONS
---------------
{chr(10).join(f"{i+1}. {rec}" for i, rec in enumerate(analysis_response.recommendations))}

================================================================================
DISCLAIMER: {analysis_response.disclaimer}
================================================================================
AI Analysis Timestamp: {analysis_response.timestamp}
Report Generated By: Smart Medical Card AI System (Imagine Cup 2026)
================================================================================
"""
    
    return {
        "success": True,
        "patient_id": patient_id,
        "report_text": report,
        "analysis": analysis_response.model_dump(),
        "generated_at": datetime.utcnow().isoformat()
    }


# =============================================================================
# Run Server
# =============================================================================

# 🚀 Frontend Serving (Production)
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting Smart Medical Card - Pipeline 2 API")
    print("📡 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
