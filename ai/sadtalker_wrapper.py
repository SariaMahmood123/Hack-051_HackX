"""
SadTalker Wrapper
Handles talking-head video generation from audio + image
"""
import sys
import torch
from pathlib import Path
from typing import Optional
import logging

# Add SadTalker to Python path (add main directory, not src)
SADTALKER_PATH = Path(__file__).parent.parent / "SadTalker" / "SadTalker-main"
sys.path.insert(0, str(SADTALKER_PATH))

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
            logger.info("[SadTalker] Loading models (this may take 30-60s)...")
            
            # Add SadTalker-main directory to path (so src. imports work)
            sad_main_path = str(SADTALKER_PATH)
            if sad_main_path not in sys.path:
                sys.path.insert(0, sad_main_path)
            
            # Import SadTalker modules WITH src. prefix (as they're meant to be)
            from src.utils.preprocess import CropAndExtract
            from src.test_audio2coeff import Audio2Coeff
            from src.facerender.animate import AnimateFromCoeff
            from src.utils.init_path import init_path
            
            # Initialize paths using SadTalker's own init_path function
            self.sadtalker_paths = init_path(
                checkpoint_dir=str(self.model_path),
                config_dir=str(SADTALKER_PATH / 'src' / 'config'),
                size=256,
                old_version=False,
                preprocess='crop'
            )
            
            # Store component classes for later use
            self.CropAndExtract = CropAndExtract
            self.Audio2Coeff = Audio2Coeff
            self.AnimateFromCoeff = AnimateFromCoeff
            
            logger.info("[SadTalker] [OK] Models loaded successfully")
            self.is_loaded = True
        
        except Exception as e:
            logger.error(f"[SadTalker] Failed to load model: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to load SadTalker model: {str(e)}")
    
    def generate(
        self,
        audio_path: Path,
        reference_image: Path,
        output_path: Path,
        fps: int = 25,
        enhancer: Optional[str] = "gfpgan"  # Options: "gfpgan", "RestoreFormer", None
    ) -> Path:
        """
        Generate talking-head video
        
        Args:
            audio_path: Path to audio file (WAV recommended)
            reference_image: Path to portrait image (clear frontal face)
            output_path: Where to save generated video
            fps: Frames per second for output video
            enhancer: Optional face enhancement model for better quality
        
        Returns:
            Path to generated video file
        """
        if not self.is_loaded:
            self.load_model()
        
        try:
            logger.info(f"[SadTalker] Generating video from {reference_image.name}")
            logger.info(f"[SadTalker] Audio: {audio_path.name}, FPS: {fps}, Enhancer: {enhancer}")
            
            # Import necessary modules
            from src.generate_batch import get_data
            from src.generate_facerender_batch import get_facerender_data
            import tempfile
            import shutil
            
            # Create temporary save directory
            with tempfile.TemporaryDirectory() as save_dir:
                save_dir = Path(save_dir)
                first_frame_dir = save_dir / 'first_frame_dir'
                first_frame_dir.mkdir(exist_ok=True)
                
                # Initialize models
                logger.info("[SadTalker] Initializing preprocessor...")
                preprocess_model = self.CropAndExtract(self.sadtalker_paths, self.device)
                
                logger.info("[SadTalker] Initializing audio-to-coefficient model...")
                audio_to_coeff = self.Audio2Coeff(self.sadtalker_paths, self.device)
                
                logger.info("[SadTalker] Initializing animation model...")
                animate_from_coeff = self.AnimateFromCoeff(self.sadtalker_paths, self.device)
                
                # Extract 3DMM coefficients from source image
                logger.info("[SadTalker] Extracting 3DMM from image...")
                first_coeff_path, crop_pic_path, crop_info = preprocess_model.generate(
                    str(reference_image),
                    str(first_frame_dir),
                    'crop',
                    source_image_flag=True,
                    pic_size=256
                )
                
                if first_coeff_path is None:
                    raise ValueError("Failed to extract coefficients from reference image")
                
                # Generate coefficients from audio
                logger.info("[SadTalker] Generating coefficients from audio...")
                batch = get_data(
                    first_coeff_path=first_coeff_path,
                    audio_path=str(audio_path),
                    device=self.device,
                    ref_eyeblink_coeff_path=None,
                    still=False
                )
                coeff_path = audio_to_coeff.generate(batch, save_dir, 0, None)
                
                # Generate animation frames
                logger.info("[SadTalker] Generating animation frames...")
                data = get_facerender_data(
                    coeff_path=coeff_path,
                    pic_path=crop_pic_path,
                    first_coeff_path=first_coeff_path,
                    audio_path=str(audio_path),
                    batch_size=1,
                    input_yaw_list=None,
                    input_pitch_list=None,
                    input_roll_list=None,
                    expression_scale=1.0,
                    still_mode=False,
                    preprocess='crop'
                )
                
                result = animate_from_coeff.generate(
                    x=data,
                    video_save_dir=str(save_dir),
                    pic_path=str(reference_image),
                    crop_info=crop_info,
                    enhancer=None,  # GFPGAN requires GPU but has loading issues  
                    background_enhancer=None,
                    preprocess='crop',
                    img_size=256  # Keep at 256 for stability
                )
                
                # Find generated video
                logger.info("[SadTalker] Locating generated video...")
                generated_videos = list(save_dir.glob("*.mp4"))
                if not generated_videos:
                    raise FileNotFoundError("No video file was generated")
                
                # Copy to final output path
                src_video = generated_videos[0]
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_video, output_path)
                
                file_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"[SadTalker] [OK] Video generated: {output_path.name} ({file_size:.2f} MB)")
                
                return output_path
        
        except Exception as e:
            logger.error(f"[SadTalker] Video generation failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Video generation failed: {str(e)}")
    
    async def generate_async(
        self,
        audio_path: Path,
        reference_image: Path,
        output_path: Path,
        fps: int = 25,
        enhancer: Optional[str] = "gfpgan"
    ) -> Path:
        """
        Async wrapper for generate
        Note: SadTalker is CPU/GPU bound, not I/O bound, so this just wraps the sync call
        """
        return self.generate(audio_path, reference_image, output_path, fps, enhancer)
    
    def unload_model(self):
        """Free GPU memory"""
        if self.model:
            del self.model
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self.is_loaded = False
            logger.info("[SadTalker] Model unloaded, GPU memory freed")

