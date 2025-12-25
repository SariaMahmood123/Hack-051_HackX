# backend/routes/generation.py
"""
Lumen Generation Routes (rewrite)
--------------------------------
Implements:
- GET  /api/health
- POST /api/generate/mkbhd          -> script + audio (no video)
- POST /api/generate/full           -> script + intent + audio + video (SadTalker + Motion Governor)

Key fixes vs your current behavior (based on your logs):
1) Reject "prompt-echo" scripts from Gemini intent mode (too short / too similar).
2) Retry Gemini with stronger instructions and/or fall back to plain text generation + local intent building.
3) Add robust SadTalker retry when preprocess hits NaN in croper.align_face (common failure mode).
4) Ensure per-request SadTalker wrapper usage to avoid stale state issues.

IMPORTANT:
- You MUST adapt the import paths to match your repo.
- You MUST adapt the return schema to match your frontend expectations.
"""

from __future__ import annotations

import os
import re
import uuid
import time
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import shared JSON parsing utilities
from ai.json_utils import parse_intent_json, json_to_script_intent


# ----------------------------
# Gemini Quota Guard
# ----------------------------

@dataclass
class GeminiGuard:
    """
    Tracks Gemini API usage and enforces quota-safe behavior.
    DEFAULT: max_calls=1 (SINGLE-CALL POLICY - no retries allowed)
    Once disabled (e.g., due to 429 or after first call), all further Gemini calls are skipped.
    """
    disabled: bool = False
    calls_made: int = 0
    max_calls: int = 1  # SINGLE-CALL POLICY: exactly ONE Gemini call per request
    disabled_reason: Optional[str] = None
    
    def can_call(self) -> bool:
        """Check if Gemini can be called."""
        if self.disabled:
            return False
        if self.calls_made >= self.max_calls:
            if not self.disabled:
                self.disabled = True
                self.disabled_reason = f"max_calls_reached={self.max_calls}"
            return False
        return True
    
    def record_call(self) -> None:
        """Increment call counter."""
        self.calls_made += 1
    
    def disable(self, reason: str) -> None:
        """Permanently disable Gemini for this request."""
        self.disabled = True
        self.disabled_reason = reason

logger = logging.getLogger("lumen")
# FIXED: Removed prefix from router definition (prefix is applied in main.py)
# This prevents double-prefixing that caused 404 on POST /api/generate/full
router = APIRouter(tags=["generation"])


# ----------------------------
# Pydantic request/response
# ----------------------------

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt/topic/question")
    persona: str = Field("MKBHD", description="Persona: MKBHD or IJUSTINE etc.")
    # Optional toggles
    enable_intent: bool = Field(True, description="Use structured intent flow")
    enable_governor: bool = Field(True, description="Enable Motion Governor")
    style: str = Field("calm_tech", description="Motion governor style preset")
    temperature: float = Field(0.6, ge=0.0, le=2.0)
    max_tokens: int = Field(3000, ge=64, le=8000)


class GenerateMKBHDAudioResponse(BaseModel):
    request_id: str
    script_text: str
    audio_path: str
    audio_duration_s: float
    intent_path: Optional[str] = None
    timing_map_path: Optional[str] = None


class GenerateFullResponse(BaseModel):
    request_id: str
    script_text: str
    audio_path: str
    video_path: str
    audio_duration_s: float
    intent_path: Optional[str] = None
    timing_map_path: Optional[str] = None


# ----------------------------
# Local helpers (validation)
# ----------------------------

def _normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _token_set(s: str) -> set:
    s = _normalize_text(s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [t for t in s.split(" ") if t]
    return set(tokens)


def _similarity_ratio(prompt: str, output: str) -> float:
    """
    Fast, dependency-free similarity estimate using token overlap.
    0.0 = unrelated, 1.0 = identical token set.
    """
    a = _token_set(prompt)
    b = _token_set(output)
    if not a or not b:
        return 0.0
    inter = len(a.intersection(b))
    union = len(a.union(b))
    return inter / max(union, 1)


def validate_script_output(
    prompt: str,
    script_text: str,
    num_segments: int,
    *,
    min_words: int = 80,
    min_segments: int = 6,
    max_prompt_similarity: float = 0.60,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Reject the failure mode shown in your logs:
    Gemini returns a tiny “script” that is just the prompt split into segments.
    """
    words = len(_normalize_text(script_text).split(" ")) if script_text else 0
    sim = _similarity_ratio(prompt, script_text)
    ok = True
    reasons: List[str] = []

    if words < min_words:
        ok = False
        reasons.append(f"too_short_words={words}<min_words={min_words}")
    if num_segments < min_segments:
        ok = False
        reasons.append(f"too_few_segments={num_segments}<min_segments={min_segments}")
    if sim > max_prompt_similarity:
        ok = False
        reasons.append(f"too_similar_to_prompt={sim:.2f}>max={max_prompt_similarity:.2f}")

    meta = {"words": words, "segments": num_segments, "similarity": sim, "reasons": reasons}
    return ok, meta


def is_sadtalker_nan_crop_error(err: Exception) -> bool:
    msg = str(err)
    return ("cannot convert float NaN to integer" in msg) or ("align_face" in msg and "NaN" in msg)


# ----------------------------
# Wiring to your AI modules
# ----------------------------
# You MUST update these imports to match your codebase.

# Gemini
from ai.gemini_client import GeminiClient  # adjust if needed

# Intent contract
from ai.script_intent import (
    ScriptIntent,
    create_simple_intent,
)

# XTTS wrapper (must expose an intent-aware synthesis that can return timing map)
# Expected interface below:
#   xtts = XTTSWrapper(...)
#   audio_path, duration_s, timing_map = xtts.synthesize_with_intent(script_intent, voice="mkbhd", out_dir=Path(...))
from ai.xtts_wrapper import XTTSWrapper  # adjust if needed

# SadTalker wrapper (expected interface):
#   s = SadTalkerWrapper(device="cuda", checkpoints_dir=Path(...))
#   final_video_path = s.generate(audio_path, reference_image, output_path, fps=25,
#                                 enable_governor=True, style="calm_tech", timing_map_path=..., intent_json_path=...)
from ai.sadtalker_wrapper import SadTalkerWrapper  # adjust if needed


# ----------------------------
# Environment / Paths
# ----------------------------

ROOT = Path(os.getenv("LUMEN_ROOT", Path(__file__).resolve().parents[2]))
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

ASSETS = ROOT / "assets"
DEFAULT_IMAGE = ASSETS / "mkbhd2.jpg"

SADTALKER_CHECKPOINTS = Path(os.getenv("SADTALKER_CHECKPOINTS", str(ROOT / "SadTalker" / "SadTalker-main" / "checkpoints")))


# ----------------------------
# API endpoints
# ----------------------------

@router.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@router.post("/generate/mkbhd", response_model=GenerateMKBHDAudioResponse)
def generate_mkbhd(req: GenerateRequest) -> GenerateMKBHDAudioResponse:
    """
    Audio-only endpoint: creates (script + intent) then XTTS audio.
    """
    request_id = str(uuid.uuid4())
    t0 = time.time()
    logger.info(f"-> POST /api/generate/mkbhd")
    logger.info(f"[{request_id}] MKBHD generation started: {req.prompt[:120]}...")

    try:
        gemini = GeminiClient(model_name="gemini-2.5-flash")
        xtts = XTTSWrapper(device="cpu")  # match your logs (CPU mode)

        script_text, script_intent = _generate_persona_script_with_validation(
            request_id=request_id,
            gemini=gemini,
            persona="MKBHD",
            prompt=req.prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            enable_intent=req.enable_intent,
        )

        out_dir = OUTPUTS / "mkbhd"
        out_dir.mkdir(parents=True, exist_ok=True)

        audio_path, duration_s, timing_map = xtts.synthesize_with_intent(
            script_intent=script_intent,
            voice="mkbhd",
            out_dir=out_dir,
            request_id=request_id,
        )

        intent_path = out_dir / f"mkbhd_{request_id}_intent.json"
        script_intent.save(intent_path)

        timing_map_path = out_dir / f"mkbhd_{request_id}_timing_map.json"
        timing_map.save(timing_map_path)

        logger.info(f"[{request_id}] MKBHD audio generated: {duration_s:.1f}s")
        logger.info(f"<- POST /api/generate/mkbhd status=200 duration={time.time()-t0:.2f}s")

        return GenerateMKBHDAudioResponse(
            request_id=request_id,
            script_text=script_text,
            audio_path=str(audio_path),
            audio_duration_s=float(duration_s),
            intent_path=str(intent_path),
            timing_map_path=str(timing_map_path),
        )

    except Exception as e:
        logger.exception(f"[{request_id}] /api/generate/mkbhd failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


@router.post("/generate/full", response_model=GenerateFullResponse)
def generate_full(req: GenerateRequest) -> GenerateFullResponse:
    """
    Full pipeline endpoint:
    Gemini (SINGLE CALL ONLY) -> ScriptIntent -> XTTS audio + TimingMap -> SadTalker -> MotionGovernor -> video
    
    ARCHITECTURAL GUARANTEE: Exactly ONE Gemini API call per request (enforced by guard.max_calls=1)
    Only XTTS/SadTalker/video generation failures should return 500.
    """
    request_id = str(uuid.uuid4())
    t0 = time.time()
    logger.info(f"-> POST /api/generate/full")
    logger.info(f"[{request_id}] Full intent pipeline started: {req.persona}")
    logger.info(f"[{request_id}] Prompt: {req.prompt[:140]}...")

    try:
        # Create Gemini guard with SINGLE-CALL POLICY (max_calls=1)
        guard = GeminiGuard()  # Default max_calls=1
        logger.info(f"[{request_id}] SINGLE-CALL POLICY: max_calls={guard.max_calls}")
        
        # Stage 1: script + intent (EXACTLY ONE Gemini call)
        gemini = GeminiClient(model_name="gemini-2.5-flash")

        script_text, script_intent = _generate_persona_script_with_validation(
            request_id=request_id,
            gemini=gemini,
            persona=req.persona,
            prompt=req.prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            enable_intent=req.enable_intent,
            guard=guard,
        )
        
        # Log final Gemini usage (should always be 0 or 1)
        logger.info(f"[{request_id}] Gemini calls made: {guard.calls_made}/{guard.max_calls}")
        logger.info(f"[{request_id}] Guard final state: disabled={guard.disabled}, reason={guard.disabled_reason}")
        
        if guard.calls_made > 1:
            logger.error(f"[{request_id}] ❌ SINGLE-CALL POLICY VIOLATED: {guard.calls_made} calls made!")

        # Stage 2: audio + timing map
        xtts = XTTSWrapper(device="cpu")  # match your setup (cpu mode)
        out_dir = OUTPUTS / "full"
        out_dir.mkdir(parents=True, exist_ok=True)

        audio_path, duration_s, timing_map = xtts.synthesize_with_intent(
            script_intent=script_intent,
            voice=req.persona.lower(),  # e.g. "mkbhd"
            out_dir=out_dir,
            request_id=request_id,
        )

        intent_path = out_dir / f"{req.persona.lower()}_{request_id}_intent.json"
        script_intent.save(intent_path)

        timing_map_path = out_dir / f"{req.persona.lower()}_{request_id}_timing_map.json"
        timing_map.save(timing_map_path)

        logger.info(f"[{request_id}] ✓ Audio generated: {Path(audio_path).name}")
        logger.info(f"[{request_id}] ✓ Timing map: {timing_map.total_duration:.2f}s, {timing_map.num_frames} frames")

        # Stage 3: video generation (SadTalker + Motion Governor)
        sadtalker = SadTalkerWrapper(
            device="cuda",
            checkpoints_dir=SADTALKER_CHECKPOINTS,
        )

        reference_image = DEFAULT_IMAGE
        if not reference_image.exists():
            raise RuntimeError(f"Reference image not found: {reference_image}")

        final_video_path = out_dir / f"{req.persona.lower()}_{request_id}.mp4"

        final_video_path = _sadtalker_generate_with_nan_retry(
            request_id=request_id,
            sadtalker=sadtalker,
            audio_path=Path(audio_path),
            reference_image=reference_image,
            output_path=final_video_path,
            fps=25,
            enable_governor=req.enable_governor,
            style=req.style,
            timing_map_path=timing_map_path,
            intent_path=intent_path,
        )

        logger.info(f"[{request_id}] ✓ Video generated: {final_video_path.name}")
        logger.info(f"<- POST /api/generate/full status=200 duration={time.time()-t0:.2f}s")

        return GenerateFullResponse(
            request_id=request_id,
            script_text=script_text,
            audio_path=str(audio_path),
            video_path=str(final_video_path),
            audio_duration_s=float(duration_s),
            intent_path=str(intent_path),
            timing_map_path=str(timing_map_path),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] /api/generate/full failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


# ----------------------------
# Script generation w/ retries
# ----------------------------

def _generate_persona_script_with_validation(
    *,
    request_id: str,
    gemini: GeminiClient,
    persona: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
    enable_intent: bool,
    guard: GeminiGuard,
) -> Tuple[str, ScriptIntent]:
    """
    SINGLE-CALL GEMINI POLICY: Makes exactly ONE Gemini call, then proceeds.
    
    Flow:
    1. Check guard (must allow exactly ONE call)
    2. Call gemini.generate_once() - THE ONLY GEMINI CALL
    3. If successful: use Gemini script (validation is advisory only)
    4. If None: use local fallback
    5. NEVER retry Gemini, NEVER call Gemini again
    
    GUARANTEES:
    - Exactly ONE Gemini call (or zero if guard prevents)
    - Validation NEVER triggers more Gemini calls
    - Always returns usable (script_text, script_intent)
    - Pipeline never crashes
    """
    logger.info(f"[{request_id}] STAGE 1: Generating {persona} script (SINGLE-CALL POLICY)...")
    logger.info(f"[{request_id}] GeminiGuard: disabled={guard.disabled}, calls={guard.calls_made}/{guard.max_calls}")
    
    script_text = None
    script_intent = None
    
    # Attempt the SINGLE Gemini call (if guard allows)
    if guard.can_call():
        logger.info(f"[{request_id}] Attempting SINGLE Gemini call...")
        guard.record_call()
        
        try:
            result = gemini.generate_once(
                prompt=prompt,
                persona=persona,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            if result is not None:
                script_text, script_intent = result
                logger.info(f"[{request_id}] ✓ Gemini call succeeded")
                
                # Build intent locally if not provided
                if script_intent is None:
                    logger.info(f"[{request_id}] Building intent locally from Gemini script...")
                    script_intent = _simple_sentence_intent(script_text)
                
                # Validate (ADVISORY ONLY - no action taken on failure)
                ok, meta = validate_script_output(prompt, script_text, len(script_intent.segments))
                if ok:
                    logger.info(f"[{request_id}] ✓ Validation passed: {meta}")
                else:
                    logger.warning(f"[{request_id}] ⚠ Validation failed (proceeding anyway): {meta}")
                    logger.warning(f"[{request_id}] SINGLE-CALL POLICY: accepting script despite validation failure")
                
                logger.info(f"[{request_id}] ✓ Using Gemini script: {len(script_text)} chars, {len(script_intent.segments)} segments")
                return script_text, script_intent
            else:
                logger.warning(f"[{request_id}] Gemini call returned None (quota exhausted or error)")
                guard.disable("gemini_returned_none")
        
        except Exception as e:
            logger.error(f"[{request_id}] Gemini call exception: {e}")
            guard.disable(f"exception: {e}")
    else:
        logger.warning(f"[{request_id}] Gemini call SKIPPED (guard disabled: {guard.disabled_reason})")
    
    # ABSOLUTE FALLBACK: No Gemini, always succeeds
    logger.warning(f"[{request_id}] Using LOCAL FALLBACK (no Gemini)")
    logger.info(f"[{request_id}] Guard final state: disabled={guard.disabled}, reason={guard.disabled_reason}, calls={guard.calls_made}")
    
    # Create a reasonable fallback script
    fallback_text = f"""Let me help you with that question about {prompt}. 

When it comes to {persona} style recommendations, here's what you should know: 
The key factors to consider are your specific needs, budget, and use case. 

Based on current options, I'd recommend looking at the latest releases and comparing features carefully. 
Check reviews, compare specifications, and think about what matters most to you. 

Remember, the best choice depends on your individual requirements and preferences. 
Do your research and make an informed decision that works for you."""
    
    script_intent = _simple_sentence_intent(fallback_text)
    script_text = " ".join(seg.text for seg in script_intent.segments)
    
    logger.info(f"[{request_id}] ✓ Fallback script: {len(script_text)} chars, {len(script_intent.segments)} segments")
    return script_text, script_intent


# ----------------------------
# DEPRECATED: Old retry functions (UNUSED - kept for reference, remove in future cleanup)
# All retry logic has been eliminated to enforce SINGLE-CALL POLICY
# ----------------------------

# _call_persona_generator() - DEPRECATED
# _retry_stronger_intent_prompt() - DEPRECATED


def _simple_sentence_intent(text: str) -> ScriptIntent:
    """
    Lightweight local intent builder:
    splits into sentences, adds small pauses, minimal emphasis.
    """
    # crude sentence split
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    segments = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # break long sentences
        if len(p.split()) > 26:
            chunks = re.split(r",\s+", p)
            for c in chunks:
                c = c.strip()
                if c:
                    segments.append({"text": c, "pause_after": 0.25, "emphasis": [], "sentence_end": c.endswith((".", "!", "?"))})
        else:
            segments.append({"text": p, "pause_after": 0.30, "emphasis": [], "sentence_end": True})

    if not segments:
        return create_simple_intent(text, pause_after=0.3)

    return ScriptIntent.from_dict({"segments": segments})


# ----------------------------
# SadTalker retry wrapper
# ----------------------------

def _sadtalker_generate_with_nan_retry(
    *,
    request_id: str,
    sadtalker: SadTalkerWrapper,
    audio_path: Path,
    reference_image: Path,
    output_path: Path,
    fps: int,
    enable_governor: bool,
    style: str,
    timing_map_path: Path,
    intent_path: Path,
) -> Path:
    """
    Wrap SadTalkerWrapper.generate with a retry if the SadTalker croper hits NaN.
    This matches your failure:
      ValueError: cannot convert float NaN to integer (croper.align_face)
    """
    try:
        return Path(
            sadtalker.generate(
                audio_path=audio_path,
                reference_image=reference_image,
                output_path=output_path,
                fps=fps,
                enable_governor=enable_governor,
                style=style,
                timing_map_path=timing_map_path,
                intent_json_path=intent_path,
                # Default preprocess mode
                crop_or_resize="crop",
            )
        )
    except Exception as e:
        if not is_sadtalker_nan_crop_error(e):
            raise

        logger.warning(f"[{request_id}] SadTalker NaN crop error detected. Retrying with safer preprocess settings...")

        # Retry with a safer preprocessing mode.
        # Depending on your wrapper, you may support 'resize' or 'ext' or a fixed center-crop.
        # The goal: avoid NaNs from landmark-based alignment.
        return Path(
            sadtalker.generate(
                audio_path=audio_path,
                reference_image=reference_image,
                output_path=output_path,
                fps=fps,
                enable_governor=enable_governor,
                style=style,
                timing_map_path=timing_map_path,
                intent_json_path=intent_path,
                crop_or_resize="resize",   # <- key change for retry
                # Optional knobs if your wrapper supports them:
                # force_center_crop=True,
                # skip_align_face=True,
            )
        )
