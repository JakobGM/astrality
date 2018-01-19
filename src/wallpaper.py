import os

from config import Config


def update_wallpaper(config: Config, period: str) -> None:
    wallpaper_path = config['wallpaper-paths'][period]

    print('Setting new wallpaper: ' + wallpaper_path)
    os.system('feh --bg-scale ' + wallpaper_path)

def exit_feh() -> None:
    this_file = os.path.realpath(__file__)
    parent_dir = os.path.join(*this_file.split('/')[:-1])
    os.system('feh --bg-scale /' + parent_dir + '/solid_black_background.jpeg')
