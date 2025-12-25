"""
Shared JSON extraction and parsing utilities for Gemini responses.
Used by both ai/gemini_client.py and backend/routes/generation.py.

CRITICAL: Never call json.loads() directly on raw Gemini output.
Always use these helpers which handle markdown fences, truncation, and validation.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger("lumen")


def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences from text.
    Handles: ```json, ```python, ```, etc.
    
    Args:
        text: Raw text potentially containing fences
        
    Returns:
        Text with fences removed
    """
    if not text:
        return ""
    
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Skip fence lines
        if stripped.startswith("```"):
            continue
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


def extract_json_object(text: str) -> Optional[str]:
    """
    Robustly extract JSON object from potentially malformed text.
    
    Handles:
    - Markdown code fences (```json ... ```)
    - Preamble text before JSON
    - Trailing text after JSON
    - Incomplete/truncated responses
    
    Args:
        text: Raw text from Gemini (may contain markdown, preamble, etc.)
        
    Returns:
        Clean JSON string ready for json.loads(), or None if unrecoverable
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Quick check for incomplete responses (e.g., just "```json" or "{\n  \"segments")
    if len(text) < 20:
        logger.debug(f"[JSON Extract] Text too short to be valid JSON: {text!r}")
        return None
    
    # Remove markdown fences first
    if "```" in text:
        text = strip_markdown_fences(text)
    
    # Find first { and last }
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        logger.debug(f"[JSON Extract] No valid JSON object boundaries found (len={len(text)})")
        return None
    
    json_str = text[start_idx:end_idx + 1]
    
    # Validate by attempting parse
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        logger.debug(f"[JSON Extract] Invalid JSON after extraction: {e}")
        logger.debug(f"[JSON Extract] Attempted string (first 200 chars): {json_str[:200]}")
        return None


def parse_intent_json(text: str) -> Optional[dict]:
    """
    Parse and validate Gemini intent JSON.
    
    This is the CANONICAL parser for all Gemini intent outputs.
    Use this instead of json.loads() to handle malformed responses gracefully.
    
    Validation rules:
    - Must have "segments" key with non-empty list
    - Each segment must have: text (str), pause_after (num), emphasis (list), sentence_end (bool)
    
    Args:
        text: Raw text from Gemini
        
    Returns:
        Validated dict with "segments" key, or None if parsing/validation fails
    """
    # Step 1: Extract clean JSON string
    json_str = extract_json_object(text)
    if not json_str:
        logger.warning("[Intent Parse] JSON extraction failed")
        return None
    
    # Step 2: Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"[Intent Parse] JSON decode failed: {e}")
        return None
    
    # Step 3: Validate schema
    if not isinstance(data, dict):
        logger.warning("[Intent Parse] Parsed JSON is not a dict")
        return None
    
    if "segments" not in data:
        logger.warning("[Intent Parse] Missing 'segments' key")
        return None
    
    segments = data["segments"]
    if not isinstance(segments, list) or len(segments) == 0:
        logger.warning(f"[Intent Parse] Invalid segments: {type(segments).__name__} with length {len(segments) if isinstance(segments, list) else 'N/A'}")
        return None
    
    # Step 4: Validate each segment
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            logger.warning(f"[Intent Parse] Segment {i} is not a dict")
            return None
        
        # Required fields
        required = ["text", "pause_after", "emphasis", "sentence_end"]
        for field in required:
            if field not in seg:
                logger.warning(f"[Intent Parse] Segment {i} missing required field: {field}")
                return None
        
        # Type validation
        if not isinstance(seg["text"], str):
            logger.warning(f"[Intent Parse] Segment {i} text is not string")
            return None
        
        if not isinstance(seg["pause_after"], (int, float)):
            logger.warning(f"[Intent Parse] Segment {i} pause_after is not numeric")
            return None
        
        if not isinstance(seg["emphasis"], list):
            logger.warning(f"[Intent Parse] Segment {i} emphasis is not list")
            return None
        
        if not isinstance(seg["sentence_end"], bool):
            logger.warning(f"[Intent Parse] Segment {i} sentence_end is not bool")
            return None
    
    logger.debug(f"[Intent Parse] ✓ Validated {len(segments)} segments")
    return data


def json_to_script_intent(data: dict) -> Optional["ScriptIntent"]:
    """
    Convert validated JSON dict to ScriptIntent object.
    
    Args:
        data: Validated dict from parse_intent_json()
        
    Returns:
        ScriptIntent instance or None if import/conversion fails
    """
    try:
        from ai.script_intent import ScriptIntent
        return ScriptIntent.from_dict(data)
    except Exception as e:
        logger.error(f"[Intent Parse] Failed to convert to ScriptIntent: {e}")
        return None
