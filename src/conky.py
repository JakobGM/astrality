import os

from config import Config


def update_conky(
    config: Config,
    daytime: str,
) -> None:
    if daytime == 'night':
        os.system('sed -i "s/282828/CBCDFF/g" $XDG_CONFIG_HOME/conky/*.conf')
    else:
        os.system('sed -i "s/CBCDFF/282828/g" $XDG_CONFIG_HOME/conky/*.conf')

