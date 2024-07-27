from pathlib import Path

import typer

from src.montajer import create_videos_with_image, clean_audiotrack

app = typer.Typer()


@app.command(name="create-videos")
def create_videos(source_mp3_folder_path: Path,
                  source_images_folder_path: Path,
                  output_video_folder_path: Path,
                  video_caption_text: str):
    create_videos_with_image(source_mp3_folder_path,
                             source_images_folder_path,
                             output_video_folder_path,
                             video_caption_text)


@app.command(name='cleanup-audio')
def cleanup_audio(audio_path: Path):
    clean_audiotrack(str(audio_path))


# Add ui.
# Хочу, чтобы можно было запускать через консоль и выбирать опции.
# Обработать только аудио, создать видео, склеивать одно видео с другим
if __name__ == '__main__':
    # video_caption_text = 'Min bir hikmətli söz'
    #
    # start_time = time.time()
    # create_videos_with_image(source_mp3_folder_path=Path('../examples'),
    #                          source_images_folder_path=Path(r'E:\ПапаРелигия\assets\photo\short'),
    #                          output_video_folder_path=Path('../out'),
    #                          video_caption_text=video_caption_text)
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f'Execution time: {elapsed_time:.2f} seconds')
    app()
