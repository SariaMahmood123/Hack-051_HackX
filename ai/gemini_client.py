"""
Gemini 2.0 Flash Client Wrapper
Handles text generation via Google Gemini API
"""
import os
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

logger = logging.getLogger("lumen")


class GeminiClient:
    """
    Wrapper for Gemini 2.0 Flash API
    Provides conversational text generation with history support
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model identifier
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        # Validate API key format
        if not self.api_key.startswith("AIza") or len(self.api_key) < 35:
            logger.warning("GEMINI_API_KEY has unexpected format. Expected format: AIza... (39 chars)")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.chat_session = None
    
    def start_chat(self, history: Optional[List[Dict]] = None):
        """
        Start a new chat session
        
        Args:
            history: Previous conversation history in format:
                     [{"role": "user", "parts": ["text"]}, {"role": "model", "parts": ["text"]}]
        """
        self.chat_session = self.model.start_chat(history=history or [])
    
    def generate(self, prompt: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Generate text response for a given prompt
        
        Args:
            prompt: User input text
            conversation_history: Optional conversation context
        
        Returns:
            Generated text response
        
        Raises:
            ValueError: Invalid API key or prompt
            RuntimeError: Generation failed (network, quota, model error)
        """
        try:
            # Start new chat with history if provided
            if conversation_history:
                self.start_chat(history=conversation_history)
            elif not self.chat_session:
                self.start_chat()
            
            # Generate response
            response = self.chat_session.send_message(prompt)
            return response.text
        
        except ValueError as e:
            # API key or configuration errors
            logger.error(f"Gemini configuration error: {str(e)}", exc_info=True)
            raise ValueError(f"Invalid Gemini configuration: {str(e)}")
        
        except Exception as e:
            # Capture API-specific errors
            error_msg = str(e)
            logger.error(f"Gemini generation failed: {error_msg}", exc_info=True)
            
            # Provide more specific error messages
            if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                raise RuntimeError("Gemini API key is invalid. Please check your GEMINI_API_KEY in .env file.")
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise RuntimeError("Gemini API quota exceeded or rate limited. Please try again later.")
            elif "404" in error_msg or "model not found" in error_msg.lower():
                raise RuntimeError(f"Gemini model '{self.model._model_name}' not found or not accessible.")
            else:
                raise RuntimeError(f"Gemini generation failed: {error_msg}")
    
    async def generate_async(self, prompt: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Async version of generate (wraps sync call for now)
        TODO: Use proper async implementation if available
        """
        return self.generate(prompt, conversation_history)
    
    def reset_chat(self):
        """Reset chat session"""
        self.chat_session = None
