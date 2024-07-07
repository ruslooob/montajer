from pprint import pprint
from typing import Literal

import os
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.VideoClip import TextClip

IMAGEMAGICK_BINARY = os.getenv('IMAGEMAGICK_BINARY')


def create_video_with_image(video_type: Literal['plain', 'short'],
                            image_path: str,
                            audio_path: str,
                            output_path: str,
                            text: str,
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

    # Create a text clip
    text_clip = TextClip(text, size=(900, 0), fontsize=60, color='white', font='./fonts/OpenSans-Bold.ttf')

    # Set the duration of the text clip to match the image duration
    text_clip = text_clip.set_duration(duration)

    # Position the text at the top of the video
    padding_top = 75
    text_clip = text_clip.set_position(('center', padding_top))

    # Composite the text clip on the image clip
    video_with_caption = CompositeVideoClip([video_clip, text_clip])

    # Save the final video with proper codec settings
    video_with_caption.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)


# Example usage:
image_path = 'photo.jpg'
audio_path = 'Hər_kəs_dilinə_hakim_olsa.mp3'
output_path = 'output_video.mp4'

create_video_with_image('plain', image_path, audio_path, output_path, 'Min bir hikmətli söz')
