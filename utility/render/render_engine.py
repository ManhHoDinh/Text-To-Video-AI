import time
import os
import tempfile
import platform
import subprocess
from moviepy.editor import (
    AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
    TextClip, VideoFileClip
)
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.audio_normalize import audio_normalize
import requests

# ----------------------
# DOWNLOAD FILE
# ----------------------
def download_file(url, filename):
    with open(filename, 'wb') as f:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        f.write(response.content)

# ----------------------
# FIND PROGRAM
# ----------------------
def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    return search_program(program_name)

# ----------------------
# MAIN RENDER FUNCTION
# ----------------------
def get_output_media(audio_file_path, timed_captions, background_video_data, video_server=None):
    OUTPUT_FILE_NAME = "rendered_video.mp4"

    # Set ImageMagick path if exists
    magick_path = get_program_path("magick")
    if magick_path:
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
    else:
        os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'

    visual_clips = []
    temp_files = []

    # ----------------------
    # HANDLE BACKGROUND VIDEO/IMAGE
    # ----------------------
    for item in background_video_data:
        t1, t2 = item['time']
        media_info = item['media']
        video_url = media_info.get('url')
        media_type = media_info.get('type', 'video')

        if not video_url:
            continue

        # Download file
        video_filename = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        download_file(video_url, video_filename)
        temp_files.append(video_filename)

        if media_type == 'video':
            clip = VideoFileClip(video_filename)
        elif media_type == 'image':
            # convert image to video clip with duration
            clip = ImageClip(video_filename, duration=t2 - t1)
        else:
            continue

        clip = clip.set_start(t1).set_end(t2)
        visual_clips.append(clip)

    # ----------------------
    # ADD AUDIO
    # ----------------------
    audio_clip = AudioFileClip(audio_file_path)
    audio_clips = [audio_clip]

    # ----------------------
    # ADD TIMED CAPTIONS
    # ----------------------
    for (t1, t2), text in timed_captions:
        text_clip = TextClip(
            txt=text,
            fontsize=40,             # chữ nhỏ hơn
            color="white",
            stroke_width=2,
            stroke_color="black",
            method="caption",        # wrap chữ đẹp hơn
            size=(1280, None),       # giới hạn width để wrap chữ
            align='center'
        ).set_start(t1).set_end(t2).set_position(("center", "bottom"))
        visual_clips.append(text_clip)

    # ----------------------
    # COMPOSITE VIDEO + AUDIO
    # ----------------------
    final_video = CompositeVideoClip(visual_clips)
    final_video.audio = CompositeAudioClip(audio_clips)
    final_video.duration = final_video.audio.duration

    final_video.write_videofile(
        OUTPUT_FILE_NAME,
        codec='libx264',
        audio_codec='aac',
        fps=25,
        preset='veryfast'
    )

    # ----------------------
    # CLEAN UP TEMP FILES
    # ----------------------
    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass

    return OUTPUT_FILE_NAME
