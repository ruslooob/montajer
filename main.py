from typing import Literal

from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.VideoClip import TextClip


def create_video_with_image(video_type: Literal['plain', 'short'],
                            image_path: str,
                            audio_path: str,
                            output_path: str,
                            duration: int = 10):
    # Load the static image
    image_clip = ImageClip(image_path).set_duration(duration)

    # Resize the image to 1920x1080
    if video_type == 'plain':
        # stretch to fit
        image_clip = image_clip.resize(newsize=(1920, 1080))
    elif video_type == 'short':
        # resize keep aspect
        image_clip = image_clip.resize(height=1920)
        image_clip = image_clip.on_color(size=(1080, 1920), color=(0, 0, 0))
    else:
        raise ValueError(f"Неверный параметр video_type. Доступные значения: ['plain', short]")

    # Load the audio file
    audio_clip = AudioFileClip(audio_path).set_duration(duration)

    # Set the audio to the image clip
    video_clip = image_clip.set_audio(audio_clip)

    # Save the final video with proper codec settings
    video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)


# Example usage:
image_path = 'photo.jpg'
audio_path = 'Hər_kəs_dilinə_hakim_olsa.mp3'
output_path = 'output_video.mp4'

create_video_with_image('plain', image_path, audio_path, output_path)
