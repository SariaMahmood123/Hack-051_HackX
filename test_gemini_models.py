"""Test script to list available Gemini models"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"Using API key: {api_key[:20]}...")

genai.configure(api_key=api_key)

print("\n" + "="*60)
print("Available Gemini Models with generateContent support:")
print("="*60)

try:
    models = list(genai.list_models())
    gen_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    
    for i, model in enumerate(gen_models[:10], 1):
        print(f"\n{i}. Model Name: {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description[:80] if model.description else 'N/A'}...")
        
    print("\n" + "="*60)
    print(f"Total models with generateContent: {len(gen_models)}")
    print("="*60)
    
    # Test the first available model
    if gen_models:
        test_model = gen_models[0].name.replace('models/', '')
        print(f"\nTesting model: {test_model}")
        test_client = genai.GenerativeModel(test_model)
        response = test_client.generate_content("Say hello in one word")
        print(f"Test response: {response.text}")
        print("\n✅ SUCCESS! This model works!")
        print(f"\nUse this in your .env file:")
        print(f"GEMINI_MODEL={test_model}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
