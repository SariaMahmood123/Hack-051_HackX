"""
Simple test script for backend endpoints
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_text_generation():
    """Test text generation endpoint"""
    print("\n" + "="*60)
    print("Testing Text Generation")
    print("="*60)
    
    payload = {
        "prompt": "Tell me a short joke about programming",
        "conversation_history": [],
        "temperature": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/api/generate/text", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Request ID: {data['request_id']}")
        print(f"Text: {data['text'][:200]}...")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_full_pipeline():
    """Test full pipeline endpoint"""
    print("\n" + "="*60)
    print("Testing Full Pipeline")
    print("="*60)
    
    payload = {
        "prompt": "Hello! How are you today?",
        "conversation_history": [],
        "temperature": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/api/generate/full", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Request ID: {data['request_id']}")
        print(f"Text: {data['text'][:100]}...")
        print(f"Audio URL: {data['audio_url']}")
        print(f"Video URL: {data['video_url']}")
        print(f"Processing Time: {data.get('processing_time', 'N/A')}s")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_api_status():
    """Test API status endpoint"""
    print("\n" + "="*60)
    print("Testing API Status")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def main():
    """Run all tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              LUMEN Backend Test Suite                     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"Testing backend at: {BASE_URL}")
    print("\nMake sure the backend server is running!")
    print("  python backend/run.py\n")
    
    input("Press Enter to start tests...")
    
    tests = [
        ("Health Check", test_health),
        ("API Status", test_api_status),
        ("Text Generation", test_text_generation),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
