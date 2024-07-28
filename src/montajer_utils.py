import glob
import os
import random
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Literal

from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip

from .ffmpeg_utils import convert_audiofile, detect_silence, remove_silence, burn_subtitles_into_video
from .file_utils import fix_filenames, remove_files, find_first_mp3_file
from .subtitles_utils import write_subtitle_file, SubtitleFormat, SubtitlesConfig


def clean_audiotrack(audio_path: str, output_path: str):
    """
        Removes all silence from audiotrack and deletes all temporary files
        :param audio_path: path to audiofile
        :param output_path path o output audiofile
        """
    files_for_remove = []
    try:
        files_for_remove, audiotrack = _clean_audiotrack(audio_path)
        print(f"files for remove: {files_for_remove}")
        audiotrack.write_audiofile(output_path)
    finally:
        remove_files([file for file in files_for_remove if not file.endswith(".mp3")])


def clean_audiotrack(audio_path: str):
    clean_audiotrack(audio_path, f"{audio_path[:-4]}_fixed.mp3")


def _clean_audiotrack(audio_path: str, duration: int = None) -> Tuple[list[str], AudioFileClip]:
    """
    Removes all silence from audiotrack.
    :param audio_path: path to audiofile
    :return tuple with creaeted filepaths and audioclip (created filepaths can be used in future tasks (i.e creating subtitles)
    """
    filename = audio_path[:-4]
    wav_path = filename + '.wav'
    convert_audiofile(audio_path, wav_path)

    output_path = f"{filename}_fixed.mp3"
    remove_silence(wav_path, detect_silence(wav_path, 0.5), 0.5, output_path)
    # todo убрать лишнюю конвертацию в mp3
    result = AudioFileClip(output_path)
    files_for_remove = [output_path, wav_path]

    if not duration:
        return files_for_remove, result
    return files_for_remove, result.set_duration(duration)


VideoType = Literal['plain', 'short']


def add_image_background(video_type: VideoType, image_path: str, duration: int) -> ImageClip:
    image_clip = ImageClip(image_path).set_duration(duration)

    if video_type == 'plain':
        # Resize to fit height, keeping aspect ratio
        image_clip = image_clip.resize(height=1080)

        # If the resized image width is less than 1920, add padding
        if image_clip.size[0] < 1920:
            image_clip = image_clip.on_color(size=(1920, 1080), color=(0, 0, 0), pos=('center', 'center'))
    elif video_type == 'short':
        image_clip = image_clip.resize(height=1920)
        image_clip = image_clip.on_color(size=(1080, 1920), color=(0, 0, 0))
    else:
        raise ValueError(f"Invalid video_type. Expected values: ['plain', 'short']")

    return image_clip


def add_text_on_background(text: str, duration: int, font_path: str, padding_top: int = 75) -> TextClip:
    text_clip = TextClip(text, size=(900, 0), fontsize=60, color='white', font=font_path)

    text_clip = text_clip.set_duration(duration)

    text_clip = text_clip.set_position(('center', padding_top))

    return text_clip


def export_video(image_clip: ImageClip,
                 audio_clip: AudioFileClip,
                 text_clip: TextClip,
                 output_path: str,
                 duration=None):
    video_clip = image_clip.set_audio(audio_clip)

    video_with_caption = CompositeVideoClip([video_clip, text_clip])

    if duration:
        video_with_caption.set_duration(duration)
        text_clip.set_duration(duration)

    video_with_caption.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)


def create_video_with_image(image_path: str,
                            audio_path: str,
                            output_path: str,
                            text: str,
                            subtitles_enabled=False,
                            subtitles_config: SubtitlesConfig = None,
                            duration: int = None):
    """
    Creates video based on audio and background image
    :param image_path: path to background image
    :param audio_path: path to audiofile
    :param output_path: path to output video
    :param text: caption test on top of generated video
    :param duration: max duration of generated video. If None that output video duration will be same as clean-up audiotrack
    :param subtitles_enabled: option for generating subtitles
    :param subtitles_config: some parameters for subtitles generation
    :return: None
    """

    def determine_video_type(duration_in_seconds: int) -> VideoType:
        return 'plain' if duration_in_seconds > 60 else 'short'

    # Use the font path from the environment variable
    font_path = 'fonts/OpenSans-Bold.ttf'
    audio_clip = None
    files_for_remove = []

    try:
        files_for_remove, audio_clip = _clean_audiotrack(audio_path, duration)
        video_type = determine_video_type(audio_clip.duration)
        image_clip = add_image_background(video_type, image_path, audio_clip.duration)
        text_clip = add_text_on_background(text, audio_clip.duration, font_path)

        # todo сделать так, чтобы субтитры сразу вставлялись в видео
        export_video(image_clip, audio_clip, text_clip, output_path)
        if subtitles_enabled:
            subtitle_path = f'{audio_path[:-4]}.srt'
            write_subtitle_file(find_first_mp3_file(files_for_remove), subtitle_path, SubtitleFormat.SRT,
                                subtitles_config)
            burn_subtitles_into_video(output_path, subtitle_path, f'{output_path[:-4]}_subtitles.mp4')
    finally:
        audio_clip.close()
        remove_files(files_for_remove)


def create_videos_with_image(source_audio_folder_path: str,
                             source_images_folder_path: str,
                             output_video_folder_path: str,
                             video_caption_text: str,
                             subtitles_enabled=False,
                             subtitles_config: SubtitlesConfig = None,
                             threads=1):
    fix_filenames(source_audio_folder_path)
    audio_paths = glob.glob(os.path.join(source_audio_folder_path, '*.mp3'))
    print(f"audio paths: {audio_paths}")
    background_image_paths = glob.glob(os.path.join(source_images_folder_path, '*.jpg'))

    def create_video_helper(audio_path: str):
        random_image_path = random.choice(background_image_paths)
        output_path = f'{output_video_folder_path}/{os.path.basename(audio_path)[:-4]}.mp4'
        create_video_with_image(
            image_path=random_image_path,
            audio_path=audio_path,
            output_path=output_path,
            text=video_caption_text,
            subtitles_enabled=subtitles_enabled,
            subtitles_config=subtitles_config
        )

    if threads == -1:
        threads = os.cpu_count()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(create_video_helper, audio_path) for audio_path in audio_paths]
        for future in futures:
            future.result()
