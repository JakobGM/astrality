# Solarity - A wallpaper theme manager which uses the suns position in the sky

## What does it do?
Solarity is a Linux tool which automatically changes the wallpaper when your specific location (given by latitude and longitude) experiences dawn, noon, sunset, and dusk. It adapts to the length of day through the year.

Conky modules are also supported, where the font color can change during the different times of the day.

It is relatively easy to add new themes to your own liking. Pull requests with new themes, conky modules, and improvements are very welcome.

## How to install

### System requirements
Solarity requires the following system packages: [`conky`](https://wiki.archlinux.org/index.php/Conky),  [`feh`](https://wiki.archlinux.org/index.php/feh), `python 3.6`, and `sed`. An example installation on ArchLinux would be:

```bash
sudo pacman -Syu conky feh python sed 
```

The default configuration uses the [Nerd Font](https://github.com/ryanoasis/nerd-fonts) "FuraCode Nerd Font". Install it if you don't change the font in your configuration. On ArchLinux, it can be installed with the `nerd-fonts-complete` AUR package:

```bash
yaourt -S nerd-fonts-complete
```

### Python requirements

Create a new virtualenv for python (or use your system python if you prefer). Install the following requirements:

```bash
pip install astral tzlocal
git clone https://github.com/jakobgm/solarity /path/to/solarity
```

The script can be run as a background job in the following way:

```bash
python /path/to/solarity/src/main.py &
```

Your wallpaper should now be automatically changed during the different times of day.

### Example installation using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/):
Here is how I would install this tool using virtualenvwrapper

```bash
git clone https://github.com/jakobgm/solarity $XDG_CONFIG_HOME
mkvirtualenv -p python3.6 -a $XDG_CONFIG_HOME/solarity solarity
pip install astral tzlocal
deactivate
```

### Example initialization using the [i3 tiling window manager](https://github.com/i3/i3)
Add the following line to `$XDG_CONFIG_HOME/i3/config`:

```config
exec --no-startup-id "/path/to/python/with/installed/dependencies /path/to/solarity/src/main.py &"
```

Or more specifically, if you have used the virtualenvwrapper method of installing solarity:

```config
exec --no-startup-id "$WORKON_HOME/solarity/bin/python $XDG_CONFIG_HOME/solarity/src/main.py &"
```

## Configuration
The configuration file for solarity should be placed in `$XDG_CONFIG_HOME/solarity/solarity.conf` and an example configuration can be found [here](https://github.com/JakobGM/solarity/blob/master/solarity.conf.example).

You can also copy the example configuration file from this repository:

```bash
cp /path/to/solarity/solarity.conf.example $XDG_CONFIG_HOME/solarity/solarity.conf
```

Edit the configuration file in order to add your current location, given by your GPS coordinates (longitude, latitude, and elevation). These coordinates can be obtained from [this website](https://www.latlong.net/).

The configuration file is parsed by the python module `[configparser](https://docs.python.org/3/library/configparser.html)`, and supports references to other configuration variables when setting new ones. Example:

```dosini
[filesystem]
username =  jakobgm
home-dir = /home/${username}

[configs]
vimrc = $[filesystem:home-dir]/.vimrc
```

More information about value interpolation can be found [here](https://docs.python.org/3/library/configparser.html#interpolation-of-values).

### Compton
If you are using the [compton](https://github.com/chjj/compton) compositor, you should disable any shadows and dims which could be applied to the conky wallpaper modules. Here is an example configuration from `$XDG_CONFIG_HOME/compton/compton.conf`:

```conf
inactive-dim = 0.1;
shadow = true;
shadow-exclude = [
    "! name~=''",
    "class_g = 'Conky'"
    ]
mark-ovredir-focused = true;
```

## How to add new wallpaper theme
Say you would want to create a new wallpaper theme called `nature`. First create a new subdirectory in `$XDG_CONFIG_HOME/wallpaper_themes` named `nature`:

```
mkdir -p $XDG_CONFIG_HOME/solarity/wallpaper_themes/nature
```

Then place pictures [supported by feh](http://search.cpan.org/~kryde/Image-Base-Imlib2-1/lib/Image/Base/Imlib2.pm#DESCRIPTION) in the newly created directory. You **have** to use the following filenames:

```
sunrise.format
morning.format
afternoon.format
sunset.format
night.format
```

Where the `format` suffixes would be any combination of `png`, `jpeg`, `jpg`, `tiff`, `pnm`, and `bmp`.

The images are not required to be different, in case if you do not have enough fitting wallpapers to choose from. You can use identical copies for some or all of the time periods, or even better, create a symbolic links. For example:

```bash
# Let sunrise be the same picture as sunset
ln -s sunrise.jpg sunrise.jpg
```

Then you have to add the following line to the `[Appearance]` section of `solarity.conf`:

```dosini
[Appearance]
...
WallpaperTheme = nature
...
```

Restart the solarity process in order to see the change of the wallpaper theme.

Pull requests containing new themes are very welcome!

## Inspirations for themes
Themes have been made by the help of several posts on the [/r/unixporn](https://reddit.com/r/unixporn) subreddit. Here are some of them:

* Default: Still on the lookout for where I got this theme originally
* Tower: Reddit user [/u/saors](https://reddit.com/u/soars): [/r/unixporn post](https://www.reddit.com/r/Rainmeter/comments/49phkc/firewatch_chrono_first_theme_includes_parallax/?st=jcktppsn&sh=792fe302)
* Tower: Reddit user [/u/TheFawxyOne](https://reddit.com/u/soars): [/r/unixporn post](https://www.reddit.com/r/Rainmeter/comments/49fpwz/ocupdate_firewatch_parallax_theme_v150_read/?st=jcktryl8&sh=4022418b)
