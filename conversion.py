import click
import pydub
from pydub.utils import mediainfo
import os
import datetime


@click.command()
@click.argument('directory')
@click.option('--force', default=False)
def convert(directory, force):
    dirs = [os.path.join(directory, d)
            for d in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, d))]

    files_to_convert = []
    for d in dirs:
        for f in os.listdir(d):
            if os.path.isfile(os.path.join(d, f)) and '_converted' not in f:
                files_to_convert.append((d, f))

    for song in files_to_convert:
        if force or not converted_version_exists(song[0], song[1]):
            try:
                valid_song = check_tags(song[0], song[1])
                process_audio(valid_song)

            except Exception as e:
                print('Problem:')
                print(e)
                continue


def converted_version_exists(directory, song):
    root_name = os.path.splitext(song)[0]
    if root_name + '_converted.mp3' in [f for f in os.listdir(directory)]:
        return True
    return False


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


def check_tags(directory, song):
    file_format = os.path.splitext(song)[-1].replace('.', '')
    root_name = os.path.splitext(song)[0]
    seg = pydub.AudioSegment.from_file(os.path.join(directory, song), file_format)
    song_meta = mediainfo(os.path.join(directory, song)).get('TAG')
    if song_meta is None:
        song_meta = {}

    print('Load', os.path.join(directory, song))
    song_meta['comment'] = 'Upload date: ' + datetime.datetime.now().isoformat()

    song_is_valid = False
    changeable_keys = ['artist', 'album', 'title']
    for k in changeable_keys:
        song_meta[k] = song_meta.get(k, '').strip()

    while not song_is_valid:
        for k in changeable_keys:
            print(k.title(), ':', song_meta[k].strip())
        print('-----------')
        needs_change = input('Change tags ? (y/n) ')
        if needs_change == 'y':
            k_to_change = input("Which field ? (artist/album/title): ")
            if k_to_change in changeable_keys:
                song_meta[k_to_change] = input('New value for {} field: '.format(k_to_change)).strip()
        elif needs_change == 'n':
            song_is_valid = True

    return {'output_file': os.path.join(directory, root_name + '_converted.mp3'),
            'tags': song_meta,
            'segment': seg}


def process_audio(valid_song):
    print('Normalize')
    print(valid_song)
    norm_seg = match_target_amplitude(valid_song['segment'], -89)
    print('Convert')
    norm_seg.export(valid_song['output_file'],
                    format="mp3",
                    tags=valid_song['tags'],
                    bitrate="192k")
    print('Exported {}'.format(valid_song['output_file']))

if __name__ == '__main__':
    convert()