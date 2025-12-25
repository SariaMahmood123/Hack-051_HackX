"""
SadTalker Wrapper
Handles talking-head video generation from audio + image

ARCHITECTURAL DESIGN:
- SadTalker = motion proposal generator (identity + pose + expr + lips)
- Motion Governor = director/constraint system
- Clean separation: generate_coeffs → govern_coeffs → render_video
"""
import sys
import torch
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict
import logging
from PIL import Image
import tempfile
import shutil

# Add SadTalker to Python path (add main directory, not src)
SADTALKER_PATH = Path(__file__).parent.parent / "SadTalker" / "SadTalker-main"
sys.path.insert(0, str(SADTALKER_PATH))

# Import Motion Governor
try:
    from ai.motion_governor import MotionGovernor, STYLE_PRESETS, StyleProfile
    MOTION_GOVERNOR_AVAILABLE = True
except ImportError:
    MOTION_GOVERNOR_AVAILABLE = False
    StyleProfile = None
    logging.warning("[SadTalker] Motion Governor not available")

# Import intent contract
try:
    from ai.script_intent import IntentTimingMap
    INTENT_AVAILABLE = True
except ImportError:
    INTENT_AVAILABLE = False
    IntentTimingMap = None

logger = logging.getLogger("lumen")


class SadTalkerWrapper:
    """
    Wrapper for SadTalker
    Generates talking-head videos from audio and a reference portrait
    
    Note: SadTalker requires GPU for reasonable performance
    Pipeline: Audio + Image → Face Animation → Video
    """
    
    def __init__(
        self, 
        model_path: Optional[Path] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize SadTalker
        
        Args:
            model_path: Path to SadTalker checkpoints
            device: Device to run inference on (cuda/cpu)
        """
        self.device = device
        self.model_path = model_path or (SADTALKER_PATH / "checkpoints")
        self.model = None
        self.is_loaded = False
        
        logger.info(f"[SadTalker] Initialized on {device}")
        logger.info(f"[SadTalker] Model path: {self.model_path}")
    
    def load_model(self):
        """
        Load SadTalker model into memory
        This is separate from __init__ to allow lazy loading
        """
        if self.is_loaded:
            return
        
        try:
            logger.info("[SadTalker] Loading models (this may take 60-90s on first run)...")
            logger.info("[SadTalker] Step 1/4: Adding SadTalker to path...")
            
            # Add SadTalker-main directory to path (so src. imports work)
            sad_main_path = str(SADTALKER_PATH)
            if sad_main_path not in sys.path:
                sys.path.insert(0, sad_main_path)
            
            # Import SadTalker modules WITH src. prefix (as they're meant to be)
            logger.info("[SadTalker] Step 2/4: Importing modules (may take 30-60s)...")
            from src.utils.preprocess import CropAndExtract
            from src.test_audio2coeff import Audio2Coeff
            from src.facerender.animate import AnimateFromCoeff
            from src.utils.init_path import init_path
            
            logger.info("[SadTalker] Step 3/4: Initializing paths...")
            # Initialize paths using SadTalker's own init_path function
            self.sadtalker_paths = init_path(
                checkpoint_dir=str(self.model_path),
                config_dir=str(SADTALKER_PATH / 'src' / 'config'),
                size=256,  # Use 256 for stability
                old_version=False,
                preprocess='crop'  # Use crop (more reliable than full)
            )
            
            logger.info("[SadTalker] Step 4/4: Storing component classes...")
            # Store component classes for later use
            self.CropAndExtract = CropAndExtract
            self.Audio2Coeff = Audio2Coeff
            self.AnimateFromCoeff = AnimateFromCoeff
            
            logger.info("[SadTalker] ✓ Models loaded successfully!")
            self.is_loaded = True
        
        except Exception as e:
            logger.error(f"[SadTalker] Failed to load model: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to load SadTalker model: {str(e)}")
    
    def preprocess_face_image(self, image_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Preprocess image to ensure it has a properly detected and cropped face.
        This prevents NaN errors in face alignment and ensures usable images.
        
        Args:
            image_path: Input image path
            output_path: Output path for preprocessed image (auto-generated if None)
        
        Returns:
            Path to preprocessed image
        """
        try:
            # Load image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            h, w = img.shape[:2]
            logger.info(f"[SadTalker] Preprocessing image {image_path.name} ({w}x{h})...")
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Try multiple face detection methods for robustness
            faces = []
            
            # Method 1: Haar Cascade (frontal face)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )
            
            if len(faces) == 0:
                # Try with more lenient parameters
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.05,
                    minNeighbors=3,
                    minSize=(80, 80)
                )
            
            if len(faces) == 0:
                # Method 2: Try alternate Haar Cascade
                alt_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
                alt_cascade = cv2.CascadeClassifier(alt_cascade_path)
                faces = alt_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.05,
                    minNeighbors=3,
                    minSize=(60, 60)
                )
            
            if len(faces) == 0:
                logger.warning(f"[SadTalker] No face detected in {image_path.name}, using center crop")
                # If no face detected, crop center square
                size = min(w, h)
                x = (w - size) // 2
                y = (h - size) // 2
                cropped = img[y:y+size, x:x+size]
            else:
                # Use the largest detected face
                if len(faces) > 1:
                    logger.info(f"[SadTalker] Detected {len(faces)} faces, using the largest one")
                    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                
                x, y, face_w, face_h = faces[0]
                logger.info(f"[SadTalker] ✓ Face detected at ({x}, {y}) size {face_w}x{face_h}")
                
                # Add generous margin around face (70% on each side for context)
                margin = 0.7
                x1 = max(0, int(x - face_w * margin))
                y1 = max(0, int(y - face_h * margin))
                x2 = min(w, int(x + face_w * (1 + margin)))
                y2 = min(h, int(y + face_h * (1 + margin)))
                
                # Crop face region
                cropped = img[y1:y2, x1:x2]
                
                # Make it square by padding if needed
                crop_h, crop_w = cropped.shape[:2]
                if crop_h != crop_w:
                    size = max(crop_h, crop_w)
                    # Create square canvas with mean color of cropped region
                    mean_color = np.mean(cropped, axis=(0, 1)).astype(np.uint8)
                    square = np.full((size, size, 3), mean_color, dtype=np.uint8)
                    # Center the cropped face
                    y_offset = (size - crop_h) // 2
                    x_offset = (size - crop_w) // 2
                    square[y_offset:y_offset+crop_h, x_offset:x_offset+crop_w] = cropped
                    cropped = square
            
            # Resize to optimal size for SadTalker (512x512)
            cropped = cv2.resize(cropped, (512, 512), interpolation=cv2.INTER_LANCZOS4)
            
            # Validate the final image has content
            img_std = np.std(cropped)
            mean_brightness = np.mean(cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY))
            
            logger.info(f"[SadTalker] Image stats - std: {img_std:.2f}, brightness: {mean_brightness:.1f}/255")
            
            # Check if image is valid
            if img_std < 5:
                logger.error(f"[SadTalker] Image has insufficient variance (std: {img_std:.2f}), skipping preprocessing")
                return image_path
            
            # Generate output path if not provided
            if output_path is None:
                output_path = image_path.parent / f"{image_path.stem}_preprocessed{image_path.suffix}"
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save preprocessed image with high quality
            success = cv2.imwrite(str(output_path), cropped, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if not success:
                logger.error(f"[SadTalker] Failed to save preprocessed image")
                return image_path
            
            # Verify the saved image can be read back
            verify = cv2.imread(str(output_path))
            if verify is None:
                logger.error(f"[SadTalker] Saved image cannot be read back")
                return image_path
            
            logger.info(f"[SadTalker] ✓ Preprocessed image saved to {output_path.name}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"[SadTalker] Face preprocessing failed: {str(e)}", exc_info=True)
            # If preprocessing fails, return original image path
            logger.warning(f"[SadTalker] Using original image without preprocessing")
            return image_path
    
    
    def generate_coeffs(
        self,
        audio_path: Path,
        reference_image: Path,
        fps: int = 25,
    ) -> Dict[str, Path]:
        """
        STAGE 1: Generate raw coefficients from audio + image.
        
        This is the "motion proposal" stage - SadTalker generates base motion.
        
        Args:
            audio_path: Audio file path
            reference_image: Portrait image path
            fps: Frames per second
        
        Returns:
            Dict with paths:
                'coeff_path': Path to coefficient .mat file
                'crop_pic_path': Cropped face image
                'crop_info': Crop metadata
                'first_coeff_path': Reference coefficients
                'save_dir': Temp directory (must be kept until render)
        """
        if not self.is_loaded:
            self.load_model()
        
        audio_path = Path(audio_path)
        reference_image = Path(reference_image)
        
        # Preprocess face
        logger.info(f"[SadTalker:Coeffs] Preprocessing face image...")
        preprocessed_image = self.preprocess_face_image(reference_image)
        if preprocessed_image != reference_image:
            logger.info(f"[SadTalker:Coeffs] Using preprocessed: {preprocessed_image.name}")
            reference_image = preprocessed_image
        
        try:
            # Import necessary modules
            from src.generate_batch import get_data
            
            # Create temp directory (caller must manage cleanup)
            save_dir = Path(tempfile.mkdtemp(prefix="sadtalker_"))
            first_frame_dir = save_dir / 'first_frame_dir'
            first_frame_dir.mkdir(exist_ok=True)
            
            logger.info("[SadTalker:Coeffs] Initializing preprocessor...")
            preprocess_model = self.CropAndExtract(self.sadtalker_paths, self.device)
            
            logger.info("[SadTalker:Coeffs] Initializing audio-to-coefficient model...")
            audio_to_coeff = self.Audio2Coeff(self.sadtalker_paths, self.device)
            
            # Extract 3DMM from image
            logger.info("[SadTalker:Coeffs] Extracting 3DMM from image...")
            first_coeff_path, crop_pic_path, crop_info = preprocess_model.generate(
                str(reference_image),
                str(first_frame_dir),
                'crop',
                source_image_flag=True,
                pic_size=512
            )
            
            if first_coeff_path is None:
                raise ValueError("Failed to extract coefficients from reference image")
            
            # Generate coefficients from audio
            logger.info("[SadTalker:Coeffs] Generating coefficients from audio...")
            batch = get_data(
                first_coeff_path=first_coeff_path,
                audio_path=str(audio_path),
                device=self.device,
                ref_eyeblink_coeff_path=None,
                still=False
            )
            coeff_path = audio_to_coeff.generate(batch, save_dir, 0, None)
            
            logger.info(f"[SadTalker:Coeffs] ✓ Raw coefficients generated: {Path(coeff_path).name}")
            
            return {
                'coeff_path': Path(coeff_path),
                'crop_pic_path': crop_pic_path,
                'crop_info': crop_info,
                'first_coeff_path': first_coeff_path,
                'save_dir': save_dir,
                'audio_path': audio_path,
                'reference_image': reference_image
            }
            
        except Exception as e:
            logger.error(f"[SadTalker:Coeffs] Failed: {e}", exc_info=True)
            raise RuntimeError(f"Coefficient generation failed: {e}")
    
    def govern_coeffs(
        self,
        coeff_data: Dict[str, Path],
        motion_style = "calm_tech",
        intent_timing_map: Optional['IntentTimingMap'] = None,
        enable_governor: bool = True,
        fps: int = 25
    ) -> Dict[str, Path]:
        """
        STAGE 2: Apply Motion Governor to constrain/improve coefficients.
        
        This is the "director" stage - Motion Governor refines the motion.
        
        Args:
            coeff_data: Output from generate_coeffs()
            motion_style: Style preset name or StyleProfile object
            intent_timing_map: Script-based intent from XTTS (optional)
            enable_governor: Enable motion control
            fps: Frames per second
        
        Returns:
            Updated coeff_data with governed coefficients
        """
        if not enable_governor:
            logger.info("[SadTalker:Govern] Governor disabled, using raw coefficients")
            return coeff_data
        
        if not MOTION_GOVERNOR_AVAILABLE:
            logger.warning("[SadTalker:Govern] Motion Governor not available")
            return coeff_data
        
        try:
            # Determine style
            if isinstance(motion_style, str):
                style_profile = STYLE_PRESETS.get(motion_style, STYLE_PRESETS["calm_tech"])
                style_name = motion_style
            elif StyleProfile and isinstance(motion_style, StyleProfile):
                style_profile = motion_style
                style_name = motion_style.name
            else:
                logger.warning(f"[SadTalker:Govern] Invalid motion_style, using calm_tech")
                style_profile = STYLE_PRESETS["calm_tech"]
                style_name = "calm_tech"
            
            logger.info(f"[SadTalker:Govern] Applying Motion Governor (style: {style_name})...")
            
            # Create governor
            governor = MotionGovernor(style_profile=style_profile, fps=fps)
            
            # Process coefficients
            governed_coeff_path = governor.process_coeff_file(
                coeff_path=coeff_data['coeff_path'],
                audio_path=coeff_data['audio_path'],
                intent_timing_map=intent_timing_map  # NEW: script intent integration
            )
            
            # Update coeff_data
            coeff_data['coeff_path'] = governed_coeff_path
            coeff_data['governed'] = True
            
            logger.info(f"[SadTalker:Govern] ✓ Motion governed successfully")
            
            return coeff_data
            
        except Exception as e:
            logger.error(f"[SadTalker:Govern] Failed: {e}", exc_info=True)
            logger.warning("[SadTalker:Govern] Fallback: using raw coefficients")
            coeff_data['governed'] = False
            return coeff_data
    
    def render_video(
        self,
        coeff_data: Dict[str, Path],
        output_path: Path,
        enhancer: Optional[str] = None,
        fps: int = 25
    ) -> Path:
        """
        STAGE 3: Render final video from coefficients.
        
        This is the "rendering" stage - convert coefficients to video.
        
        Args:
            coeff_data: Output from govern_coeffs() (or generate_coeffs())
            output_path: Output video path
            enhancer: Face enhancement model (gfpgan, RestoreFormer, None)
            fps: Frames per second
        
        Returns:
            Path to generated video
        """
        if not self.is_loaded:
            self.load_model()
        
        output_path = Path(output_path)
        
        try:
            from src.generate_facerender_batch import get_facerender_data
            
            logger.info("[SadTalker:Render] Initializing animation model...")
            animate_from_coeff = self.AnimateFromCoeff(self.sadtalker_paths, self.device)
            
            # Prepare rendering data
            logger.info("[SadTalker:Render] Preparing animation data...")
            data = get_facerender_data(
                coeff_path=str(coeff_data['coeff_path']),
                pic_path=coeff_data['crop_pic_path'],
                first_coeff_path=coeff_data['first_coeff_path'],
                audio_path=str(coeff_data['audio_path']),
                batch_size=1,
                input_yaw_list=None,
                input_pitch_list=None,
                input_roll_list=None,
                expression_scale=1.0,
                still_mode=False,
                preprocess='crop'
            )
            
            # Render video
            logger.info("[SadTalker:Render] Rendering video...")
            result = animate_from_coeff.generate(
                x=data,
                video_save_dir=str(coeff_data['save_dir']),
                pic_path=str(coeff_data['reference_image']),
                crop_info=coeff_data['crop_info'],
                enhancer=enhancer,
                background_enhancer=None,
                preprocess='crop',
                img_size=512
            )
            
            # Find and copy generated video
            logger.info("[SadTalker:Render] Locating generated video...")
            generated_videos = list(coeff_data['save_dir'].glob("*.mp4"))
            if not generated_videos:
                raise FileNotFoundError("No video file was generated")
            
            src_video = generated_videos[0]
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_video, output_path)
            
            # Clean up temp directory
            try:
                shutil.rmtree(coeff_data['save_dir'])
            except Exception as e:
                logger.warning(f"[SadTalker:Render] Failed to clean temp dir: {e}")
            
            file_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"[SadTalker:Render] ✓ Video rendered: {output_path.name} ({file_size:.2f} MB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"[SadTalker:Render] Failed: {e}", exc_info=True)
            raise RuntimeError(f"Video rendering failed: {e}")
    
    def generate(
        self,
        audio_path: Path,
        reference_image: Path,
        output_path: Path,
        fps: int = 25,
        enhancer: Optional[str] = "gfpgan",
        enable_motion_governor: bool = True,
        motion_style = "calm_tech",
        intent_timing_map: Optional['IntentTimingMap'] = None
    ) -> Path:
        """
        COMPLETE PIPELINE: Generate talking-head video (backward compatible).
        
        This method orchestrates all three stages:
        1. generate_coeffs() - SadTalker motion proposal
        2. govern_coeffs() - Motion Governor refinement
        3. render_video() - Final rendering
        
        Args:
            audio_path: Audio file path
            reference_image: Portrait image path
            output_path: Output video path
            fps: Frames per second
            enhancer: Face enhancement (gfpgan, RestoreFormer, None)
            enable_motion_governor: Enable motion control
            motion_style: Style preset or StyleProfile object
            intent_timing_map: Script intent from XTTS (NEW)
        
        Returns:
            Path to generated video
        """
        logger.info(f"[SadTalker] === COMPLETE PIPELINE ===")
        logger.info(f"[SadTalker] Audio: {audio_path.name}")
        logger.info(f"[SadTalker] Image: {reference_image.name}")
        logger.info(f"[SadTalker] Governor: {enable_motion_governor}")
        logger.info(f"[SadTalker] Style: {motion_style if isinstance(motion_style, str) else motion_style.name if motion_style else 'none'}")
        logger.info(f"[SadTalker] Intent: {'YES' if intent_timing_map else 'NO'}")
        
        # Stage 1: Generate coefficients
        coeff_data = self.generate_coeffs(audio_path, reference_image, fps)
        
        # Stage 2: Govern coefficients
        coeff_data = self.govern_coeffs(
            coeff_data,
            motion_style=motion_style,
            intent_timing_map=intent_timing_map,
            enable_governor=enable_motion_governor,
            fps=fps
        )
        
        # Stage 3: Render video
        return self.render_video(coeff_data, output_path, enhancer, fps)
    
    async def generate_async(
        self,
        audio_path: Path,
        reference_image: Path,
        output_path: Path,
        fps: int = 25,
        enhancer: Optional[str] = "gfpgan",
        enable_motion_governor: bool = True,
        motion_style = "calm_tech",
        intent_timing_map: Optional['IntentTimingMap'] = None
    ) -> Path:
        """
        Async wrapper for generate (backward compatible)
        Note: SadTalker is CPU/GPU bound, not I/O bound
        """
        return self.generate(
            audio_path, reference_image, output_path, fps, 
            enhancer, enable_motion_governor, motion_style, intent_timing_map
        )
    
    def unload_model(self):
        """Free GPU memory"""
        if self.model:
            del self.model
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self.is_loaded = False
            logger.info("[SadTalker] Model unloaded, GPU memory freed")
