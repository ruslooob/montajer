Программа автоматически делает монтаж видео.

- Создание видео со статичным изображением на заднем фоне
- Обработка аудиодорожки, удаление длительных пауз
- Добавление текста на видео
- Поддержка разных разрешений 1920x1080 (стандартное) и 1080x1920 (short)

### Примеры использования:
Помощь:
* Справка: `python montajer.py --help`
* Справка по конкретной команде: `python montajer <command_name> --help`

Использование:
* Удаление пауз в аудиотреке: `python .\montajer.py cleanup-audio --audio-path <path_to_audiofile>`
* Создание видео с простым фоном: `python .\montajer.py create-videos --source-audio-folder-path .\examples\ --source-images-folder-path 'E:\TestFolder\assets\photo' --output-video-folder-path .\out\ --video-caption-text 'Hello world'`

Запуск с помощью файла настроек:
Пример файла:
```json
{
    "task-type": "cleanup-audio",
    "settings": {
        "audio_path": "./examples/123.mp3"
    }
}
```

Запуск: `python ./montajer.py montage --config <path_to_setings_file>`
___
Пример: 
```json
{
    "task-type": "create-videos",
    "settings": {
        "source-audio-folder-path": "./examples",
        "source-images-folder-path": "E:\\TestFolder\\assets\\photo",
        "output-video-folder-path": "./out",
        "video-caption-text": "Hello World"
    }
}
```
Запуск: `python ./montajer.py montage --config <path_to_setings_file>`


### Настройка Environment:
* скачать ffmpeg, добавить в path
* скачать imagemagick, добавить в переменную среды IMAGEMAGICK_BINARY

TODO:
- Settings file support
- Subtitles generation support
- More configurations for video generation (fonts, images, captions)
- Multithreading support
- Transitions, video concatenation
- GPU Acceleration
- cli support
- ui
- Скрипт для локальной установки с нуля (ffmpeg + imagemagick)

Другое
Удаление шума из аудио взял отсюда - https://github.com/Patil-Onkar/Remove-silence-from-an-audio
