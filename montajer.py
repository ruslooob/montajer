import json
from pathlib import Path

import typer

from src.montajer_utils import create_videos_with_image, clean_audiotrack

app = typer.Typer()


@app.command(name='cleanup-audio')
def cleanup_audio(audio_path: Path = typer.Option(None)):
    clean_audiotrack(audio_path)


# todo не привязываться к расширению аудио
@app.command(name="create-videos")
def create_videos(source_audio_folder_path: Path = typer.Option(None),
                  source_images_folder_path: Path = typer.Option(None),
                  output_video_folder_path: Path = typer.Option(None),
                  video_caption_text: str = typer.Option(None)):
    create_videos_with_image(source_audio_folder_path,
                             source_images_folder_path,
                             output_video_folder_path,
                             video_caption_text)


@app.command(name="montage")
def montage(config: Path = typer.Option(None)):
    """
    Производит монтаж в соотоветвтии с заданными настройками.
    :param config Путь json-файла с конфигурацией
    """
    with open(config, 'r') as file:
        config = json.load(file)
        settings = config['settings']

        task_type = config['task-type']
        if task_type == 'create-videos':
            create_videos(settings['source-mp3-folder-path'],
                          settings['source-images-folder-path'],
                          settings['output-video-folder-path'],
                          settings['video-caption-text'])
        elif task_type == 'cleanup-audio':
            cleanup_audio(settings['audio-path'])
        else:
            raise ValueError("Неверный task-type")


# Add ui.
# Хочу, чтобы можно было запускать через консоль и выбирать опции.
# Обработать только аудио, создать видео, склеивать одно видео с другим
if __name__ == '__main__':
    app()
