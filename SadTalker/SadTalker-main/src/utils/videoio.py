import shutil
import uuid

import os
import subprocess

import cv2

# Use imageio-ffmpeg's bundled FFmpeg if system FFmpeg not available
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except:
    FFMPEG_PATH = 'ffmpeg'

def load_video_to_cv2(input_path):
    video_stream = cv2.VideoCapture(input_path)
    fps = video_stream.get(cv2.CAP_PROP_FPS)
    full_frames = [] 
    while 1:
        still_reading, frame = video_stream.read()
        if not still_reading:
            video_stream.release()
            break 
        full_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return full_frames

def save_video_with_watermark(video, audio, save_path, watermark=False):
    # Create temp file in same directory as input video
    video_dir = os.path.dirname(video)
    temp_file = os.path.join(video_dir, str(uuid.uuid4())+'.mp4')
    
    # Use subprocess instead of os.system for better path handling
    cmd = [FFMPEG_PATH, '-y', '-hide_banner', '-loglevel', 'error', 
           '-i', video, '-i', audio, '-vcodec', 'copy', temp_file]
    print(f"[DEBUG] FFmpeg command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"[DEBUG] FFmpeg exit code: {result.returncode}")
    if result.stderr:
        print(f"[DEBUG] FFmpeg stderr: {result.stderr}")
    print(f"[DEBUG] Temp file exists: {os.path.exists(temp_file)}")

    if watermark is False:
        shutil.move(temp_file, save_path)
    else:
        # watermark
        try:
            ##### check if stable-diffusion-webui
            import webui
            from modules import paths
            watarmark_path = paths.script_path+"/extensions/SadTalker/docs/sadtalker_logo.png"
        except:
            # get the root path of sadtalker.
            dir_path = os.path.dirname(os.path.realpath(__file__))
            watarmark_path = dir_path+"/../../docs/sadtalker_logo.png"

        cmd = [FFMPEG_PATH, '-y', '-hide_banner', '-loglevel', 'error',
               '-i', temp_file, '-i', watarmark_path, 
               '-filter_complex', '[1]scale=100:-1[wm];[0][wm]overlay=(main_w-overlay_w)-10:10',
               save_path]
        subprocess.run(cmd, check=False)
        os.remove(temp_file)