import json
import time
from pathlib import Path

import typer

from src.montajer_utils import create_videos_with_image, clean_audiotrack

app = typer.Typer()


@app.command(name='cleanup-audio')
def cleanup_audio(audio_path: Path = typer.Option(), output_path: Path = typer.Option(None)):
    if output_path:
        clean_audiotrack(audio_path, output_path)
    else:
        clean_audiotrack(audio_path)


@app.command(name="create-videos")
def create_videos(source_audio_folder_path: Path = typer.Option(),
                  source_images_folder_path: Path = typer.Option(),
                  output_video_folder_path: Path = typer.Option(),
                  video_caption_text: str = typer.Option(),
                  threads: int = typer.Option(1)):
    start_time = time.time()
    create_videos_with_image(source_audio_folder_path,
                             source_images_folder_path,
                             output_video_folder_path,
                             video_caption_text,
                             threads)
    print(f"Общее время монтажа: {time.time() - start_time:.2f}")


@app.command(name="montage")
def montage(config: Path = typer.Option()):
    """
    Производит монтаж в соответствии с заданными настройками.
    :param config Путь json-файла с конфигурацией
    """
    with open(config, 'r', encoding='utf-8') as file:
        config = json.load(file)
        arguments = config['arguments']
        task_type = config['task-type']
        if task_type == 'create-videos':
            create_videos(arguments['source-audio-folder-path'],
                          arguments['source-images-folder-path'],
                          arguments['output-video-folder-path'],
                          arguments['video-caption-text'],
                          config['threads'])
        elif task_type == 'cleanup-audio':
            cleanup_audio(arguments['audio-path'])
        else:
            raise ValueError("Неверный task-type")


# Add ui.
# Хочу, чтобы можно было запускать через консоль и выбирать опции.
# Обработать только аудио, создать видео, склеивать одно видео с другим
if __name__ == '__main__':
    app()
