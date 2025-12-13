from utility.script.script_generator import generate_script, extract_text_for_tts
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a topic.")
    parser.add_argument("topic", type=str, help="The topic for the video")
    args = parser.parse_args()

    SAMPLE_TOPIC = args.topic
    SAMPLE_FILE_NAME = "audio_tts.mp3"
    VIDEO_SERVER = "pexel"

    # 1. Generate clean script text
    script_text = generate_script(SAMPLE_TOPIC)
    print("script:", script_text)

    # 2. Generate TTS audio safely
    # Lấy toàn bộ text từ script JSON
    text_for_tts = extract_text_for_tts(script_text)
    print(text_for_tts)
    # Gọi hàm tạo audio với chuỗi text
    generate_audio(text_for_tts, SAMPLE_FILE_NAME)
    # 3. Generate whisper timestamps
    timed_captions = generate_timed_captions(
      audio_filename=SAMPLE_FILE_NAME,
      script_json=script_text,   # đổi tên tham số
      model_size="medium"
    )

    print(timed_captions)

    # 4. Generate search terms from captions
    search_terms = getVideoSearchQueriesTimed(script_text, timed_captions)
    print(search_terms)
    # 5. Get background videos
    if search_terms:
        background_video_urls = generate_video_url(search_terms)
        print(background_video_urls)
    else:
        print("No background video")
        background_video_urls = None
    print(background_video_urls)
    # 6. Merge empty intervals
    background_video_urls = merge_empty_intervals(background_video_urls)

    # 7. Final video rendering
    if background_video_urls:
        video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
        print(video)
    else:
        print("No video")
