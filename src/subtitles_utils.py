from collections import namedtuple
from enum import Enum

from faster_whisper import WhisperModel

WordTimestamp = namedtuple('WordTimestamp', ['start', 'end', 'word'])


def generate_word_timestamps(audio_path: str) -> list[WordTimestamp]:
    """
    Generate subtitles for the given audio file using faster-whisper.
    :param audio_path: Path to the audio file.
    :return: Subtitles as a string.
    """
    model = WhisperModel("base", device="cuda", compute_type="float16")
    segments, info = model.transcribe(audio_path, language='az', word_timestamps=True)

    word_timestamps = []
    for segment in segments:
        for word in segment.words:
            word_timestamps.append(WordTimestamp(word.start, word.end, word.word.strip()))
    return word_timestamps


# todo сделать не WordTimestamps, а SubtitleEntry. Поля будут одинаковыми, но это не будет вводить в заблуждене
#  неверной терминологией
def generate_subtitles(word_timestamps: list[WordTimestamp],
                       max_line_width=25,
                       max_line_count=2) -> list[WordTimestamp]:
    subtitles = []
    curr_entry = word_timestamps[0]

    for i in range(1, len(word_timestamps)):
        word_timestamp = word_timestamps[i]

        last_line = curr_entry.word.split('\n')[-1]
        if len(last_line + " " + word_timestamp.word) <= max_line_width:
            curr_entry = WordTimestamp(curr_entry.start, word_timestamp.end,
                                       curr_entry.word + ' ' + word_timestamp.word)
        else:
            line_count = curr_entry.word.count('\n') + 1
            if line_count < max_line_count:
                curr_entry = WordTimestamp(curr_entry.start, word_timestamp.end,
                                           curr_entry.word + "\n" + word_timestamp.word)
            else:
                subtitles.append(curr_entry)
                curr_entry = word_timestamp

    subtitles.append(curr_entry)

    return subtitles


def write_srt_file(output_path: str, word_timestamps: list[WordTimestamp]):
    def format_time(seconds: float) -> str:
        millis = int((seconds - int(seconds)) * 1000)
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, word_timestamp in enumerate(word_timestamps):
            srt_entry = f'{i + 1}\n{format_time(word_timestamp.start)} --> {format_time(word_timestamp.end)}\n{word_timestamp.word}\n\n'
            f.write(srt_entry)


class SubtitleFormat(Enum):
    SRT = 1,


def write_subtitle_file(audio_path: str, output_path: str, subtitle_format: SubtitleFormat):
    """
    Process an audio file to generate subtitles.
    :param audio_path: Path to the audio file.
    :param output_path: Path to the output subtitle file
    :param subtitle_format: Enum, Output subtitle file format
    """

    word_timestamps = generate_word_timestamps(audio_path)

    subtitles = generate_subtitles(word_timestamps)

    if subtitle_format == SubtitleFormat.SRT:
        write_srt_file(output_path, subtitles)
    else:
        raise ValueError(f'unknown subtitle format')


if __name__ == '__main__':
    write_subtitle_file('../examples/audio/123.mp3', '../examples/audio/123.srt', SubtitleFormat.SRT)
