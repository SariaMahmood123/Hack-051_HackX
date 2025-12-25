# ARCHITECTURE DOCUMENTATION
## YouTuber Chatbot Avatar System

**Last Updated**: December 25, 2025  
**Version**: 2.0 (Intent-Aware Architecture)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architectural Philosophy](#architectural-philosophy)
3. [Pipeline Flow](#pipeline-flow)
4. [Component Architecture](#component-architecture)
5. [Intent Contract](#intent-contract)
6. [Motion Governor Design](#motion-governor-design)
7. [Integration Points](#integration-points)
8. [Testing Strategy](#testing-strategy)
9. [Future Extensions](#future-extensions)

---

## System Overview

This is a **YouTuber chatbot avatar system** that generates talking-head videos from text prompts with natural, intentional motion.

### Core Components

- **Gemini LLM**: Script generation with structured intent output
- **XTTS-v2**: High-quality voice cloning with segmented audio generation
- **SadTalker**: Talking-head video generation (identity + motion + lip-sync)
- **Motion Governor**: Unified motion control layer (director system)

### Key Innovation

**Intent propagation** from script → audio → motion, creating a coherent system where:
- Gemini understands **semantic intent** (pause, emphasis, sentence boundaries)
- XTTS obeys intent via **segmented generation** with explicit silence
- Motion Governor combines **audio + script intent** for unified control

---

## Architectural Philosophy

### Design Principles

1. **Separation of Concerns**
   - SadTalker = motion **proposal** generator (NOT final authority)
   - Motion Governor = motion **director** (constraint system)
   - Clean boundaries between stages

2. **Intent as Currency**
   - Intent flows through the system as structured data
   - Each stage enriches intent (Gemini → timing → fusion)
   - Intent is **first-class**, not a hack

3. **Determinism**
   - No randomness in motion control
   - Reproducible results for same inputs
   - Debuggable behavior

4. **Graceful Degradation**
   - If intent parsing fails → fallback to plain text
   - If governor fails → fallback to raw coefficients
   - System never crashes due to intent processing

5. **Product Quality**
   - Not a demo, not a prototype
   - Clean code, clear abstractions
   - Explainable via logs

---

## Pipeline Flow

### High-Level Flow

```
User Prompt
   ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 1: GEMINI (Script + Intent Generation)       │
├─────────────────────────────────────────────────────┤
│ Input: User prompt                                  │
│ Output: Script text + ScriptIntent                  │
│   - segments: [text, pause_after, emphasis, ...]   │
│   - Structured JSON (not plain text)                │
└─────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 2: XTTS (Segmented Audio + Timing)           │
├─────────────────────────────────────────────────────┤
│ Input: ScriptIntent                                 │
│ Processing:                                         │
│   - Generate audio per segment                      │
│   - Insert explicit silence (numpy zeros)           │
│   - Text shaping for emphasis (CAPS)                │
│ Output: WAV + IntentTimingMap                       │
│   - audio_path: concatenated audio                  │
│   - timing_map: time → intent mapping               │
└─────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 3: SADTALKER (3-Stage Architecture)          │
├─────────────────────────────────────────────────────┤
│ 3a. generate_coeffs()                               │
│     - SadTalker generates raw coefficients          │
│     - Identity + pose + expr + lips                 │
│                                                     │
│ 3b. govern_coeffs()  ← ARCHITECTURAL CORE           │
│     - Motion Governor processes coefficients        │
│     - Combines audio + script intent                │
│     - Never touches lips/mouth                      │
│                                                     │
│ 3c. render_video()                                  │
│     - Render final video from governed coeffs       │
└─────────────────────────────────────────────────────┘
   ↓
Final Video (coherent, intentional motion)
```

### Data Flow Diagram

```
[Gemini]
   ↓ ScriptIntent {segments: [{text, pause, emphasis}]}
[XTTS]
   ↓ IntentTimingMap {time → intent, fps}
[SadTalker:Coeffs]
   ↓ raw_coeff.mat (pose + expr + lips)
[Motion Governor] ← audio_path (for RMS analysis)
   ↓ governed_coeff.mat (refined pose + expr)
[SadTalker:Render]
   ↓ final_video.mp4
```

---

## Component Architecture

### 1. Gemini Client (`ai/gemini_client.py`)

**Role**: Script generation with intent extraction

#### Key Methods

```python
def generate_with_intent(prompt: str) -> Tuple[str, ScriptIntent]:
    """
    Generate script with structured intent.
    
    Prompt engineering:
    - Wraps user prompt with JSON schema instructions
    - Requests structured output: {segments: [...]}
    - Parses JSON or falls back to plain text
    
    Returns:
        (plain_text, script_intent)
    """
```

#### Intent Schema (Embedded in Prompt)

```json
{
  "segments": [
    {
      "text": "sentence or phrase",
      "pause_after": 0.3,
      "emphasis": ["word1", "word2"],
      "sentence_end": true
    }
  ]
}
```

#### Backward Compatibility

- `generate()` method still works (plain text)
- `generate_with_intent()` is opt-in
- Parsing failures → `create_simple_intent()` fallback

---

### 2. XTTS Wrapper (`ai/xtts_wrapper.py`)

**Role**: Segmented audio generation with explicit timing

#### Key Methods

```python
def synthesize_with_intent(
    script_intent: ScriptIntent,
    reference_audio: Path,
    output_path: Path,
    fps: int = 25
) -> Tuple[Path, IntentTimingMap]:
    """
    Intent-aware synthesis.
    
    Process:
    1. Loop through script_intent.segments
    2. Generate audio per segment (to temp file)
    3. Insert explicit silence (np.zeros) for pause_after
    4. Concatenate all segments
    5. Build IntentTimingMap (links time → intent)
    
    Text shaping for emphasis:
    - emphasis words → CAPITALIZED (TTS stresses them)
    
    Returns:
        (audio_path, timing_map)
    """
```

#### IntentTimingMap Structure

```python
class IntentTimingMap:
    segments: List[TimingSegment]  # per-segment timing
    total_duration: float
    fps: int
    
    def build_intent_mask() -> np.ndarray:
        """
        Returns: [T] float array
            0.0 = pause/silence
            1.0 = normal speech
            1.1-1.3 = emphasis
        """
```

---

### 3. SadTalker Wrapper (`ai/sadtalker_wrapper.py`)

**Role**: Motion proposal + rendering (3-stage architecture)

#### Stage Separation (ARCHITECTURAL KEY)

```python
# OLD (monolithic):
def generate(audio, image) -> video:
    # Everything mixed together
    pass

# NEW (clean separation):
def generate_coeffs(audio, image) -> coeff_data:
    """Stage 1: SadTalker motion proposal"""
    
def govern_coeffs(coeff_data, intent_map, style) -> coeff_data:
    """Stage 2: Motion Governor refinement"""
    
def render_video(coeff_data) -> video:
    """Stage 3: Final rendering"""
```

#### Why 3 Stages?

1. **Testability**: Can test coefficient generation independently
2. **Debugging**: Can inspect coefficients before/after governance
3. **Extensibility**: Can add custom processing between stages
4. **Clarity**: Each stage has single responsibility

#### Backward Compatibility

```python
def generate(..., intent_timing_map=None):
    """
    Orchestrates all 3 stages (backward compatible).
    Old code still works without intent.
    """
    coeff_data = self.generate_coeffs(...)
    coeff_data = self.govern_coeffs(..., intent_timing_map)
    return self.render_video(coeff_data)
```

---

### 4. Motion Governor (`ai/motion_governor.py`)

**Role**: Unified motion control layer (THE DIRECTOR)

#### Architectural Role

- **NOT** a post-processing hack
- **IS** the central decision-maker for motion
- SadTalker generates proposals, Governor refines them

#### Intent Fusion (CORE INNOVATION)

```python
def process_coeff_file(
    coeff_path: Path,
    audio_path: Path,
    intent_timing_map: IntentTimingMap
) -> Path:
    """
    Combines TWO intent sources:
    
    1. Audio intent (RMS energy analysis via librosa)
       - Detects silence/speech from waveform
       - Returns: [T] mask (0.0=pause, 1.0=speech)
    
    2. Script intent (from XTTS timing map)
       - Knows semantic meaning (emphasis, sentence ends)
       - Returns: [T] mask (0.0=pause, 1.0-1.3=emphasis)
    
    Fusion: multiplicative (AND logic)
       combined_intent[t] = audio_intent[t] * script_intent[t]
    
    Result: BOTH audio AND script must agree for motion.
    """
```

#### Processing Pipeline (Per Frame)

```
Raw Coefficients (from SadTalker)
   ↓
1. CLAMP
   - Hard safety limits on pose/expr
   - Prevents wild motion
   ↓
2. INTENT GATE
   - Multiply by combined_intent[t]
   - Low intent → stillness
   - High intent → expressiveness
   ↓
3. STYLE SCALE
   - Apply style-specific factors
   - pose_scale, expr_strength
   ↓
4. TEMPORAL SMOOTH
   - IIR filter (removes jitter)
   - alpha = 1 - smoothing
   ↓
5. SENTENCE NOD (optional)
   - Subtle pitch impulse at sentence_end frames
   - Nod amplitude from style
   ↓
Governed Coefficients
```

#### Style Profiles

```python
@dataclass
class StyleProfile:
    name: str
    pose_max: Tuple[float, float, float]  # safety limits
    pose_scale: Tuple[float, float, float]  # scaling factors
    expr_strength: float
    smoothing: float  # 0..1 (higher = smoother)
    stillness_on_pause: float  # 0..1 (higher = stiller)
    nod_rate: float  # nods per second
    nod_amplitude: float  # pitch delta

# Presets
STYLE_PRESETS = {
    "calm_tech": StyleProfile(...),
    "energetic": StyleProfile(...),
    "lecturer": StyleProfile(...)
}
```

#### What Governor NEVER Touches

- **Lip/mouth coefficients**: Preserved for lip-sync
- **Identity coefficients**: Preserved for face consistency
- **Only modifies**: Pose (yaw/pitch/roll) + Expression (64-dim)

---

### 5. Script Intent Contract (`ai/script_intent.py`)

**Role**: Canonical schema for intent propagation

#### Classes

```python
@dataclass
class SegmentIntent:
    """Single script segment"""
    text: str
    pause_after: float  # seconds
    emphasis: List[str]  # words to stress
    sentence_end: bool  # triggers nod

@dataclass
class ScriptIntent:
    """Complete script"""
    segments: List[SegmentIntent]
    total_duration: Optional[float]  # filled after audio

@dataclass
class TimingSegment:
    """Audio timing for one segment"""
    segment_idx: int
    start_time: float
    end_time: float
    pause_after: float
    emphasis: List[str]
    sentence_end: bool

class IntentTimingMap:
    """Maps audio time → intent"""
    segments: List[TimingSegment]
    total_duration: float
    fps: int
    
    def build_intent_mask() -> np.ndarray:
        """[T] float mask for Motion Governor"""
```

#### Helper Functions

```python
def flatten_segments_to_text(script_intent) -> str:
    """Convert structured intent → plain text"""

def parse_gemini_intent_output(gemini_response) -> ScriptIntent:
    """Parse Gemini JSON → ScriptIntent"""

def create_simple_intent(text) -> ScriptIntent:
    """Fallback for plain text"""
```

---

### 6. Pipeline Manager (`ai/pipeline.py`)

**Role**: End-to-end orchestration

#### Initialization

```python
pipeline = PipelineManager(
    gemini_api_key=...,
    reference_audio=...,
    reference_image=...,
    motion_style="calm_tech",
    enable_intent=True,  # Intent-aware pipeline
    enable_governor=True  # Motion control
)
```

#### Generation

```python
result = await pipeline.generate_full_response(
    prompt="Talk about GPUs",
    enable_intent=True,
    enable_governor=True,
    motion_style="calm_tech"
)

# Returns:
{
    "text": "...",
    "script_intent": {...},
    "audio_path": "...",
    "intent_timing_map": {...},
    "video_path": "...",
    "metadata": {...}
}
```

---

## Intent Contract

### Why Intent is First-Class

Traditional pipeline: `Text → Audio → Video`  
- Each stage is blind to others
- No semantic understanding
- Motion is reactive, not intentional

Intent-aware pipeline: `Intent → Intent → Intent`  
- Intent flows through entire system
- Each stage enriches intent
- Motion is **intentional and coherent**

### Intent Evolution Through Pipeline

```
Stage 1: Gemini
   Intent created: {text, pause_after, emphasis, sentence_end}

Stage 2: XTTS
   Intent enriched: {start_time, end_time, audio frames}

Stage 3: Motion Governor
   Intent consumed: {combined audio + script mask [T]}
```

### Intent as Contract

- **Schema-based**: Not arbitrary data structures
- **Versioned**: Can evolve without breaking system
- **Serializable**: JSON for debugging/inspection
- **Type-safe**: Python dataclasses with validation

---

## Motion Governor Design

### Mental Model

```
SadTalker = "What if we move like this?"
Motion Governor = "No, move like THIS."
```

- SadTalker proposes motion
- Governor constrains/refines it
- Governor has final authority

### Intent Fusion Math

```python
# Audio intent (from RMS energy)
audio_mask[t] = 0.05 if silence else 1.0

# Script intent (from Gemini → XTTS)
script_mask[t] = 0.0 (pause) | 1.0 (normal) | 1.1-1.3 (emphasis)

# Fusion (multiplicative = AND logic)
combined[t] = audio_mask[t] * script_mask[t]

# Result interpretation:
# 0.0-0.1 = pause (strong stillness)
# 0.8-1.0 = normal speech
# 1.1-1.3 = emphasis (boost expressiveness)
```

### Why Multiplicative Fusion?

- **AND logic**: Both must agree
- **Natural zeros**: Either pause → result pause
- **Emphasis preserved**: 1.0 * 1.2 = 1.2
- **Commutative**: Order doesn't matter

### Temporal Smoothing

```python
# IIR filter (exponential moving average)
alpha = 1.0 - smoothing
output[t] = alpha * input[t] + (1 - alpha) * output[t-1]

# Higher smoothing → lower alpha → more history
# smoothing=0.8 → alpha=0.2 → 80% previous, 20% current
```

---

## Integration Points

### Gemini → XTTS

**Data**: `ScriptIntent` object  
**Method**: `xtts.synthesize_with_intent(script_intent, ...)`  
**Contract**: Intent must have `segments` list

### XTTS → SadTalker

**Data**: `IntentTimingMap` object  
**Method**: `sadtalker.generate(..., intent_timing_map=...)`  
**Contract**: Timing map must match audio duration

### SadTalker → Motion Governor

**Data**: `.mat` coefficient file  
**Method**: `governor.process_coeff_file(coeff_path, audio_path, intent_timing_map)`  
**Contract**: Coefficients must be SadTalker format (id+exp+tex+angles)

### Graceful Degradation

- If Gemini intent parsing fails → `create_simple_intent(text)`
- If XTTS segmentation fails → fallback to `synthesize(text)`
- If Governor fails → return original coefficients
- System never crashes due to intent issues

---

## Testing Strategy

### Test Modes

1. **Baseline**: SadTalker only (no governor, no intent)
2. **Audio-only**: Governor with audio intent only
3. **Script-only**: Governor with script intent only
4. **Full-intent**: Audio + script intent fusion
5. **Reference-style**: Custom style from video

### Test Script

```bash
python test_integration_pipeline.py
```

### Expected Outputs

```
outputs/integration_tests/
├── baseline/
│   ├── audio/
│   └── video/
├── audio_only/
├── script_only/
├── full_intent/
│   ├── intent/ (script.json, timing.json)
│   ├── audio/
│   └── video/
└── reference_style/
```

### Validation Criteria

- **Baseline**: Verify SadTalker works without modifications
- **Audio-only**: Check pause stillness from RMS
- **Script-only**: Verify emphasis boost from script
- **Full-intent**: Validate multiplicative fusion
- **Reference-style**: Custom motion parameters applied

---

## Future Extensions

### Short-Term

1. **MediaPipe Integration**: Higher-accuracy reference extraction
2. **GFPGAN Re-enable**: Test with motion governor at 512px
3. **Nod Tuning**: Refine sentence-end nod parameters
4. **Emphasis Detection**: Analyze pitch/volume for auto-emphasis

### Medium-Term

1. **Emotion Intent**: Add emotional state to intent (happy, serious, etc.)
2. **Gaze Control**: Eye direction based on intent
3. **Gesture Hints**: Upper body motion suggestions
4. **Multi-Speaker**: Handle dialogue with speaker switching

### Long-Term

1. **Real-Time Pipeline**: Streaming intent + generation
2. **Interactive Feedback**: User-guided motion tuning
3. **Style Learning**: Extract styles from multi-video corpus
4. **Cross-Lingual**: Intent propagation across languages

### Explicitly Out of Scope

- **Wav2Lip**: Lip-sync is SadTalker's job
- **XTTS Retraining**: Use as-is
- **Model Fine-tuning**: No retraining
- **Real-time Inference**: Batch processing only

---

## Conclusion

This is an **ARCHITECTED SYSTEM**, not a collection of hacks.

### Key Achievements

✅ Intent propagates from Gemini → XTTS → Motion Governor  
✅ Clean separation of concerns (proposal vs. director)  
✅ Deterministic, debuggable, explainable  
✅ Backward compatible (old code still works)  
✅ Production-ready error handling  

### Mental Model

```
Gemini = Scriptwriter (semantic understanding)
XTTS = Voice actor (timing + emphasis)
SadTalker = Puppeteer (motion proposals)
Motion Governor = Director (final authority)
```

### Next Steps

1. Run integration tests
2. Tune style parameters
3. Enable GFPGAN
4. Deploy to production

---

**Document Owner**: GitHub Copilot  
**Architecture Version**: 2.0  
**Last Refactor**: December 25, 2025
