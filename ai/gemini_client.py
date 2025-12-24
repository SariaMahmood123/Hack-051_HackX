"""
Gemini Client Wrapper
Handles stateless text generation via Google Gemini API
Refactored for concurrent backend usage without shared state
"""
import os
import logging
from typing import Optional
import google.generativeai as genai

logger = logging.getLogger("lumen")


class GeminiClient:
    """
    Stateless wrapper for Gemini API
    
    Key design decisions:
    - Uses generate_content() instead of chat sessions (stateless, concurrent-safe)
    - Limits response tokens to keep responses fast and reduce quota usage
    - No shared state between requests (safe for FastAPI backend)
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model identifier (e.g., "gemini-2.5-flash")
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        # Validate API key format
        if not self.api_key.startswith("AIza") or len(self.api_key) < 35:
            logger.warning("GEMINI_API_KEY has unexpected format. Expected format: AIza... (39 chars)")
        
        # Configure API
        genai.configure(api_key=self.api_key)
        
        # Store model name for error messages
        self.model_name = model_name
        
        # Create model instance - SDK handles models/ prefix internally
        self.model = genai.GenerativeModel(model_name)
        
        logger.info(f"[OK] Initialized GeminiClient with model: {model_name}")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 150) -> str:
        """
        Generate text response for a given prompt (stateless)
        
        This method is stateless and safe for concurrent backend requests.
        Each call is independent - no shared chat sessions or state.
        
        Args:
            prompt: User input text
        
        Returns:
            Generated text response
        
        Raises:
            ValueError: Invalid prompt or configuration
            RuntimeError: Generation failed (network, quota, model error)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        try:
            # Use generate_content() for stateless generation
            # This is safer for concurrent backend usage than chat sessions
            # Each request is independent with no shared state
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        except ValueError as e:
            # API key or configuration errors
            logger.error(f"Gemini configuration error: {str(e)}", exc_info=True)
            raise ValueError(f"Invalid Gemini configuration: {str(e)}")
        
        except Exception as e:
            # Capture API-specific errors
            error_msg = str(e)
            logger.error(f"Gemini generation failed: {error_msg}", exc_info=True)
            
            # Provide specific error messages based on error type
            if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                raise RuntimeError("Gemini API key is invalid. Please check your GEMINI_API_KEY in .env file.")
            elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise RuntimeError(f"Gemini API rate limit exceeded. Please wait a moment and try again. (Current model: {self.model_name})")
            elif "404" in error_msg or "model not found" in error_msg.lower():
                raise RuntimeError(f"Gemini model '{self.model_name}' not found. Verify model name in .env file. Available: gemini-2.5-flash, gemini-2.5-pro")
            else:
                raise RuntimeError(f"Gemini generation failed: {error_msg}")
    
    async def generate_async(self, prompt: str, temperature: float = 0.7, max_tokens: int = 150) -> str:
        """
        Async version of generate (wraps sync call)
        
        Note: google.generativeai SDK doesn't have native async support yet,
        so this is a simple wrapper for compatibility with async endpoints.
        
        Args:
            prompt: User input text
            temperature: Creativity level (0.0-2.0)
            max_tokens: Maximum response length
        
        Returns:
            Generated text response
        """
        return self.generate(prompt, temperature, max_tokens)
