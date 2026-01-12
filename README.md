# 🏥 Smart Medical Card - Pipeline 2

## Medical Scan Analysis API using Azure GPT-4o Vision

**Imagine Cup 2026 - Healthcare Track**

This API analyzes medical scans (ultrasound, X-ray, etc.) using GPT-4o Vision and returns:
- Classification (benign/malignant/normal)
- Diagnostic findings
- Radiologist-style reports
- Recommendations

---

## 🚀 Quick Start (5 minutes)

### Step 1: Setup Environment

```bash
# Navigate to project folder
cd pipeline2

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Credentials

```bash
# Copy template
cp .env.template .env

# Edit .env and add your Azure OpenAI key
# AZURE_OPENAI_KEY=your-actual-key-here
```

### Step 3: Run the Server

```bash
python main.py
```

Server starts at: `http://localhost:8000`

### Step 4: Test the API

```bash
# Open in browser for interactive docs
http://localhost:8000/docs

# Or run test script
python test_api.py
```

---

## 📡 API Endpoints

### Health Check
```
GET /health
```

### Analyze Any Medical Scan
```
POST /analyze
Content-Type: multipart/form-data

file: <image file>
scan_type: (optional) breast_ultrasound | pcos_ultrasound
```

### Specialized Endpoints
```
POST /analyze/breast-ultrasound  - For breast ultrasounds (BI-RADS)
POST /analyze/pcos               - For PCOS detection
POST /report/generate            - Generate full medical report
```

---

## 📋 Example Response

```json
{
  "success": true,
  "scan_type": "breast ultrasound",
  "classification": "benign",
  "confidence": "high",
  "findings": [
    "Well-defined oval mass identified",
    "Homogeneous internal echoes",
    "Parallel orientation to skin"
  ],
  "report": "The ultrasound demonstrates a well-circumscribed oval mass...",
  "recommendations": [
    "Routine follow-up in 6 months",
    "Clinical correlation recommended"
  ],
  "timestamp": "2026-01-09T03:00:00Z",
  "disclaimer": "This AI analysis is for educational purposes only..."
}
```

---

## 🧪 Testing with Sample Images

### Download Test Images from Kaggle:

**Breast Ultrasound (BUSI):**
```
https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset
```

**PCOS Ultrasound:**
```
https://www.kaggle.com/datasets/anaghachoudhari/pcos-detection-using-ultrasound-images
```

### Test Command:
```bash
python test_api.py ./samples/breast_benign.png breast_ultrasound
python test_api.py ./samples/pcos_infected.png pcos_ultrasound
```

---

## 🔧 Configuration

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_KEY` | Your API key |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (gpt-4o-vision) |

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Client    │ ──── │  FastAPI     │ ──── │  Azure OpenAI   │
│  (Browser)  │      │  Backend     │      │  GPT-4o Vision  │
└─────────────┘      └──────────────┘      └─────────────────┘
      │                     │
      │                     ▼
      │              ┌──────────────┐
      └───────────── │   Response   │
                     │   (JSON)     │
                     └──────────────┘
```

---

## ⚠️ Disclaimer

This AI system is for **educational and demonstration purposes only** (Imagine Cup 2026).

- NOT a replacement for professional medical diagnosis
- Always consult qualified healthcare professionals
- Results should be reviewed by licensed radiologists

---

## 📁 Project Structure

```
pipeline2/
├── main.py           # FastAPI application
├── test_api.py       # Test script
├── requirements.txt  # Python dependencies
├── .env.template     # Environment template
├── .env              # Your credentials (create this)
└── README.md         # This file
```

---

## 🎯 For Imagine Cup Demo

1. Start the server: `python main.py`
2. Open Swagger UI: `http://localhost:8000/docs`
3. Upload a medical scan image
4. Show the AI analysis results
5. Generate a full medical report

**Good luck with your submission!** 🏆
