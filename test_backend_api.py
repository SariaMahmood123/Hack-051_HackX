"""
Quick test script to verify Gemini 2.5 Flash integration
Run this to test the backend API without the frontend
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test health endpoint"""
    print("1. Testing /api/health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Server running")
        print(f"   GPU: {data.get('gpu_available', 'N/A')}")
        print(f"   Gemini Model: {data.get('gemini_model', 'N/A')}")
    print()

def test_text_generation():
    """Test text generation endpoint"""
    print("2. Testing /api/generate/full...")
    
    payload = {
        "prompt": "Say hello in exactly 5 words",
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print(f"   Sending: {payload['prompt']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/full",
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ SUCCESS!")
            print(f"   Response: {data.get('text', 'N/A')}")
            print(f"   Request ID: {data.get('request_id', 'N/A')[:8]}...")
        else:
            print(f"   ✗ FAILED")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ✗ TIMEOUT (>30s)")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    print()

def main():
    print("="*60)
    print("Testing Gemini 2.5 Flash Integration")
    print("="*60)
    print()
    
    test_health()
    test_text_generation()
    
    print("="*60)
    print("Testing complete!")
    print("="*60)

if __name__ == "__main__":
    main()
