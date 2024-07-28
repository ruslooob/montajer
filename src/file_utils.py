import os
import re


def remove_files(files_for_remove: list[str]):
    """
    Deletes all files according to the list of paths to these files
    :param files_for_remove: list of paths
    """
    for file_path in files_for_remove:
        os.remove(file_path)


def fix_filenames(folder: str):
    """
    Fixes filenames in the specified folder by replacing spaces with underscores
    and removing special characters except dots in file extensions.
    """
    if not folder.endswith('/'):
        folder = folder + '/'

    for filename in os.listdir(folder):
        name, extension = os.path.splitext(filename)
        fixed_name = name.replace(' ', '_')
        fixed_name = re.sub(r'[^\w\s]', '', fixed_name)
        fixed_filename = fixed_name + extension
        os.rename(os.path.join(folder, filename), os.path.join(folder, fixed_filename))


def find_first_mp3_file(files: list[str]):
    for file in files:
        if file.endswith('.mp3'):
            return file
