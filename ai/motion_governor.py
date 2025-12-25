"""
Motion Governor
Unified control layer for SadTalker motion/expression coefficients.
Improves pose + expression quality via clamping, smoothing, intent gating, and style scaling.

ARCHITECTURAL ROLE:
- SadTalker = motion proposal generator
- Motion Governor = director/constraint system
- Accepts BOTH audio intent (pause detection) AND script intent (emphasis, sentence ends)
"""
import numpy as np
import scipy.io as scio
from pathlib import Path
from typing import Optional, Dict, Tuple
import json
import logging
from dataclasses import dataclass, asdict
import cv2

logger = logging.getLogger("lumen")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("[MotionGovernor] librosa not available - audio analysis features disabled")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("[MotionGovernor] mediapipe not available - reference style extraction limited")

# Import intent contract
try:
    from ai.script_intent import IntentTimingMap
    INTENT_AVAILABLE = True
except ImportError:
    INTENT_AVAILABLE = False
    IntentTimingMap = None
    logger.warning("[MotionGovernor] Intent system not available")


@dataclass
class StyleProfile:
    """Style profile for motion control"""
    name: str = "calm_tech"
    
    # Pose constraints (radians or normalized units matching SadTalker)
    pose_max: Tuple[float, float, float] = (0.3, 0.2, 0.2)  # yaw, pitch, roll
    pose_scale: Tuple[float, float, float] = (0.6, 0.5, 0.4)  # reduce amplitude
    
    # Expression constraints
    expr_max: float = 3.0
    expr_strength: float = 0.7  # overall expression intensity
    
    # Temporal smoothing (0..1, higher = more smoothing)
    smoothing: float = 0.75
    
    # Pause behavior
    stillness_on_pause: float = 0.85  # freeze pose during silence
    stillness_expr_on_pause: float = 0.90  # freeze expressions during silence
    
    # Optional nod behavior at sentence boundaries
    nod_rate: float = 0.0  # per second (0 = disabled)
    nod_amplitude: float = 0.05  # pitch delta
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StyleProfile':
        return cls(**data)
    
    @classmethod
    def load(cls, path: Path) -> 'StyleProfile':
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))
    
    def save(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Preset styles
STYLE_PRESETS = {
    "calm_tech": StyleProfile(
        name="calm_tech",
        pose_max=(0.25, 0.15, 0.15),
        pose_scale=(0.5, 0.4, 0.3),
        expr_strength=0.6,
        smoothing=0.80,
        stillness_on_pause=0.90,
        stillness_expr_on_pause=0.92
    ),
    "energetic": StyleProfile(
        name="energetic",
        pose_max=(0.5, 0.4, 0.3),
        pose_scale=(0.9, 0.8, 0.7),
        expr_strength=1.1,
        smoothing=0.60,
        stillness_on_pause=0.60,
        stillness_expr_on_pause=0.70,
        nod_rate=0.3,
        nod_amplitude=0.08
    ),
    "lecturer": StyleProfile(
        name="lecturer",
        pose_max=(0.35, 0.25, 0.2),
        pose_scale=(0.7, 0.6, 0.5),
        expr_strength=0.8,
        smoothing=0.70,
        stillness_on_pause=0.75,
        stillness_expr_on_pause=0.85,
        nod_rate=0.2,
        nod_amplitude=0.06
    )
}


class MotionGovernor:
    """
    Unified motion control layer for SadTalker coefficients.
    
    Applies deterministic constraints to improve pose and expression quality:
    - Clamping (safety net)
    - Intent gating (audio/script aware)
    - Style scaling (preset or reference-based)
    - Temporal smoothing (removes jitter)
    - Pause stillness (reduces fidgeting)
    """
    
    def __init__(
        self,
        style_profile: Optional[StyleProfile] = None,
        fps: int = 25,
        enable_governor: bool = True
    ):
        """
        Initialize Motion Governor.
        
        Args:
            style_profile: Style configuration (uses calm_tech if None)
            fps: Frames per second for time-to-frame mapping
            enable_governor: If False, acts as pass-through
        """
        self.style = style_profile or STYLE_PRESETS["calm_tech"]
        self.fps = fps
        self.enable_governor = enable_governor
        
        # State for temporal smoothing
        self.prev_pose = None
        self.prev_expr = None
        
        logger.info(f"[MotionGovernor] Initialized with style '{self.style.name}'")
        logger.info(f"[MotionGovernor] Governor enabled: {self.enable_governor}")
    
    def reset(self):
        """Reset temporal state (call between videos)"""
        self.prev_pose = None
        self.prev_expr = None
    
    def process_coeff_file(
        self,
        coeff_path: Path,
        audio_path: Optional[Path] = None,
        intent_timing_map: Optional['IntentTimingMap'] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Process a SadTalker coefficient file (.mat format).
        
        THIS IS THE CENTRAL ARCHITECTURAL METHOD.
        Combines audio-based AND script-based intent for unified control.
        
        Args:
            coeff_path: Path to input coefficient file
            audio_path: Optional audio file for pause detection
            intent_timing_map: Optional script intent from XTTS (NEW)
            output_path: Output path (defaults to coeff_path with _governed suffix)
        
        Returns:
            Path to output coefficient file
        
        Intent Fusion:
            audio_intent[t] = 0.0 (silence) or 1.0 (speech) from librosa RMS
            script_intent[t] = 0.0 (pause) or 1.0-1.3 (normal/emphasis) from IntentTimingMap
            combined_intent[t] = audio_intent[t] * script_intent[t]
            
            This ensures BOTH audio AND script agree before allowing motion.
        """
        if not self.enable_governor:
            logger.info("[MotionGovernor] Governor disabled, returning original")
            return coeff_path
        
        # Log intent sources
        logger.info(f"[MotionGovernor] === INTENT SOURCES ===")
        logger.info(f"[MotionGovernor] Audio intent: {'YES' if audio_path else 'NO'}")
        logger.info(f"[MotionGovernor] Script intent: {'YES' if intent_timing_map else 'NO'}")
        logger.info(f"[MotionGovernor] Style: {self.style.name}")
        
        try:
            # Load coefficients
            logger.info(f"[MotionGovernor] Loading coefficients from {coeff_path.name}")
            coeff_dict = scio.loadmat(str(coeff_path))
            
            # Extract 3DMM coefficients (shape: [T, 73] or [T, 257] depending on model)
            # Format: [id(80), exp(64), tex(80), angles(3), gamma(27), trans(3)]
            # We care about: angles (pose) and exp (expressions)
            coeff_3dmm = coeff_dict['coeff_3dmm']  # [T, dims]
            
            T, dims = coeff_3dmm.shape
            logger.info(f"[MotionGovernor] Processing {T} frames, {dims} coefficients per frame")
            
            # DETECT COMPACT VS FULL 3DMM MODELS
            # Compact models (< 200 dims): Latent audio→face coefficients - DO NOT MODIFY DIRECTLY
            # Full models (>= 200 dims): True 3DMM parameters - safe to clamp/scale
            IS_COMPACT_MODEL = dims < 200
            
            if IS_COMPACT_MODEL:
                logger.warning(f"[MotionGovernor] Compact model detected ({dims} dims) - using renderer-safe intent gating")
                logger.warning(f"[MotionGovernor] Expression coefficients are LATENT - will not be clamped/scaled")
            else:
                logger.info(f"[MotionGovernor] Full 3DMM model ({dims} dims) - using standard motion processing")
            
            # DYNAMIC COEFFICIENT LAYOUT DETECTION (capability-driven)
            # SadTalker outputs vary by model/version:
            #   - 257-dim: id(80) + exp(64) + tex(80) + angles(3) + gamma(27) + trans(3)
            #   - 224-dim: id(80) + exp(64) + tex(80) (no pose angles)
            #   - 73-dim:  exp(64) + angles(3) + gamma(3) + trans(3) [COMPACT/LATENT]
            #   - 70-dim:  exp(64) + angles(3) + trans(3) [COMPACT/LATENT]
            
            # Detect capabilities based on coefficient dimensions
            HAS_EXP = False
            HAS_POSE = False
            exp_start = None
            exp_end = None
            pose_start = None
            pose_end = None
            
            exp_dim = 64
            
            # Common layouts
            if dims >= 224:
                # Full format: id(80) + exp(64) + tex(80) + [angles(3) + ...]
                HAS_EXP = True
                exp_start = 80
                exp_end = 144
                if dims >= 227:
                    HAS_POSE = True
                    pose_start = 224
                    pose_end = 227
            elif dims >= 67 and dims < 224:
                # Compact format: exp(64) + angles(3) + [...]
                HAS_EXP = True
                exp_start = 0
                exp_end = 64
                if dims >= 67:
                    HAS_POSE = True
                    pose_start = 64
                    pose_end = 67
            else:
                logger.error(f"[MotionGovernor] Unsupported coefficient layout: {dims} dims")
                raise ValueError(f"Cannot parse coefficient format with {dims} dimensions")
            
            logger.info(f"[MotionGovernor] Capabilities: EXP={HAS_EXP}, POSE={HAS_POSE}, COMPACT={IS_COMPACT_MODEL}")
            
            # Extract expression coefficients
            if HAS_EXP:
                raw_exp = coeff_3dmm[:, exp_start:exp_end]  # [T, 64]
                logger.info(f"[MotionGovernor] Extracted expression from columns [{exp_start}:{exp_end}]")
            else:
                # Fallback: create neutral expressions
                raw_exp = np.zeros((T, exp_dim), dtype=np.float32)
                logger.warning(f"[MotionGovernor] Expression coefficients not available - using neutral")
            
            # Extract pose angles
            if HAS_POSE:
                raw_pose = coeff_3dmm[:, pose_start:pose_end]  # [T, 3]
                logger.info(f"[MotionGovernor] Extracted pose angles from columns [{pose_start}:{pose_end}]")
            else:
                # Fallback: create zero pose (no head motion)
                raw_pose = np.zeros((T, 3), dtype=np.float32)
                logger.warning(f"[MotionGovernor] Pose angles not available - using zero pose")
            
            # Validate extraction
            if raw_pose.shape != (T, 3):
                logger.error(f"[MotionGovernor] Invalid pose shape: {raw_pose.shape}, expected ({T}, 3)")
                raw_pose = np.zeros((T, 3), dtype=np.float32)
            if raw_exp.shape != (T, exp_dim):
                logger.error(f"[MotionGovernor] Invalid expression shape: {raw_exp.shape}, expected ({T}, {exp_dim})")
                raw_exp = np.zeros((T, exp_dim), dtype=np.float32)
            
            # CRITICAL: T is SadTalker motion frame count (source of truth)
            
            # 1. Audio-based intent (pause detection from RMS energy)
            audio_intent_mask = None
            if audio_path and LIBROSA_AVAILABLE:
                audio_intent_mask = self._build_audio_intent_mask(audio_path, T)
                # Align to SadTalker frame count
                audio_intent_mask = self._align_intent_mask(audio_intent_mask, T, "audio")
            
            # 2. Script-based intent (pause/emphasis from Gemini → XTTS)
            script_intent_mask = None
            sentence_end_frames = []
            if intent_timing_map and INTENT_AVAILABLE:
                script_intent_mask = intent_timing_map.build_intent_mask()
                sentence_end_frames = intent_timing_map.get_sentence_end_frames()
                
                # Align script intent to SadTalker frame count
                script_intent_mask = self._align_intent_mask(script_intent_mask, T, "script")
                
                # Align sentence end frames: drop any beyond motion length
                if sentence_end_frames:
                    original_count = len(sentence_end_frames)
                    sentence_end_frames = [f for f in sentence_end_frames if f < T]
                    if len(sentence_end_frames) < original_count:
                        logger.info(f"[MotionGovernor] Sentence ends: {original_count} → {len(sentence_end_frames)} (dropped out-of-range)")
            
            # 3. Combine intents (multiplicative fusion)
            combined_intent_mask = self._combine_intent_masks(
                audio_intent_mask, script_intent_mask, T
            )
            
            # Final safety: align combined mask to T
            combined_intent_mask = self._align_intent_mask(combined_intent_mask, T, "combined")
            
            # Log intent statistics
            pause_frames = (combined_intent_mask < 0.1).sum() if combined_intent_mask is not None else 0
            emphasis_frames = (combined_intent_mask > 1.05).sum() if combined_intent_mask is not None else 0
            logger.info(f"[MotionGovernor] Combined intent: {pause_frames} pause, {emphasis_frames} emphasis frames")
            
            # RENDERER-SAFE COEFFICIENT PROCESSING
            coeff_3dmm_out = coeff_3dmm.copy()
            
            if IS_COMPACT_MODEL:
                # COMPACT MODEL: Latent coefficients - only apply intent as scalar gating
                # DO NOT clamp/scale individual coefficients (breaks renderer)
                logger.info(f"[MotionGovernor] Applying intent gating (scalar modulation only)")
                
                if combined_intent_mask is not None:
                    # Apply intent mask as subtle frame-wise scalar multiplier
                    # Use conservative blending to avoid excessive motion
                    # Range: 0.7 (pause) to 1.0 (emphasis) instead of 0.05 to 1.2
                    intent_normalized = combined_intent_mask.reshape(T, 1)  # [T, 1]
                    
                    # Clamp and rescale intent to subtle range
                    # Original: 0.0-1.2, Target: 0.7-1.0 (30% motion range)
                    intent_clamped = np.clip(intent_normalized, 0.0, 1.2)
                    intent_subtle = 0.7 + (intent_clamped * 0.25)  # Maps [0, 1.2] -> [0.7, 1.0]
                    
                    coeff_3dmm_out = coeff_3dmm * intent_subtle
                    
                    intent_min = intent_subtle.min()
                    intent_max = intent_subtle.max()
                    logger.info(f"[MotionGovernor] ✓ Applied subtle intent gating: range [{intent_min:.3f}, {intent_max:.3f}]")
                else:
                    logger.info(f"[MotionGovernor] No intent mask - returning original coefficients")
                
            else:
                # FULL 3DMM MODEL: True parameters - safe to process through motion governor
                logger.info(f"[MotionGovernor] Processing through full motion governor pipeline")
                
                # Extract expression coefficients
                if HAS_EXP:
                    raw_exp = coeff_3dmm[:, exp_start:exp_end]  # [T, 64]
                    logger.info(f"[MotionGovernor] Extracted expression from columns [{exp_start}:{exp_end}]")
                else:
                    raw_exp = np.zeros((T, exp_dim), dtype=np.float32)
                    logger.warning(f"[MotionGovernor] Expression coefficients not available - using neutral")
                
                # Extract pose angles
                if HAS_POSE:
                    raw_pose = coeff_3dmm[:, pose_start:pose_end]  # [T, 3]
                    logger.info(f"[MotionGovernor] Extracted pose angles from columns [{pose_start}:{pose_end}]")
                else:
                    raw_pose = np.zeros((T, 3), dtype=np.float32)
                    logger.warning(f"[MotionGovernor] Pose angles not available - using zero pose")
                
                # Validate extraction
                if raw_pose.shape != (T, 3):
                    logger.error(f"[MotionGovernor] Invalid pose shape: {raw_pose.shape}, expected ({T}, 3)")
                    raw_pose = np.zeros((T, 3), dtype=np.float32)
                if raw_exp.shape != (T, exp_dim):
                    logger.error(f"[MotionGovernor] Invalid expression shape: {raw_exp.shape}, expected ({T}, {exp_dim})")
                    raw_exp = np.zeros((T, exp_dim), dtype=np.float32)
                
                # Process motion with combined intent
                pose_out, expr_out = self._process_motion(
                    raw_pose, raw_exp, combined_intent_mask, sentence_end_frames
                )
                
                # Write back processed coefficients
                if HAS_EXP and exp_start is not None and exp_end is not None:
                    coeff_3dmm_out[:, exp_start:exp_end] = expr_out
                    logger.info(f"[MotionGovernor] ✓ Updated expression coefficients [{exp_start}:{exp_end}]")
                
                if HAS_POSE and pose_start is not None and pose_end is not None:
                    coeff_3dmm_out[:, pose_start:pose_end] = pose_out
                    logger.info(f"[MotionGovernor] ✓ Updated pose coefficients [{pose_start}:{pose_end}]")
            
            # Save output
            if output_path is None:
                output_path = coeff_path.parent / f"{coeff_path.stem}_governed.mat"
            
            output_dict = coeff_dict.copy()
            output_dict['coeff_3dmm'] = coeff_3dmm_out
            
            scio.savemat(str(output_path), output_dict)
            logger.info(f"[MotionGovernor] ✓ Saved governed coefficients to {output_path.name}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"[MotionGovernor] Processing failed: {e}", exc_info=True)
            logger.warning("[MotionGovernor] Fallback: returning original coefficients")
            return coeff_path
    
    def _align_intent_mask(self, intent_mask: np.ndarray, target_length: int, mask_name: str = "intent") -> np.ndarray:
        """
        Align intent mask to match SadTalker motion frame count.
        
        SadTalker is the source of truth for frame count.
        Intent masks must adapt to motion, not vice versa.
        
        Args:
            intent_mask: Original intent mask [T_intent]
            target_length: SadTalker motion frame count [T_motion]
            mask_name: Name for logging
            
        Returns:
            Aligned intent mask [T_motion]
        """
        if intent_mask is None:
            return None
            
        original_len = len(intent_mask)
        
        if original_len == target_length:
            return intent_mask
        
        if original_len > target_length:
            # Truncate: drop excess frames
            aligned = intent_mask[:target_length]
            logger.info(f"[MotionGovernor] Aligned {mask_name} mask: {original_len} → {target_length} (truncated)")
        else:
            # Pad: repeat last value (natural state persistence)
            last_value = intent_mask[-1]
            padding = np.full(target_length - original_len, last_value)
            aligned = np.concatenate([intent_mask, padding])
            logger.info(f"[MotionGovernor] Aligned {mask_name} mask: {original_len} → {target_length} (padded with {last_value:.2f})")
        
        return aligned
    
    def _build_audio_intent_mask(self, audio_path: Path, num_frames: int) -> np.ndarray:
        """
        Build audio-based intent mask from RMS energy analysis.
        
        Args:
            audio_path: Path to audio file
            num_frames: Number of video frames
        
        Returns:
            Float array [T] where:
                ~0.0 = silence/pause
                ~1.0 = speech
        """
        try:
            logger.info(f"[MotionGovernor:Audio] Analyzing audio energy...")
            
            # Load audio
            y, sr = librosa.load(str(audio_path), sr=None)
            
            # Compute short-time RMS energy
            hop_length = int(sr / self.fps)
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            
            # Determine silence threshold
            threshold = np.percentile(rms, 20) * 1.5
            
            # Convert to intent mask (1.0 for speech, 0.05 for pause)
            intent_mask = np.where(rms >= threshold, 1.0, 0.05).astype(np.float32)
            
            # Resize to match video frames
            if len(intent_mask) != num_frames:
                x_old = np.linspace(0, 1, len(intent_mask))
                x_new = np.linspace(0, 1, num_frames)
                intent_mask = np.interp(x_new, x_old, intent_mask)
            
            pause_count = (intent_mask < 0.1).sum()
            logger.info(f"[MotionGovernor:Audio] Detected {pause_count}/{num_frames} pause frames")
            
            return intent_mask
            
        except Exception as e:
            logger.warning(f"[MotionGovernor:Audio] Analysis failed: {e}")
            return np.ones(num_frames, dtype=np.float32)
    
    def _combine_intent_masks(
        self,
        audio_mask: Optional[np.ndarray],
        script_mask: Optional[np.ndarray],
        num_frames: int
    ) -> Optional[np.ndarray]:
        """
        Combine audio and script intent masks (ARCHITECTURAL CORE).
        
        Fusion strategy: multiplicative (AND logic)
        - If either says pause → pause wins
        - If both say speech → script emphasis can boost
        
        Args:
            audio_mask: Audio-based intent [T] or None
            script_mask: Script-based intent [T] or None
            num_frames: Number of frames
        
        Returns:
            Combined intent mask [T] or None
        """
        if audio_mask is None and script_mask is None:
            return None
        
        if audio_mask is None:
            logger.info("[MotionGovernor:Intent] Using script intent only")
            return script_mask
        
        if script_mask is None:
            logger.info("[MotionGovernor:Intent] Using audio intent only")
            return audio_mask
        
        # Both available: multiplicative fusion
        combined = audio_mask * script_mask
        
        logger.info("[MotionGovernor:Intent] Fused audio + script intent")
        logger.info(f"[MotionGovernor:Intent] Audio pauses: {(audio_mask < 0.1).sum()}")
        logger.info(f"[MotionGovernor:Intent] Script pauses: {(script_mask < 0.1).sum()}")
        logger.info(f"[MotionGovernor:Intent] Combined pauses: {(combined < 0.1).sum()}")
        
        return combined
    
    def _detect_pauses(self, audio_path: Path, num_frames: int) -> np.ndarray:
        """
        DEPRECATED: Use _build_audio_intent_mask instead.
        Kept for backward compatibility.
        """
        mask = self._build_audio_intent_mask(audio_path, num_frames)
        return mask < 0.1  # Convert to boolean
    
    def _process_motion(
        self,
        raw_pose: np.ndarray,
        raw_expr: np.ndarray,
        intent_mask: Optional[np.ndarray] = None,
        sentence_end_frames: Optional[list] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Core motion processing logic with intent fusion.
        
        Args:
            raw_pose: [T, 3] yaw, pitch, roll
            raw_expr: [T, E] expression coefficients
            intent_mask: [T] float intent values (0.0=pause, 1.0=normal, >1.0=emphasis)
            sentence_end_frames: List of frame indices for sentence ends (for nod impulse)
        
        Returns:
            (pose_out, expr_out) processed coefficients
        
        Processing Pipeline:
            1. CLAMP: Hard safety limits
            2. INTENT GATE: Multiply by intent mask (pause stillness, emphasis boost)
            3. STYLE SCALE: Apply style-specific scaling
            4. SMOOTH: IIR temporal filter
            5. SENTENCE NOD: Subtle pitch impulse at sentence boundaries
        """
        T = raw_pose.shape[0]
        
        if intent_mask is None:
            intent_mask = np.ones(T, dtype=np.float32)
        
        if sentence_end_frames is None:
            sentence_end_frames = []
        
        # Initialize output
        pose_out = np.zeros_like(raw_pose)
        expr_out = np.zeros_like(raw_expr)
        
        # Reset state for new sequence
        self.reset()
        
        logger.info(f"[MotionGovernor] Processing {T} frames with intent fusion...")
        
        for t in range(T):
            # 1. CLAMP (safety net)
            pose_clamped = np.clip(
                raw_pose[t],
                -np.array(self.style.pose_max),
                np.array(self.style.pose_max)
            )
            
            expr_clamped = np.clip(
                raw_expr[t],
                -self.style.expr_max,
                self.style.expr_max
            )
            
            # 2. INTENT GATE (UNIFIED: audio + script intent)
            intent = intent_mask[t]
            
            # Intent interpretation:
            # 0.0-0.1 = pause (strong stillness)
            # 0.8-1.0 = normal speech
            # 1.1-1.3 = emphasis (boost expressiveness)
            
            is_pause = intent < 0.1
            is_emphasis = intent > 1.05
            
            # 3. STYLE SCALE (modulated by intent)
            pose_scaled = pose_clamped * np.array(self.style.pose_scale) * intent
            expr_scaled = expr_clamped * self.style.expr_strength * intent
            
            # 4. TEMPORAL SMOOTHING (IIR filter)
            alpha = 1.0 - self.style.smoothing  # higher smoothing = lower alpha
            
            if self.prev_pose is None:
                # First frame
                pose_smoothed = pose_scaled
                expr_smoothed = expr_scaled
            else:
                pose_smoothed = alpha * pose_scaled + (1 - alpha) * self.prev_pose
                expr_smoothed = alpha * expr_scaled + (1 - alpha) * self.prev_expr
            
            # 5. PAUSE STILLNESS OVERRIDE (for very low intent)
            if is_pause:
                pose_smoothed *= (1 - self.style.stillness_on_pause)
                expr_smoothed *= (1 - self.style.stillness_expr_on_pause)
            
            # 6. SENTENCE END NOD (subtle pitch impulse)
            if t in sentence_end_frames and self.style.nod_rate > 0:
                nod_impulse = self.style.nod_amplitude
                pose_smoothed[1] += nod_impulse  # pitch (positive = nod down)
            
            # Store output
            pose_out[t] = pose_smoothed
            expr_out[t] = expr_smoothed
            
            # Update state
            self.prev_pose = pose_smoothed
            self.prev_expr = expr_smoothed
        
        # Log statistics
        pose_std = np.std(pose_out, axis=0)
        expr_std = np.std(expr_out)
        logger.info(f"[MotionGovernor] ✓ Pose std: yaw={pose_std[0]:.3f}, pitch={pose_std[1]:.3f}, roll={pose_std[2]:.3f}")
        logger.info(f"[MotionGovernor] ✓ Expression std: {expr_std:.3f}")
        
        return pose_out, expr_out


def build_style_from_reference(video_path: Path, name: str = "reference") -> StyleProfile:
    """
    Build a style profile from a reference video by analyzing motion statistics.
    
    Extracts head pose angles across frames and computes statistics to derive
    appropriate scaling factors and constraints.
    
    Args:
        video_path: Path to reference video
        name: Name for the generated style profile
    
    Returns:
        StyleProfile derived from reference video motion
    
    Raises:
        FileNotFoundError: If video doesn't exist
        RuntimeError: If pose extraction fails
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    logger.info(f"[MotionGovernor] Building style profile from reference: {video_path.name}")
    
    # Method 1: Try MediaPipe (most accurate)
    if MEDIAPIPE_AVAILABLE:
        try:
            return _build_style_mediapipe(video_path, name)
        except Exception as e:
            logger.warning(f"[MotionGovernor] MediaPipe extraction failed: {e}, trying fallback")
    
    # Method 2: Fallback to OpenCV-based estimation
    try:
        return _build_style_opencv(video_path, name)
    except Exception as e:
        logger.error(f"[MotionGovernor] All pose extraction methods failed: {e}")
        raise RuntimeError(
            f"Failed to extract pose from reference video. "
            f"Ensure video contains clear face visibility. Error: {e}"
        )


def _build_style_mediapipe(video_path: Path, name: str) -> StyleProfile:
    """Extract pose using MediaPipe Face Mesh (most accurate)"""
    logger.info("[MotionGovernor] Using MediaPipe for pose extraction...")
    
    mp_face_mesh = mp.solutions.face_mesh
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"[MotionGovernor] Video: {frame_count} frames at {fps} fps")
    
    # Collect pose angles
    yaw_angles = []
    pitch_angles = []
    roll_angles = []
    
    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:
        
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames for speed (sample every 3rd frame)
            if frame_idx % 3 != 0:
                frame_idx += 1
                continue
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                
                # Estimate pose from landmarks
                # Use key points: nose tip, chin, left eye, right eye, left mouth, right mouth
                h, w = frame.shape[:2]
                
                # Extract 3D coordinates (normalized)
                nose = landmarks.landmark[1]  # Nose tip
                chin = landmarks.landmark[152]  # Chin
                left_eye = landmarks.landmark[33]  # Left eye
                right_eye = landmarks.landmark[263]  # Right eye
                
                # Convert to pixel coordinates
                nose_2d = np.array([nose.x * w, nose.y * h])
                chin_2d = np.array([chin.x * w, chin.y * h])
                left_eye_2d = np.array([left_eye.x * w, left_eye.y * h])
                right_eye_2d = np.array([right_eye.x * w, right_eye.y * h])
                
                # Estimate angles
                # Yaw: horizontal head rotation (left/right)
                eye_center = (left_eye_2d + right_eye_2d) / 2
                yaw = np.arctan2(nose_2d[0] - eye_center[0], w * 0.3) * 2  # Approximate
                
                # Pitch: vertical head rotation (up/down)
                pitch = np.arctan2(nose_2d[1] - eye_center[1], h * 0.3) * 2
                
                # Roll: head tilt (shoulder to shoulder)
                roll = np.arctan2(right_eye_2d[1] - left_eye_2d[1], 
                                 right_eye_2d[0] - left_eye_2d[0])
                
                yaw_angles.append(yaw)
                pitch_angles.append(pitch)
                roll_angles.append(roll)
            
            frame_idx += 1
            
            # Progress logging
            if frame_idx % 100 == 0:
                logger.info(f"[MotionGovernor] Processed {frame_idx}/{frame_count} frames...")
    
    cap.release()
    
    if len(yaw_angles) < 10:
        raise RuntimeError("Insufficient face detections in video")
    
    logger.info(f"[MotionGovernor] Extracted pose from {len(yaw_angles)} frames")
    
    # Compute statistics
    return _compute_style_from_angles(
        np.array(yaw_angles),
        np.array(pitch_angles),
        np.array(roll_angles),
        name,
        fps
    )


def _build_style_opencv(video_path: Path, name: str) -> StyleProfile:
    """Fallback pose extraction using OpenCV (less accurate but more compatible)"""
    logger.info("[MotionGovernor] Using OpenCV fallback for pose extraction...")
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"[MotionGovernor] Video: {frame_count} frames at {fps} fps")
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    # Collect motion statistics (simplified)
    face_positions = []
    face_sizes = []
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames for speed
        if frame_idx % 5 != 0:
            frame_idx += 1
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        if len(faces) > 0:
            # Use largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            
            # Normalize positions
            frame_h, frame_w = frame.shape[:2]
            face_center_x = (x + w/2) / frame_w - 0.5  # -0.5 to 0.5
            face_center_y = (y + h/2) / frame_h - 0.5
            face_size = (w * h) / (frame_w * frame_h)
            
            face_positions.append([face_center_x, face_center_y])
            face_sizes.append(face_size)
        
        frame_idx += 1
        
        if frame_idx % 100 == 0:
            logger.info(f"[MotionGovernor] Processed {frame_idx}/{frame_count} frames...")
    
    cap.release()
    
    if len(face_positions) < 10:
        raise RuntimeError("Insufficient face detections in video")
    
    logger.info(f"[MotionGovernor] Analyzed {len(face_positions)} frames")
    
    # Estimate pose from face movement (approximate)
    positions = np.array(face_positions)
    sizes = np.array(face_sizes)
    
    # Approximate angles from position variance
    yaw_approx = positions[:, 0] * 0.6  # Horizontal movement → yaw
    pitch_approx = positions[:, 1] * 0.5  # Vertical movement → pitch
    roll_approx = np.zeros_like(yaw_approx)  # Can't estimate roll reliably
    
    return _compute_style_from_angles(
        yaw_approx, pitch_approx, roll_approx, name, fps
    )


def _compute_style_from_angles(
    yaw: np.ndarray,
    pitch: np.ndarray,
    roll: np.ndarray,
    name: str,
    fps: float
) -> StyleProfile:
    """Compute StyleProfile from extracted pose angles"""
    
    # Compute statistics
    yaw_std = np.std(yaw)
    pitch_std = np.std(pitch)
    roll_std = np.std(roll)
    
    yaw_max = np.abs(yaw).max()
    pitch_max = np.abs(pitch).max()
    roll_max = np.abs(roll).max()
    
    logger.info(f"[MotionGovernor] Pose statistics:")
    logger.info(f"  Yaw:   std={yaw_std:.3f}, max={yaw_max:.3f}")
    logger.info(f"  Pitch: std={pitch_std:.3f}, max={pitch_max:.3f}")
    logger.info(f"  Roll:  std={roll_std:.3f}, max={roll_max:.3f}")
    
    # Derive style parameters
    # pose_max: Set to 95th percentile to clip extreme outliers
    pose_max = (
        np.percentile(np.abs(yaw), 95),
        np.percentile(np.abs(pitch), 95),
        np.percentile(np.abs(roll), 95) if roll_std > 0.01 else 0.2
    )
    
    # pose_scale: Scale based on observed variance
    # Higher variance → allow more motion (up to 1.0)
    # Lower variance → reduce motion
    yaw_scale = min(1.0, yaw_std / 0.3 * 0.8)
    pitch_scale = min(1.0, pitch_std / 0.2 * 0.7)
    roll_scale = min(1.0, roll_std / 0.15 * 0.6) if roll_std > 0.01 else 0.4
    
    pose_scale = (
        max(0.3, yaw_scale),
        max(0.3, pitch_scale),
        max(0.3, roll_scale)
    )
    
    # Determine motion style based on overall activity
    total_motion = yaw_std + pitch_std + roll_std
    
    if total_motion < 0.3:
        # Very calm/static
        smoothing = 0.85
        stillness = 0.90
        expr_strength = 0.6
    elif total_motion < 0.6:
        # Moderate motion
        smoothing = 0.70
        stillness = 0.75
        expr_strength = 0.8
    else:
        # Dynamic/energetic
        smoothing = 0.60
        stillness = 0.60
        expr_strength = 1.0
    
    # Detect nod rate (simplified: count direction changes in pitch)
    pitch_diff = np.diff(pitch)
    pitch_sign_changes = np.sum(np.abs(np.diff(np.sign(pitch_diff))) > 0)
    nod_rate = pitch_sign_changes / (len(pitch) / fps) if fps > 0 else 0
    nod_amplitude = pitch_std * 0.5 if nod_rate > 0.1 else 0.05
    
    logger.info(f"[MotionGovernor] Derived style parameters:")
    logger.info(f"  pose_max: {pose_max}")
    logger.info(f"  pose_scale: {pose_scale}")
    logger.info(f"  smoothing: {smoothing}")
    logger.info(f"  nod_rate: {nod_rate:.2f}/s")
    
    return StyleProfile(
        name=name,
        pose_max=pose_max,
        pose_scale=pose_scale,
        expr_max=3.0,
        expr_strength=expr_strength,
        smoothing=smoothing,
        stillness_on_pause=stillness,
        stillness_expr_on_pause=stillness + 0.05,
        nod_rate=nod_rate,
        nod_amplitude=nod_amplitude
    )
