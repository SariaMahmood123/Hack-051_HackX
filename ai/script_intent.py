"""
Script Intent Contract
Defines canonical schema for intent propagation through the pipeline.
This is the "currency" that flows from Gemini → XTTS → Motion Governor.
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import logging

logger = logging.getLogger("lumen")


@dataclass
class SegmentIntent:
    """Single segment of script with intent markers"""
    text: str
    pause_after: float = 0.0  # seconds of silence after segment
    emphasis: List[str] = None  # words to emphasize
    sentence_end: bool = False  # triggers subtle nod
    
    def __post_init__(self):
        if self.emphasis is None:
            self.emphasis = []
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SegmentIntent':
        return cls(**data)


@dataclass
class ScriptIntent:
    """Complete script with structured intent data"""
    segments: List[SegmentIntent]
    total_duration: Optional[float] = None  # filled after audio generation
    
    def to_dict(self) -> dict:
        return {
            "segments": [seg.to_dict() for seg in self.segments],
            "total_duration": self.total_duration
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptIntent':
        segments = [SegmentIntent.from_dict(seg) for seg in data["segments"]]
        return cls(segments=segments, total_duration=data.get("total_duration"))
    
    def save(self, path: Path):
        """Save intent to JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path) -> 'ScriptIntent':
        """Load intent from JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_dict(json.load(f))


@dataclass
class TimingSegment:
    """Audio timing information for a segment"""
    segment_idx: int
    start_time: float  # seconds
    end_time: float  # seconds
    pause_after: float  # seconds
    emphasis: List[str]
    sentence_end: bool


class IntentTimingMap:
    """
    Maps audio time → intent information.
    Created by XTTS after audio generation.
    Consumed by Motion Governor.
    """
    
    def __init__(self, segments: List[TimingSegment], total_duration: float, fps: int = 25):
        """
        Args:
            segments: List of timing segments
            total_duration: Total audio duration in seconds
            fps: Frames per second for frame mapping
        """
        self.segments = segments
        self.total_duration = total_duration
        self.fps = fps
        self.num_frames = int(np.ceil(total_duration * fps))
    
    def build_intent_mask(self) -> np.ndarray:
        """
        Build frame-level intent mask for Motion Governor.
        
        Returns:
            intent_mask: [T] float array where:
                0.0 = pause/silence (maximum stillness)
                1.0 = normal speech (baseline motion)
                1.1-1.3 = emphasis (increased expressiveness)
                
        This mask is multiplied with audio-based intent gate in Motion Governor.
        """
        intent_mask = np.ones(self.num_frames, dtype=np.float32)
        
        for seg in self.segments:
            # Convert time to frames
            start_frame = int(seg.start_time * self.fps)
            end_frame = int(seg.end_time * self.fps)
            pause_end_frame = int((seg.end_time + seg.pause_after) * self.fps)
            
            # Clamp to valid range
            start_frame = max(0, min(start_frame, self.num_frames - 1))
            end_frame = max(0, min(end_frame, self.num_frames - 1))
            pause_end_frame = max(0, min(pause_end_frame, self.num_frames - 1))
            
            # Apply emphasis during speech
            if seg.emphasis and len(seg.emphasis) > 0:
                # Emphasis: boost intent for this segment
                # More emphasis words = stronger boost
                emphasis_factor = min(1.3, 1.1 + len(seg.emphasis) * 0.05)
                intent_mask[start_frame:end_frame] = emphasis_factor
            
            # Apply pause after segment
            if seg.pause_after > 0.01:  # More than 10ms
                intent_mask[end_frame:pause_end_frame] = 0.0
            
            # Mark sentence end (for subtle nod)
            # This is handled separately in Motion Governor via nod_impulse
            # Here we just ensure it's marked as normal intent
            if seg.sentence_end:
                # Could add a small boost at end for micro-nod
                pass
        
        logger.info(f"[IntentMask] Built mask: {self.num_frames} frames")
        logger.info(f"[IntentMask] Pause frames: {(intent_mask < 0.1).sum()} ({(intent_mask < 0.1).sum()/self.num_frames*100:.1f}%)")
        logger.info(f"[IntentMask] Emphasis frames: {(intent_mask > 1.05).sum()} ({(intent_mask > 1.05).sum()/self.num_frames*100:.1f}%)")
        
        return intent_mask
    
    def get_sentence_end_frames(self) -> List[int]:
        """
        Get frame indices where sentence ends occur.
        Used by Motion Governor for nod impulses.
        
        Returns:
            List of frame indices
        """
        end_frames = []
        for seg in self.segments:
            if seg.sentence_end:
                frame_idx = int(seg.end_time * self.fps)
                if 0 <= frame_idx < self.num_frames:
                    end_frames.append(frame_idx)
        
        logger.info(f"[IntentMask] Sentence ends: {len(end_frames)} frames")
        return end_frames
    
    def to_dict(self) -> dict:
        """Serialize to dict"""
        return {
            "segments": [
                {
                    "segment_idx": seg.segment_idx,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "pause_after": seg.pause_after,
                    "emphasis": seg.emphasis,
                    "sentence_end": seg.sentence_end
                }
                for seg in self.segments
            ],
            "total_duration": self.total_duration,
            "fps": self.fps
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'IntentTimingMap':
        """Deserialize from dict"""
        segments = [
            TimingSegment(
                segment_idx=seg["segment_idx"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                pause_after=seg["pause_after"],
                emphasis=seg["emphasis"],
                sentence_end=seg["sentence_end"]
            )
            for seg in data["segments"]
        ]
        return cls(
            segments=segments,
            total_duration=data["total_duration"],
            fps=data["fps"]
        )
    
    def save(self, path: Path):
        """Save to JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'IntentTimingMap':
        """Load from JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_dict(json.load(f))


def flatten_segments_to_text(script_intent: ScriptIntent) -> str:
    """
    Convert structured intent back to plain text.
    Used for audio generation.
    
    Args:
        script_intent: Structured script with intents
    
    Returns:
        Plain text string ready for TTS
    """
    segments_text = []
    for seg in script_intent.segments:
        text = seg.text.strip()
        
        # Apply emphasis via text shaping (capitalization for TTS)
        if seg.emphasis:
            for word in seg.emphasis:
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                # Capitalize for emphasis (TTS will stress it)
                text = pattern.sub(word.upper(), text)
        
        segments_text.append(text)
    
    # Join with spaces
    full_text = " ".join(segments_text)
    return full_text


def parse_gemini_intent_output(gemini_response: str) -> Optional[ScriptIntent]:
    """
    Parse Gemini output that contains intent JSON.
    
    Handles various response formats:
    1. Plain JSON: {"segments": [...]}
    2. JSON in markdown: ```json\n{...}\n```
    3. JSON with preamble/trailing text
    4. Incomplete responses (e.g., just "```json")
    
    Args:
        gemini_response: Raw text from Gemini
    
    Returns:
        ScriptIntent object or None if parsing fails
    """
    if not gemini_response or not isinstance(gemini_response, str):
        logger.warning("[ScriptIntent] Empty or invalid response")
        return None
    
    response = gemini_response.strip()
    
    # Quick check for incomplete responses (e.g., "```json" only)
    if len(response) < 20 and "```" in response:
        logger.warning(f"[ScriptIntent] Incomplete response detected: {response!r}")
        return None
    
    # Try direct JSON parse
    try:
        data = json.loads(response)
        # Validate required fields
        if "segments" not in data or not data["segments"]:
            logger.warning("[ScriptIntent] Parsed JSON missing segments or empty segments")
            return None
        return ScriptIntent.from_dict(data)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code block (```json ... ```)
    try:
        import re
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            data = json.loads(json_str)
            if "segments" not in data or not data["segments"]:
                logger.warning("[ScriptIntent] Fenced JSON missing segments or empty segments")
                return None
            return ScriptIntent.from_dict(data)
    except Exception as e:
        logger.debug(f"[ScriptIntent] Markdown fence extraction failed: {e}")
    
    # Try finding JSON object in the text (look for {...})
    try:
        import re
        # Find the first { and last } in the response
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end+1]
            data = json.loads(json_str)
            # Validate required fields
            if "segments" not in data or not data["segments"]:
                logger.warning("[ScriptIntent] Extracted JSON missing segments or empty segments")
                return None
            return ScriptIntent.from_dict(data)
    except Exception as e:
        logger.warning(f"[ScriptIntent] Failed to parse Gemini output: {e}")
        # Show sanitized preview (first 200 chars)
        preview = response[:200].replace('\n', ' ')
        logger.debug(f"[ScriptIntent] Raw response preview: {preview}...")
    
    return None


def create_simple_intent(text: str, pause_after: float = 0.3) -> ScriptIntent:
    """
    Create a simple single-segment intent from plain text.
    Fallback for when Gemini doesn't output structured intent.
    
    Args:
        text: Script text
        pause_after: Pause duration in seconds
    
    Returns:
        ScriptIntent with single segment
    """
    segment = SegmentIntent(
        text=text,
        pause_after=pause_after,
        emphasis=[],
        sentence_end=True
    )
    return ScriptIntent(segments=[segment])
