import json
import time

import typer

from src.montajer_utils import create_videos_with_image, clean_audiotrack
from src.subtitles_utils import SubtitlesConfig

app = typer.Typer()


@app.command(name='cleanup-audio')
def cleanup_audio(audio_path: str = typer.Option(), output_path: str = typer.Option(None)):
    if output_path:
        clean_audiotrack(audio_path, output_path)
    else:
        clean_audiotrack(audio_path)

# todo убрать _fixed
# сдлать конвртацию из m4a в mp3
@app.command(name="create-videos")
def create_videos(source_audio_folder_path: str = typer.Option(),
                  source_images_folder_path: str = typer.Option(),
                  output_video_folder_path: str = typer.Option(),
                  video_caption_text: str = typer.Option(),
                  subtitles_enabled: bool = typer.Option(False),
                  subtitles_max_line_width: int = typer.Option(),
                  subtitles_max_line_count: int = typer.Option(),
                  subtitles_model: str = typer.Option(),
                  subtitles_language: str = typer.Option(),
                  threads: int = typer.Option(1)):
    start_time = time.time()
    create_videos_with_image(source_audio_folder_path,
                             source_images_folder_path,
                             output_video_folder_path,
                             video_caption_text,
                             subtitles_enabled,
                             SubtitlesConfig(
                                 subtitles_max_line_width,
                                 subtitles_max_line_count,
                                 subtitles_model,
                                 subtitles_language
                             ) if subtitles_enabled else None,
                             threads)
    print(f"Общее время монтажа: {time.time() - start_time:.2f}")


@app.command(name="montage")
def montage(config: str = typer.Option()):
    """
    Производит монтаж в соответствии с заданными настройками.
    :param config Путь json-файла с конфигурацией
    """

    with open(config, 'r', encoding='utf-8') as file:
        config = json.load(file)
        task_type = config['task-type']
        if task_type == 'create-videos':
            create_videos(source_audio_folder_path=config['source-audio-folder-path'],
                          source_images_folder_path=config['source-images-folder-path'],
                          output_video_folder_path=config['output-video-folder-path'],
                          video_caption_text=config['video-caption-text'],
                          subtitles_enabled=config['subtitles-enabled'],
                          subtitles_max_line_width=config['subtitles-max-line-width'],
                          subtitles_max_line_count=config['subtitles-max-line-count'],
                          subtitles_model=config['subtitles-model'],
                          subtitles_language=config['subtitles-language'],
                          threads=config['threads'])
        elif task_type == 'cleanup-audio':
            cleanup_audio(config['audio-path'])
        else:
            raise ValueError("Неверный task-type")


# TODO
# Add ui.
# Хочу, чтобы можно было запускать через консоль и выбирать опции.
# Обработать только аудио, создать видео, склеивать одно видео с другим
# команды для отдельного создания субтитров (из видео и из аудио)
if __name__ == '__main__':
    app()
