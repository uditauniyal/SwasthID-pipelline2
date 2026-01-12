"""
Test Script for Pipeline 2 API
Run this after starting the server to verify everything works.
"""

import os
import requests
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200


def test_analyze_with_sample():
    """Test analyze endpoint with a sample/test image."""
    print("\n🔍 Testing analyze endpoint...")
    
    # Create a simple test image (1x1 pixel PNG)
    # In real usage, this would be an actual medical scan
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    test_image_bytes = base64.b64decode(test_image_base64)
    
    # Save temporary test image
    test_image_path = Path("test_image.png")
    test_image_path.write_bytes(test_image_bytes)
    
    try:
        with open(test_image_path, "rb") as f:
            files = {"file": ("test_image.png", f, "image/png")}
            response = requests.post(f"{API_URL}/analyze", files=files)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Scan Type: {result.get('scan_type')}")
            print(f"   Classification: {result.get('classification')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Findings: {result.get('findings')}")
        else:
            print(f"   Error: {response.text}")
            
    finally:
        # Cleanup
        if test_image_path.exists():
            test_image_path.unlink()
    
    return response.status_code == 200


def test_with_real_image(image_path: str, scan_type: str = None):
    """Test with a real medical image."""
    print(f"\n🔍 Testing with real image: {image_path}")
    
    if not Path(image_path).exists():
        print(f"   ❌ Image not found: {image_path}")
        return False
    
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        data = {"scan_type": scan_type} if scan_type else {}
        response = requests.post(f"{API_URL}/analyze", files=files, data=data)
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"\n   📋 ANALYSIS RESULTS:")
        print(f"   {'='*50}")
        print(f"   Scan Type: {result.get('scan_type')}")
        print(f"   Classification: {result.get('classification')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"\n   Findings:")
        for finding in result.get('findings', []):
            print(f"      • {finding}")
        print(f"\n   Report:")
        print(f"      {result.get('report')}")
        print(f"\n   Recommendations:")
        for rec in result.get('recommendations', []):
            print(f"      • {rec}")
        print(f"   {'='*50}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False


def main():
    print("=" * 60)
    print("🏥 Smart Medical Card - Pipeline 2 Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if test_health():
        print("   ✅ Health check passed!")
    else:
        print("   ❌ Health check failed! Is the server running?")
        print("   Run: python main.py")
        return
    
    # Test 2: Basic analyze (with dummy image)
    print("\n" + "-" * 60)
    if test_analyze_with_sample():
        print("   ✅ Analyze endpoint working!")
    else:
        print("   ⚠️  Analyze returned error (expected with test image)")
    
    # Test 3: Real image (if provided)
    print("\n" + "-" * 60)
    print("\n📌 To test with a real medical scan:")
    print("   python test_api.py /path/to/your/scan.png breast_ultrasound")
    print("   python test_api.py /path/to/your/scan.png pcos_ultrasound")
    
    print("\n" + "=" * 60)
    print("✅ Basic tests complete!")
    print("📡 API Documentation: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test with provided image
        image_path = sys.argv[1]
        scan_type = sys.argv[2] if len(sys.argv) > 2 else None
        test_with_real_image(image_path, scan_type)
    else:
        main()
