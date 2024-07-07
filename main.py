import glob
import os
import random
import re
import subprocess
import time
from pathlib import Path
from typing import Literal, Tuple

import numpy as np
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
from scipy.io.wavfile import read, write
from tqdm import tqdm


def convert_mp3_to_wav(input_path: str, output_path: str):
    """
    Convert an MP3 file to a WAV file using FFmpeg.

    Args:
        input_path (str): Path to the input MP3 file.
        output_path (str): Path to the output WAV file.
    """
    command = ['ffmpeg', '-hide_banner', '-y', '-i', input_path, output_path]
    subprocess.run(command, check=True)


def detect_silence(path, time):
    '''
    This function is a python wrapper to run the ffmpeg command in python and extract the desired output

    path= Audio file path
    time = silence time threshold

    returns = list of tuples with start and end point of silences
    '''
    command = "ffmpeg -i " + path + " -af silencedetect=n=-30dB:d=" + str(time) + " -f null -"
    out = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()
    s = stdout.decode("utf-8")
    k = s.split('[silencedetect @')
    if len(k) == 1:
        # print(stderr)
        return None

    start, end = [], []
    for line in k:
        if "silence_start" in line:
            try:
                start_time = float(line.split("silence_start: ")[1])
                start.append(start_time)
            except ValueError:
                continue
        elif "silence_end" in line:
            try:
                parts = line.split("silence_end: ")
                if len(parts) > 1:
                    end_time = float(parts[1].split(" |")[0])
                    end.append(end_time)
            except ValueError:
                continue
    if len(start) != len(end):
        min_len = min(len(start), len(end))
        start = start[:min_len]
        end = end[:min_len]

    return list(zip(start, end))


def remove_silence(path, sil, keep_sil, out_path):
    '''
    This function removes silence from the audio.

    Input:
    path = Input audio file path
    sil = List of silence time slots that needs to be removed
    keep_sil = Time to keep as allowed silence after removing silence
    out_path = Output path of audio file

    returns:
    Non - silent patches and save the new audio in out path
    '''
    rate, aud = read(path)
    a = float(keep_sil) / 2
    sil_updated = [(i[0] + a, i[1] - a) for i in sil]

    # convert the silence patch to non-sil patches
    non_sil = []
    tmp = 0
    ed = len(aud) / rate
    for i in range(len(sil_updated)):
        non_sil.append((tmp, sil_updated[i][0]))
        tmp = sil_updated[i][1]
    if sil_updated[-1][1] + a / 2 < ed:
        non_sil.append((sil_updated[-1][1], ed))
    if non_sil[0][0] == non_sil[0][1]:
        del non_sil[0]

    # cut the audio
    ans = []
    ad = list(aud)
    for i in tqdm(non_sil, desc='Удаление пустых частей аудиодорожки...'):
        ans = ans + ad[int(i[0] * rate):int(i[1] * rate)]
    # nm=path.split('/')[-1]
    write(out_path, rate, np.array(ans))
    return non_sil


def clean_audiotrack(audio_path: str, duration: int) -> Tuple[list[str], AudioFileClip]:
    filename = audio_path[:-4]
    output_path = f"{filename}_fixed.mp3"
    wav_path = filename + '.wav'
    convert_mp3_to_wav(audio_path, wav_path)
    remove_silence(wav_path, detect_silence(wav_path, 0.5), 0.5, output_path)
    result = AudioFileClip(output_path)
    files_for_remove = [output_path, wav_path]
    if not duration:
        return files_for_remove, result
    return files_for_remove, result.set_duration(duration)


def add_image_background(video_type: Literal['plain', 'short'], image_path: str, duration: int) -> ImageClip:
    # Load the static image
    image_clip = ImageClip(image_path).set_duration(duration)

    # Resize the image to 1920x1080
    if video_type == 'plain':
        # Stretch to fit
        image_clip = image_clip.resize(newsize=(1920, 1080))
    elif video_type == 'short':
        # Resize keep aspect
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
    video_with_caption.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24, threads=4)


def remove_files(files_for_remove: list[str]):
    for file_path in files_for_remove:
        os.remove(file_path)


def create_video_with_image(image_path: str,
                            audio_path: str,
                            output_path: str,
                            text: str,
                            duration: int = None):
    """
    Создать видео на основе аудиодорожки и изображения
    :param image_path: путь до изображения на заднем плане
    :param audio_path: путь до аудиодорожки
    :param output_path: путь для получившегося видео
    :param text: Надпись на видео
    :param duration: длительность получившегося видео, если None, то длительность видео равна длине отредактированной аудиодорожки
    :return: ничего не возвращает
    """
    # Use the font path from the environment variable
    font_path = './fonts/OpenSans-Bold.ttf'

    files_for_remove, audio_clip = clean_audiotrack(audio_path, duration)
    if audio_clip.duration > 60:
        video_type = 'plain'
    else:
        video_type = 'short'
    image_clip = add_image_background(video_type, image_path, audio_clip.duration)
    text_clip = add_text_on_background(text, audio_clip.duration, font_path)
    export_video(image_clip, audio_clip, text_clip, output_path)
    remove_files(files_for_remove)


def fix_filenames(folder):
    """
    Fixes filenames in the specified folder by replacing spaces with underscores
    and removing special characters except dots in file extensions.
    """
    if not folder.endswith('/'):
        folder += '/'

    for filename in os.listdir(folder):
        name, extension = os.path.splitext(filename)
        fixed_name = name.replace(' ', '_')
        fixed_name = re.sub(r'[^\w\s]', '', fixed_name)
        fixed_filename = fixed_name + extension
        os.rename(os.path.join(folder, filename), os.path.join(folder, fixed_filename))


def create_videos_with_image(source_mp3_folder_path: Path,
                             source_images_path: Path,
                             output_video_folder_path: Path,
                             video_caption_text: str):
    fix_filenames(str(source_mp3_folder_path))
    mp3_paths = glob.glob(os.path.join(source_mp3_folder_path, '*.mp3'))
    background_image_paths = glob.glob(os.path.join(source_images_path, '*.jpg'))
    for mp3_path in mp3_paths:
        random_image_path = random.choice(background_image_paths)
        create_video_with_image(image_path=str(random_image_path),
                                audio_path=str(mp3_path),
                                output_path=f'{output_video_folder_path}/{os.path.basename(mp3_path)[:-4]}.mp4',
                                text=video_caption_text)


# parallelise render
# separaterd shorts image paths and plain videos paths
# add ui
# refactor (create another file file_utils) and maybe file for ffmpeg wrapper
if __name__ == '__main__':
    image_path = 'photo.jpg'
    audio_path = 'sample_with_pauses.mp3'
    output_path = 'ouput.mp4'
    video_caption_text = 'Min bir hikmətli söz'

    start_time = time.time()
    create_videos_with_image(Path('./source'),
                             Path(r'E:\ПапаРелигия\assets\photo'),
                             Path('./out'),
                             video_caption_text)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Время исполнения: {elapsed_time:.2f} секунд')
