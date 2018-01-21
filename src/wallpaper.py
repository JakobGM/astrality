from glob import glob
import os
import subprocess

from config import Config


def update_wallpaper(config: Config, period: str) -> None:
    wallpaper_path = config['wallpaper_paths'][period]
    wallpaper_path = glob(wallpaper_path + '.*')[0]

    print('Setting new wallpaper: ' + wallpaper_path)
    subprocess.Popen([
        'feh',
        config['wallpaper'].get('feh-option', '--bg-scale'),
        wallpaper_path,
    ])

def exit_feh(config) -> None:
    this_file = os.path.realpath(__file__)
    parent_dir = os.path.join(*this_file.split('/')[:-1])
    feh_process = subprocess.Popen([
        'feh',
        config['wallpaper'].get('feh-option', '--bg-scale'),
        '/' + parent_dir + '/solid_black_background.jpeg',
    ])
    try:
        exit_code = feh_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print('feh is using unusually long time to set the background image.')
    finally:
        if exit_code != 0:
            print(f'feh exited with error code: {exit_code}.')
