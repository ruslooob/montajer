import glob
import os
import random
from pathlib import Path
from typing import Tuple, Literal

from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip

from .ffmpeg_utils import convert_audiofile, detect_silence, remove_silence
from .file_utils import fix_filenames, remove_files


def clean_audiotrack(audio_path: Path):
    """
    Removes all silence from audiotrack and deletes all temporary files
    :param audio_path: path to audiofile
    """
    try:
        files_for_remove, audiotrack = _clean_audiotrack(audio_path)
        print(f"files for remove: {files_for_remove}")
        output_path = f"{str(audio_path)[:-4]}_fixed.mp3"
        audiotrack.write_audiofile(output_path)
    finally:
        remove_files([file for file in files_for_remove if not str(file).endswith(".mp3")])


def _clean_audiotrack(audio_path: Path, duration: int = None) -> Tuple[list[Path], AudioFileClip]:
    """
    Removes all silence from audiotrack.
    :param audio_path: path to audiofile
    :return tuple with creaeted filepaths and audioclip
    """
    filename = str(audio_path)[:-4]
    wav_path = Path(filename + '.wav')
    convert_audiofile(audio_path, wav_path)

    output_path = Path(f"{filename}_fixed.mp3")
    remove_silence(wav_path, detect_silence(wav_path, 0.5), 0.5, output_path)
    # todo убрать лишнюю конвертацию в mp3
    result = AudioFileClip(str(output_path))
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
    text_clip = TextClip(text, size=(900, 0), fontsize=60, color='white', font=font_path)

    text_clip = text_clip.set_duration(duration)

    text_clip = text_clip.set_position(('center', padding_top))

    return text_clip


def export_video(image_clip: ImageClip, audio_clip: AudioFileClip, text_clip: TextClip, output_path: str):
    video_clip = image_clip.set_audio(audio_clip)

    video_with_caption = CompositeVideoClip([video_clip, text_clip])

    video_with_caption.write_videofile(str(output_path), codec='libx264', audio_codec='aac', fps=24)


def create_video_with_image(image_path: str,
                            audio_path: Path,
                            output_path: Path,
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
        files_for_remove, audio_clip = _clean_audiotrack(audio_path, duration)
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


def create_videos_with_image(source_audio_folder_path: Path,
                             source_images_folder_path: Path,
                             output_video_folder_path: Path,
                             video_caption_text: str):
    """
    Creates videos from given audio folder path
    :param source_audio_folder_path:
    :param source_images_folder_path:
    :param output_video_folder_path:
    :param video_caption_text:
    :return:
    """
    fix_filenames(source_audio_folder_path)
    audio_paths = glob.glob(os.path.join(source_audio_folder_path, '*.mp3'))
    background_image_paths = glob.glob(os.path.join(source_images_folder_path, '*.jpg'))

    for audio_path in audio_paths:
        random_image_path = random.choice(background_image_paths)
        create_video_with_image(image_path=random_image_path,
                                audio_path=Path(audio_path),
                                output_path=Path(f'{output_video_folder_path}/{os.path.basename(audio_path)[:-4]}.mp4'),
                                text=video_caption_text)
