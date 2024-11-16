import subprocess

import numpy as np
from scipy.io.wavfile import write, read
from tqdm import tqdm


def convert_audiofile(input_path: str, output_path: str):
    """
    Convert audiofile from one format to another.
    Formats will be specified by extension of both paths.

    :param input_path: path to input audiofile (extension included)
    :param output_path: path to output audiofile (extension also included)
    """
    command = ['ffmpeg', '-hide_banner', '-y', '-i', input_path, output_path]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        raise


def detect_silence(path: str, time: float):
    """
    This function is a python wrapper to run the ffmpeg command in python and extract the desired output

    path= Audio file path
    time = silence time threshold

    returns = list of tuples with start and end point of silences
    """
    command = "ffmpeg -i " + path + " -af silencedetect=n=-35dB:d=" + str(time) + " -f null -"
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


# todo разобраться, почему зависает на секунд 10 во время многопоточного выполнения
def remove_silence(path: str, sil, keep_sil, out_path: str):
    """
    Removes silence from the audio.

    Input:
    path = Input audio file path
    sil = List of silence time slots that needs to be removed
    keep_sil = Time to keep as allowed silence after removing silence
    out_path = Output path of audio file

    returns:
    Non - silent patches and save the new audio in out path
    """
    rate, aud = read(path)
    if not sil:
        write(out_path, rate, aud)
        return None

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
    for i in tqdm(non_sil, desc='Remove silence parts...'):
        ans = ans + ad[int(i[0] * rate):int(i[1] * rate)]
    write(out_path, rate, np.array(ans))
    return non_sil


def to_unix_path(path: str) -> str:
    unix_path = path.replace('\\', '/')
    return unix_path


# add font
def burn_subtitles_into_video(video_path: str, subtitles_path: str, output_path: str):
    command = f'ffmpeg -y -i {video_path} -vf \"subtitles=\'{to_unix_path(subtitles_path)}\':force_style=\'Alignment=2,MarginV=50\'" -c:a copy {output_path}'

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
