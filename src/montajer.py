import glob
import os
import random
from pathlib import Path
from typing import Tuple, Literal

from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip

from .ffmpeg_utils import convert_audiofile, detect_silence, remove_silence
from .file_utils import fix_filenames, remove_files


# todo make audio_path path type
def clean_audiotrack(audio_path: str, duration: int = None) -> Tuple[list[str], AudioFileClip]:
    filename = audio_path[:-4]
    output_path = f"{filename}_fixed.mp3"
    wav_path = filename + '.wav'
    convert_audiofile(audio_path, wav_path)
    remove_silence(wav_path, detect_silence(wav_path, 0.5), 0.5, output_path)
    result = AudioFileClip(output_path)
    files_for_remove = [output_path, wav_path]
    if not duration:
        return files_for_remove, result
    return files_for_remove, result.set_duration(duration)


def add_image_background(video_type: Literal['plain', 'short'], image_path: str, duration: int) -> ImageClip:
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
    # Create a text clip
    text_clip = TextClip(text, size=(900, 0), fontsize=60, color='white', font=font_path)

    # Set the duration of the text clip to match the image duration
    text_clip = text_clip.set_duration(duration)

    # Position the text at the top of the video
    text_clip = text_clip.set_position(('center', padding_top))

    return text_clip


def export_video(image_clip: ImageClip, audio_clip: AudioFileClip, text_clip: TextClip, output_path: str):
    # Set the audio to the image clip
    video_clip = image_clip.set_audio(audio_clip)

    # Composite the text clip on the image clip
    video_with_caption = CompositeVideoClip([video_clip, text_clip])

    # Save the final video with proper codec settings
    video_with_caption.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)


def create_video_with_image(image_path: str,
                            audio_path: str,
                            output_path: str,
                            text: str,
                            duration: int = None):
    """
    Creates video based on audio and background image
    :param image_path: path to background image
    :param audio_path: path to audiofile
    :param output_path: path to output video
    :param text: caption test on top of generated video
    :param duration: max duration of generated video. If None that output video duration will be same as clean-up audiotrack
    :return: None
    """
    # Use the font path from the environment variable
    font_path = 'fonts/OpenSans-Bold.ttf'
    try:
        files_for_remove, audio_clip = clean_audiotrack(audio_path, duration)
        if audio_clip.duration > 60:
            video_type = 'plain'
        else:
            video_type = 'short'
        image_clip = add_image_background(video_type, image_path, audio_clip.duration)
        text_clip = add_text_on_background(text, audio_clip.duration, font_path)
        export_video(image_clip, audio_clip, text_clip, output_path)
    finally:
        audio_clip.close()
        remove_files(files_for_remove)


def create_videos_with_image(source_mp3_folder_path: Path,
                             source_images_folder_path: Path,
                             output_video_folder_path: Path,
                             video_caption_text: str):
    """
    Creates videos from given audio folder path
    :param source_mp3_folder_path:
    :param source_images_folder_path:
    :param output_video_folder_path:
    :param video_caption_text:
    :return:
    """
    fix_filenames(str(source_mp3_folder_path))
    mp3_paths = glob.glob(os.path.join(source_mp3_folder_path, '*.mp3'))
    background_image_paths = glob.glob(os.path.join(source_images_folder_path, '*.jpg'))

    for mp3_path in mp3_paths:
        random_image_path = random.choice(background_image_paths)
        create_video_with_image(image_path=str(random_image_path),
                                audio_path=str(mp3_path),
                                output_path=f'{output_video_folder_path}/{os.path.basename(mp3_path)[:-4]}.mp4',
                                text=video_caption_text)
