"""
Gemini Client Wrapper
Stateless, production-safe Gemini integration with intent propagation.

Key guarantees:
- Never hard-fails downstream video pipeline due to JSON formatting
- Automatic repair + retry for malformed Gemini outputs
- Clean fallback to simple intent if structured output fails
- Safe for concurrent backend usage (no chat state)

ARCHITECTURAL ROLE:
Gemini = Script + semantic intent generator

INTERFACE CONTRACT (refactored 2025-12-25):
- generate() accepts force_json: bool = False parameter
- When force_json=True: Uses ONLY response_mime_type="application/json" (NO SCHEMA)
- When force_json=False: Standard text generation with manual JSON parsing
- All persona methods use 3-tier retry strategy:
  Tier 1: JSON mime type mode (force_json=True) with strict prompt
  Tier 2: No JSON mode (force_json=False) with soft prompt  
  Tier 3: Fallback to create_simple_intent (always succeeds, never crashes)
  
CRITICAL SDK LIMITATION:
The deprecated google.generativeai SDK does NOT support complex JSON schemas.
❌ response_schema with nested arrays/objects causes: TypeError: unhashable type: 'list'
❌ Union types like "type": ["number", "null"] are NOT supported
✅ We use response_mime_type="application/json" ONLY and enforce structure via prompt.
  
ROBUSTNESS FEATURES:
- _extract_json_object(): Handles markdown fences, preambles, incomplete responses
- parse_gemini_intent_output(): Validates segments exist and are non-empty
- 3-tier retry strategy: Degrades gracefully from strict JSON → soft JSON → simple intent
- Comprehensive logging for debugging (response length, previews, tier status)
- Safe handling of quota exhaustion and malformed responses
- Pipeline NEVER crashes - always returns usable intent
"""

import os
import json
import logging
from typing import Optional, Tuple, Dict, Any

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# Shared JSON parsing (CANONICAL - use this, not ad-hoc json.loads)
from ai.json_utils import parse_intent_json, json_to_script_intent

# Intent contract
try:
    from ai.script_intent import (
        ScriptIntent,
        parse_gemini_intent_output,
        create_simple_intent,
    )
    INTENT_AVAILABLE = True
except ImportError:
    ScriptIntent = None
    INTENT_AVAILABLE = False

logger = logging.getLogger("lumen")


# ----------------------------
# Utility: JSON sanitization
# ----------------------------

def _sanitize_json_response(text: Optional[str]) -> Optional[str]:
    """
    Remove markdown fences and invalid preambles from Gemini output.
    Returns cleaned JSON string or None if unrecoverable.
    """
    if not text:
        return None

    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        lines = [
            line for line in text.splitlines()
            if not line.strip().startswith("```")
        ]
        text = "\n".join(lines).strip()

    # Must start with a JSON object
    if not text.startswith("{"):
        return None

    # Must end with }
    end = text.rfind("}")
    if end == -1:
        return None

    return text[: end + 1]


def _extract_json_object(text: str) -> Optional[str]:
    """
    Robust JSON extraction that handles:
    - Plain JSON objects
    - Markdown code fences: ```json {...} ```
    - Preamble text before JSON
    - Trailing text after JSON
    - Incomplete responses (e.g., just "```json" with no content)
    
    Returns:
        Cleaned JSON string ready for json.loads(), or None if unrecoverable
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Handle incomplete responses (e.g., "```json" only)
    if len(text) < 20 and "```" in text:
        logger.warning(f"[JSON Extract] Incomplete response detected: {text!r}")
        return None
    
    # Extract from markdown code fences
    if "```" in text:
        import re
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            # Malformed fence - try to strip prefix
            text = text.replace("```json", "").replace("```", "").strip()
    
    # Find first { and last }
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        logger.warning(f"[JSON Extract] No valid JSON object found in response (len={len(text)})")
        return None
    
    json_str = text[start_idx:end_idx + 1]
    
    # Validate by attempting parse
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        logger.warning(f"[JSON Extract] Invalid JSON after extraction: {e}")
        logger.debug(f"[JSON Extract] Extracted string (first 200 chars): {json_str[:200]}")
        return None


# ----------------------------
# Gemini Client
# ----------------------------

class GeminiClient:
    """
    Stateless Gemini API wrapper with intent awareness.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

        logger.info(f"[OK] GeminiClient initialized ({model_name})")

    # ----------------------------
    # Low-level generation
    # ----------------------------

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
force_json: bool = False,
    ) -> str:
        """
        Generate text from Gemini.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens
            force_json: If True, request JSON output via response_mime_type ONLY (no schema)
        
        Returns:
            Generated text (or JSON string if force_json=True)
            
        IMPORTANT: The deprecated google.generativeai SDK does NOT support complex JSON schemas.
        We use response_mime_type="application/json" ONLY and enforce structure via prompt.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Build generation config
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Enable JSON mode if requested (MIME TYPE ONLY - NO SCHEMA)
            # The deprecated SDK crashes on complex schemas with union types or nested arrays
            if force_json:
                logger.debug(f"[Gemini] JSON mode enabled (mime type only, no schema) - model={self.model_name}, tokens={max_tokens}")
                generation_config.response_mime_type = "application/json"
                # ❌ DO NOT USE response_schema - causes "unhashable type: 'list'" errors

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            result = response.text or ""
            
            # Log response preview for debugging
            logger.debug(f"[Gemini] Response length: {len(result)} chars, force_json={force_json}")
            if len(result) < 500:
                logger.debug(f"[Gemini] Full response: {result}")
            else:
                logger.debug(f"[Gemini] Response preview: {result[:200]}...")
            
            # If force_json, attempt extraction and validation
            if force_json:
                extracted = _extract_json_object(result)
                if not extracted:
                    logger.warning(f"[Gemini] JSON extraction failed from response (len={len(result)})")
                    # Return raw response - let caller decide whether to retry
                    return result
                return extracted
            
            return result
        
        except ResourceExhausted as e:
            logger.error(f"[Gemini] ❌ QUOTA EXHAUSTED - {e}")
            logger.error("[Gemini] Returning None - caller should proceed with fallback")
            return None
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                logger.error(f"[Gemini] ❌ QUOTA/RATE LIMIT - {e}")
                logger.error("[Gemini] Returning None - caller should proceed with fallback")
                return None
            logger.error(f"[Gemini] Generation failed (force_json={force_json}): {e}")
            raise RuntimeError(f"Gemini API error: {e}")

    # ----------------------------
    # SINGLE-CALL API (No Retries)
    # ----------------------------

    def generate_once(
        self,
        prompt: str,
        *,
        persona: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Optional[Tuple[str, Optional[ScriptIntent]]]:
        """
        SINGLE-CALL GEMINI API - Makes exactly ONE request, no retries.
        
        This is the ONLY method that should be called from the backend for /api/generate/full.
        Enforces architectural constraint: ONE Gemini call per API request.
        
        Args:
            prompt: User's request
            persona: "mkbhd" or "ijustine"
            max_tokens: Maximum tokens (default 4096 for comprehensive responses)
            temperature: Sampling temperature
            
        Returns:
            (script_text, script_intent) if successful
            None if Gemini call fails (quota, error, etc.)
            
        GUARANTEES:
        - Makes exactly ONE Gemini API call
        - Catches ALL exceptions internally
        - Returns None on ANY error (never raises)
        - No retries, no tiers, no fallback Gemini calls
        """
        logger.info(f"[Gemini] CALLING GEMINI ONCE for {persona} script generation (max_tokens={max_tokens})")
        
        # Build comprehensive single prompt that requests BOTH script AND intent
        if persona.lower() == "mkbhd":
            style_desc = """MKBHD (Marques Brownlee) style:
- Calm, professional, measured tone
- Well-researched insights with specific details
- Clear comparisons when evaluating options
- Honest, balanced perspective
- Natural pacing with thoughtful pauses
- Technical accuracy without jargon overload"""
            persona_name = "Marques Brownlee (MKBHD)"
        else:  # ijustine
            style_desc = """iJustine style:
- Energetic, enthusiastic, upbeat tone
- Fun and relatable personality
- Excited about new technology
- Friendly and conversational
- Quick pacing with natural energy
- Makes tech accessible and enjoyable"""
            persona_name = "iJustine"
        
        full_prompt = f"""You are {persona_name}, a tech content creator.

{style_desc}

User's Question: {prompt}

Task: Write a complete spoken script that answers this question in your unique style.

Requirements:
1. Length: 120-180 words (8-12 sentences)
2. Style: Authentic {persona} voice and tone
3. Content: Helpful, specific, actionable advice
4. Structure: Natural flow with clear sentence boundaries
5. Quality: Actually answer the question (don't just echo it back)

OPTIONAL: If possible, include timing metadata as JSON at the end:
{{
  "segments": [
    {{"text": "sentence", "pause_after": 0.3, "emphasis": ["word"], "sentence_end": true}}
  ]
}}

Prioritize script quality over structure. If you can't provide perfect JSON, that's fine - just give the best script you can.

Your script:
""".strip()
        
        try:
            # Make the SINGLE Gemini call
            raw_response = self.generate(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                force_json=False  # Don't force JSON - accept any format
            )
            
            # Check for quota exhaustion (generate() returns None)
            if raw_response is None:
                logger.error(f"[Gemini] ❌ GEMINI CALL FAILED (quota exhausted or error) - returning None")
                return None
            
            logger.info(f"[Gemini] ✓ Gemini response received: {len(raw_response)} chars")
            
            # Try to extract intent from response
            script_text = raw_response
            script_intent = None
            
            if INTENT_AVAILABLE:
                # Attempt to parse embedded intent JSON
                try:
                    data = parse_intent_json(raw_response)
                    if data:
                        script_intent = json_to_script_intent(data)
                        if script_intent and len(script_intent.segments) > 0:
                            # Extract clean script text from segments
                            script_text = " ".join(seg.text for seg in script_intent.segments)
                            logger.info(f"[Gemini] ✓ Parsed intent: {len(script_intent.segments)} segments")
                except Exception as e:
                    logger.warning(f"[Gemini] Intent parsing failed (will build locally): {e}")
            
            # If no intent was parsed, we'll return None for intent (backend will build it locally)
            if script_intent is None:
                logger.info(f"[Gemini] No structured intent in response - backend will build locally")
            
            return (script_text, script_intent)
            
        except ResourceExhausted as e:
            logger.error(f"[Gemini] ❌ QUOTA EXHAUSTED - {e}")
            logger.error("[Gemini] Returning None - backend will use local fallback")
            return None
        except Exception as e:
            # Catch ALL exceptions - never let errors propagate
            if "429" in str(e) or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                logger.error(f"[Gemini] ❌ QUOTA/RATE LIMIT - {e}")
            else:
                logger.error(f"[Gemini] ❌ GEMINI CALL FAILED - {e}")
            logger.error("[Gemini] Returning None - backend will use local fallback")
            return None

    # ----------------------------
    # Core intent-aware generator
    # ----------------------------

    def generate_with_intent(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> Tuple[str, Optional["ScriptIntent"]]:
        """
        Generic intent-aware generation with 3-tier retry strategy.
        
        Tier 1: force_json=True (JSON mime type, strict prompt)
        Tier 2: force_json=False (no JSON mode, soft prompt)
        Tier 3: Fallback to create_simple_intent (always succeeds)
        
        Pipeline NEVER crashes - we degrade gracefully to simple intent.
        """

        if not INTENT_AVAILABLE:
            text = self.generate(prompt, temperature, max_tokens, force_json=False)
            return text, None

        # ---- TIER 1: JSON mode with strict prompt ----
        strict_prompt = f"""
You are a script writer. Output ONLY a valid JSON object.

Format (STRICTLY follow this structure):
{{
  "segments": [
    {{
      "text": "sentence content here",
      "pause_after": 0.3,
      "emphasis": [],
      "sentence_end": true
    }}
  ]
}}

Rules:
- NO markdown fences
- NO explanations
- NO text before or after JSON
- Start with {{ and end with }}

Topic: {prompt}
""".strip()

        try:
            logger.info("[Gemini] Tier 1: JSON mime type mode")
            raw = self.generate(strict_prompt, temperature, max_tokens, force_json=True)
            
            # Check for quota exhaustion
            if raw is None:
                logger.error("[Gemini] Tier 1 returned None (quota exhausted), skipping to Tier 3")
            else:
                intent = parse_gemini_intent_output(raw)
                if intent and len(intent.segments) > 0:
                    plain_text = " ".join(seg.text for seg in intent.segments)
                    logger.info(f"[Gemini] ✓ Tier 1 success: {len(intent.segments)} segments")
                    return plain_text, intent
                else:
                    logger.warning("[Gemini] Tier 1: Parsed but no segments, trying Tier 2")
        except Exception as e:
            logger.warning(f"[Gemini] Tier 1 failed: {e}")

        # ---- TIER 2: No JSON mode, soft prompt ----
        soft_prompt = f"""
Write a script about: {prompt}

Return as JSON (no markdown):
{{
  "segments": [
    {{"text": "...", "pause_after": 0.3, "emphasis": [], "sentence_end": true}}
  ]
}}
""".strip()

        try:
            logger.info("[Gemini] Tier 2: No JSON mode (soft prompt)")
            raw = self.generate(soft_prompt, temperature=0.5, max_tokens=600, force_json=False)
            
            # Check for quota exhaustion
            if raw is None:
                logger.error("[Gemini] Tier 2 returned None (quota exhausted), skipping to Tier 3")
            else:
                intent = parse_gemini_intent_output(raw)
                if intent and len(intent.segments) > 0:
                    plain_text = " ".join(seg.text for seg in intent.segments)
                    logger.info(f"[Gemini] ✓ Tier 2 success: {len(intent.segments)} segments")
                    return plain_text, intent
                else:
                    logger.warning("[Gemini] Tier 2: Parsed but no segments, using Tier 3 fallback")
        except Exception as e:
            logger.warning(f"[Gemini] Tier 2 failed: {e}")

        # ---- TIER 3: Fallback (always succeeds, never crashes pipeline) ----
        logger.warning("[Gemini] Tier 3: Fallback to simple intent")
        try:
            # Try to get plain text if previous attempts gave us something
            fallback_prompt = f"Write a short script (100-150 words) about: {prompt}"
            plain_text = self.generate(fallback_prompt, temperature=0.6, max_tokens=400, force_json=False)
            
            # Check for quota exhaustion - use prompt as last resort
            if plain_text is None:
                logger.error("[Gemini] Tier 3 returned None (quota exhausted), using prompt as text")
                plain_text = prompt
            
            intent = create_simple_intent(plain_text, pause_after=0.3)
            logger.info(f"[Gemini] ✓ Tier 3 fallback: simple intent created")
            return plain_text, intent
        except Exception as e:
            # Absolute last resort - use the prompt itself
            logger.error(f"[Gemini] Tier 3 fallback failed: {e}, using prompt as text")
            intent = create_simple_intent(prompt, pause_after=0.3)
            return prompt, intent

    # ----------------------------
    # Persona: MKBHD
    # ----------------------------

    def generate_mkbhd_script(
        self,
        prompt: str,
        temperature: float = 0.6,
        max_tokens: int = 1500,
    ) -> Tuple[str, Optional["ScriptIntent"]]:
        """
        Generate MKBHD-style script with intent.
        Uses 3-tier retry strategy - never crashes pipeline.
        """
        if not INTENT_AVAILABLE:
            text = self.generate(prompt, temperature, max_tokens, force_json=False)
            return text, None

        # ---- TIER 1: JSON mode ----
        tier1_prompt = f"""
You are Marques Brownlee (MKBHD). Write a tech review script.

Style: Calm, professional, measured, clear.

Output ONLY this JSON structure (no markdown, no explanations):
{{
  "segments": [
    {{"text": "sentence", "pause_after": 0.4, "emphasis": [], "sentence_end": true}}
  ]
}}

Topic: {prompt}
""".strip()

        try:
            logger.info("[Gemini:MKBHD] Tier 1: JSON mode")
            raw = self.generate(tier1_prompt, temperature, max_tokens, force_json=True)
            intent = parse_gemini_intent_output(raw)
            if intent and len(intent.segments) > 0:
                plain_text = " ".join(seg.text for seg in intent.segments)
                logger.info(f"[Gemini:MKBHD] ✓ Tier 1 success: {len(intent.segments)} segments")
                return plain_text, intent
        except Exception as e:
            logger.warning(f"[Gemini:MKBHD] Tier 1 failed: {e}")

        # ---- TIER 2: No JSON mode ----
        tier2_prompt = f"""
MKBHD-style tech script about: {prompt}

Return JSON (no fences):
{{"segments": [{{"text": "...", "pause_after": 0.4, "emphasis": [], "sentence_end": true}}]}}
""".strip()

        try:
            logger.info("[Gemini:MKBHD] Tier 2: No JSON mode")
            raw = self.generate(tier2_prompt, temperature=0.5, max_tokens=1000, force_json=False)
            intent = parse_gemini_intent_output(raw)
            if intent and len(intent.segments) > 0:
                plain_text = " ".join(seg.text for seg in intent.segments)
                logger.info(f"[Gemini:MKBHD] ✓ Tier 2 success: {len(intent.segments)} segments")
                return plain_text, intent
        except Exception as e:
            logger.warning(f"[Gemini:MKBHD] Tier 2 failed: {e}")

        # ---- TIER 3: Fallback (delegate to generic intent generator) ----
        logger.warning("[Gemini:MKBHD] Tier 3: Fallback to generic intent")
        return self.generate_with_intent(prompt, temperature=0.5, max_tokens=800)

    # ----------------------------
    # Persona: iJustine
    # ----------------------------

    def generate_ijustine_script(
        self,
        prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 1500,
    ) -> Tuple[str, Optional["ScriptIntent"]]:
        """
        Generate iJustine-style script with intent.
        Uses 3-tier retry strategy - never crashes pipeline.
        """
        if not INTENT_AVAILABLE:
            text = self.generate(prompt, temperature, max_tokens, force_json=False)
            return text, None

        # ---- TIER 1: JSON mode ----
        tier1_prompt = f"""
You are iJustine. Write an energetic tech video script.

Style: Energetic, excited, friendly, conversational.

Output ONLY this JSON structure (no markdown, no explanations):
{{
  "segments": [
    {{"text": "sentence", "pause_after": 0.25, "emphasis": ["word"], "sentence_end": false}}
  ]
}}

Topic: {prompt}
""".strip()

        try:
            logger.info("[Gemini:iJustine] Tier 1: JSON mode")
            raw = self.generate(tier1_prompt, temperature, max_tokens, force_json=True)
            intent = parse_gemini_intent_output(raw)
            if intent and len(intent.segments) > 0:
                plain_text = " ".join(seg.text for seg in intent.segments)
                logger.info(f"[Gemini:iJustine] ✓ Tier 1 success: {len(intent.segments)} segments")
                return plain_text, intent
        except Exception as e:
            logger.warning(f"[Gemini:iJustine] Tier 1 failed: {e}")

        # ---- TIER 2: No JSON mode ----
        tier2_prompt = f"""
iJustine-style excited script about: {prompt}

Return JSON (no fences):
{{"segments": [{{"text": "...", "pause_after": 0.25, "emphasis": ["word"], "sentence_end": false}}]}}
""".strip()

        try:
            logger.info("[Gemini:iJustine] Tier 2: No JSON mode")
            raw = self.generate(tier2_prompt, temperature=0.6, max_tokens=1000, force_json=False)
            intent = parse_gemini_intent_output(raw)
            if intent and len(intent.segments) > 0:
                plain_text = " ".join(seg.text for seg in intent.segments)
                logger.info(f"[Gemini:iJustine] ✓ Tier 2 success: {len(intent.segments)} segments")
                return plain_text, intent
        except Exception as e:
            logger.warning(f"[Gemini:iJustine] Tier 2 failed: {e}")

        # ---- TIER 3: Fallback (delegate to generic intent generator) ----
        logger.warning("[Gemini:iJustine] Tier 3: Fallback to generic intent")
        return self.generate_with_intent(prompt, temperature=0.7, max_tokens=800)

    # ----------------------------
    # CANONICAL persona generation (for backend use)
    # ----------------------------

    def generate_persona_intent(
        self,
        persona: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        stronger_constraints: bool = False,
    ) -> Tuple[str, ScriptIntent, Dict[str, Any]]:
        """
        CANONICAL method for generating persona-specific scripts with intent.
        Used by backend to eliminate duplicated retry logic.
        
        Args:
            persona: "mkbhd" or "ijustine"
            prompt: User's request
            temperature: Sampling temperature
            max_tokens: Max output tokens
            stronger_constraints: If True, use longer/more detailed prompt
            
        Returns:
            (script_text, script_intent, meta_dict)
            
        Meta dict contains:
            - intent_source: "tier1_json" | "tier2_prompt" | "tier3_fallback" | "stronger_retry"
            - parse_ok: bool
            - words: int
            - segments: int
            - tier_attempts: list of tier names tried
        """
        meta = {
            "intent_source": None,
            "parse_ok": False,
            "words": 0,
            "segments": 0,
            "tier_attempts": [],
        }
        
        if not INTENT_AVAILABLE:
            text = self.generate(prompt, temperature, max_tokens, force_json=False)
            intent = None
            meta["intent_source"] = "no_intent_available"
            meta["words"] = len(text.split())
            return text, intent, meta
        
        # Build persona-specific prompt
        if stronger_constraints:
            # STRONGER CONSTRAINTS: force longer, more detailed responses
            if persona.upper() == "MKBHD":
                persona_prompt = f"""
You are Marques Brownlee (MKBHD), tech reviewer. Write a detailed, helpful tech review script.

USER REQUEST: {prompt}

REQUIREMENTS:
- 6-10 segments (each segment = 1-3 sentences)
- 120-180 words total
- Calm, measured, professional tone
- Include specific recommendations with reasoning
- Compare at least 2 options if relevant
- Consider: budget, size, battery, camera, ecosystem
- End with clear recommendation

Output ONLY JSON (no markdown, no fences):
{{
  "segments": [
    {{"text": "opening sentence", "pause_after": 0.4, "emphasis": [], "sentence_end": true}},
    {{"text": "detailed point 1", "pause_after": 0.4, "emphasis": ["key_word"], "sentence_end": true}},
    ...
  ]
}}
""".strip()
                temp = 0.5
            else:  # iJustine
                persona_prompt = f"""
You are iJustine, energetic tech YouTuber. Write an excited, detailed tech video script.

USER REQUEST: {prompt}

REQUIREMENTS:
- 6-10 segments (each segment = 1-3 sentences)
- 120-180 words total
- Energetic, friendly, conversational tone
- Include specific recommendations with enthusiasm
- Compare at least 2 options if relevant
- Make it fun and relatable
- End with clear recommendation

Output ONLY JSON (no markdown, no fences):
{{
  "segments": [
    {{"text": "opening sentence", "pause_after": 0.25, "emphasis": ["exciting"], "sentence_end": false}},
    {{"text": "detailed point 1", "pause_after": 0.3, "emphasis": ["word"], "sentence_end": true}},
    ...
  ]
}}
""".strip()
                temp = 0.6
            
            meta["intent_source"] = "stronger_retry"
        else:
            # Standard persona generation
            if persona.upper() == "MKBHD":
                return_text, return_intent = self.generate_mkbhd_script(prompt, temperature, max_tokens)
                meta["intent_source"] = "mkbhd_method"
            else:
                return_text, return_intent = self.generate_ijustine_script(prompt, temperature, max_tokens)
                meta["intent_source"] = "ijustine_method"
            
            if return_intent:
                meta["parse_ok"] = True
                meta["words"] = len(return_text.split())
                meta["segments"] = len(return_intent.segments)
            
            return return_text, return_intent, meta
        
        # Stronger constraints: 3-tier retry with shared parser
        # ---- TIER 1: JSON mode ----
        meta["tier_attempts"].append("tier1_json")
        try:
            logger.info(f"[Gemini:{persona}] Stronger Tier 1: JSON mode")
            raw = self.generate(persona_prompt, temp, max_tokens, force_json=True)
            
            # Check for quota exhaustion
            if raw is None:
                logger.error(f"[Gemini:{persona}] Tier 1 returned None (quota exhausted)")
                meta["tier_attempts"].append("tier1_quota_exhausted")
                # Skip to absolute fallback
                raise Exception("Quota exhausted in Tier 1")
            
            # Use SHARED parser (canonical)
            data = parse_intent_json(raw)
            if data:
                intent = json_to_script_intent(data)
                if intent and len(intent.segments) > 0:
                    plain_text = " ".join(seg.text for seg in intent.segments)
                    meta["intent_source"] = "stronger_tier1_json"
                    meta["parse_ok"] = True
                    meta["words"] = len(plain_text.split())
                    meta["segments"] = len(intent.segments)
                    logger.info(f"[Gemini:{persona}] ✓ Stronger Tier 1 success: {len(intent.segments)} segments")
                    return plain_text, intent, meta
        except Exception as e:
            logger.warning(f"[Gemini:{persona}] Stronger Tier 1 failed: {e}")
        
        # ---- TIER 2: No JSON mode ----
        meta["tier_attempts"].append("tier2_prompt")
        tier2_prompt = f"{persona_prompt}\n\n(Output JSON without code fences)"
        try:
            logger.info(f"[Gemini:{persona}] Stronger Tier 2: No JSON mode")
            raw = self.generate(tier2_prompt, temp, max_tokens=1200, force_json=False)
            
            # Check for quota exhaustion
            if raw is None:
                logger.error(f"[Gemini:{persona}] Tier 2 returned None (quota exhausted)")
                meta["tier_attempts"].append("tier2_quota_exhausted")
                raise Exception("Quota exhausted in Tier 2")
            
            # Use SHARED parser (canonical)
            data = parse_intent_json(raw)
            if data:
                intent = json_to_script_intent(data)
                if intent and len(intent.segments) > 0:
                    plain_text = " ".join(seg.text for seg in intent.segments)
                    meta["intent_source"] = "stronger_tier2_prompt"
                    meta["parse_ok"] = True
                    meta["words"] = len(plain_text.split())
                    meta["segments"] = len(intent.segments)
                    logger.info(f"[Gemini:{persona}] ✓ Stronger Tier 2 success: {len(intent.segments)} segments")
                    return plain_text, intent, meta
        except Exception as e:
            logger.warning(f"[Gemini:{persona}] Stronger Tier 2 failed: {e}")
        
        # ---- TIER 3: Fallback ----
        meta["tier_attempts"].append("tier3_fallback")
        logger.warning(f"[Gemini:{persona}] Stronger Tier 3: Fallback to simple intent")
        try:
            fallback_prompt = f"Write a detailed {persona}-style tech script (120-180 words) about: {prompt}"
            plain_text = self.generate(fallback_prompt, temp, max_tokens=500, force_json=False)
            
            # Check for quota exhaustion
            if plain_text is None:
                logger.error(f"[Gemini:{persona}] Tier 3 returned None (quota exhausted), using absolute fallback")
                meta["tier_attempts"].append("tier3_quota_exhausted")
                raise Exception("Quota exhausted in Tier 3")
            
            intent = create_simple_intent(plain_text, pause_after=0.3)
            meta["intent_source"] = "stronger_tier3_fallback"
            meta["parse_ok"] = True  # simple intent is always valid
            meta["words"] = len(plain_text.split())
            meta["segments"] = len(intent.segments) if intent else 1
            logger.info(f"[Gemini:{persona}] ✓ Stronger Tier 3 fallback: simple intent created")
            return plain_text, intent, meta
        except Exception as e:
            # Absolute last resort
            logger.error(f"[Gemini:{persona}] Stronger Tier 3 fallback failed: {e}, using prompt as text")
            intent = create_simple_intent(prompt, pause_after=0.3)
            meta["intent_source"] = "absolute_fallback"
            meta["parse_ok"] = True
            meta["words"] = len(prompt.split())
            meta["segments"] = 1
            return prompt, intent, meta

    # ----------------------------
    # Async compatibility
    # ----------------------------

    async def generate_async(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        force_json: bool = False,
    ) -> str:
        """Async wrapper for generate(). Delegates to synchronous implementation."""
        return self.generate(prompt, temperature, max_tokens, force_json)
