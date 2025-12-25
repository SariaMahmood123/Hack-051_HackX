"""
Quick test for the persona video endpoint
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_mkbhd_video():
    """Test MKBHD persona video generation"""
    print("Testing MKBHD persona video generation...")
    
    payload = {
        "prompt": "Explain why the new M4 Mac Mini is the best value",
        "persona": "mkbhd",
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/persona-video",
            json=payload,
            timeout=600  # 10 minutes for video generation
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"Request ID: {result['request_id']}")
            print(f"Processing time: {result.get('processing_time', 'N/A')}s")
            print(f"\nText generated ({len(result['text'])} chars):")
            print(result['text'][:200] + "...")
            print(f"\nAudio URL: {result['audio_url']}")
            print(f"Video URL: {result['video_url']}")
            return result
        else:
            print(f"\n❌ Error {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return None

def test_ijustine_video():
    """Test iJustine persona video generation"""
    print("Testing iJustine persona video generation...")
    
    payload = {
        "prompt": "Tell me about the new iPhone camera features",
        "persona": "ijustine",
        "temperature": 0.8,
        "max_tokens": 300
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/persona-video",
            json=payload,
            timeout=600
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"Request ID: {result['request_id']}")
            print(f"Processing time: {result.get('processing_time', 'N/A')}s")
            print(f"\nText generated ({len(result['text'])} chars):")
            print(result['text'][:200] + "...")
            print(f"\nAudio URL: {result['audio_url']}")
            print(f"Video URL: {result['video_url']}")
            return result
        else:
            print(f"\n❌ Error {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ijustine":
        test_ijustine_video()
    else:
        test_mkbhd_video()
