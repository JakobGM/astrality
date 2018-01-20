from glob import glob
import os
import subprocess

from config import Config


def update_wallpaper(config: Config, period: str) -> None:
    wallpaper_path = config['wallpaper-paths'][period]
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
    subprocess.Popen([
        'feh',
        config['wallpaper'].get('feh-option', '--bg-scale'),
        '/' + parent_dir + '/solid_black_background.jpeg',
    ])
