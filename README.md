# Astrality - A dynamic configuration file manager <br/> [![Build Status](https://travis-ci.org/JakobGM/astrality.svg?branch=master)](https://travis-ci.org/JakobGM/astrality) [![Coverage Status](https://coveralls.io/repos/github/JakobGM/astrality/badge.svg?branch=master)](https://coveralls.io/github/JakobGM/astrality?branch=master)

<img align="left" src="astrality/doc/astrality_logo.png">

## What does it do?
Astrality is a tool for managing configuration files and scheduling tasks related to those files.

You can create templates for your configuration files, and Astrality will replace placeholders within those templates with `context` values defined in a central configuration file. Furthermore, you can dynamically manipulate that `context` at predefined times and events. 

<br/>

**Possible use cases are:**

* Insert environment variables (e.g. `$USER`) and command substitutions (e.g. `$(xrandr | grep -cw connected)`) into config files that do not support them.
* Create a single source of truth for configuration options. Change your preferred font type or color scheme, and instantly see that change be applied across several different applications.
* Change your desktop wallpaper when your specific location (given by latitude and longitude) experiences dawn, noon, sunset, and dusk. It adapts to the length of day through the year. Make your [Conky modules](https://github.com/brndnmtthws/conky) change font color accordingly.
* And much more...  An example configuration with several examples is included.

The configuration format uses the flexible [YAML](http://docs.ansible.com/ansible/latest/YAMLSyntax.html#yaml-basics) format, and the template language uses the [Jinja2 syntax](http://jinja.pocoo.org/docs/2.10/), which is easy to get started with, but allows complex templating for those inclined.

It is relatively easy to create `modules` to your own liking. Pull requests with new themes, conky modules, and improvements are very welcome.

## How to install

### System requirements
Astrality requires the following system packages: [`conky`](https://wiki.archlinux.org/index.php/Conky),  [`feh`](https://wiki.archlinux.org/index.php/feh), and `python 3.6`. An example installation on ArchLinux would be:

```bash
sudo pacman -Syu conky feh python
```

The default configuration uses the [Nerd Font](https://github.com/ryanoasis/nerd-fonts) "FuraCode Nerd Font". Install it if you don't change the font in your configuration. On ArchLinux, it can be installed with the `nerd-fonts-complete` AUR package:

```bash
yaourt -S nerd-fonts-complete
```

### Python requirements

Create a new virtualenv for python 3.6 (or use your system python 3.6 if you prefer). Install the following requirements:

```bash
pip3 install astral
git clone https://github.com/jakobgm/astrality /path/to/astrality
```

The script can be run as a background job in the following way:

```bash
python3.6 /path/to/astrality/src/main.py &
```

Your wallpaper should now be automatically changed during the different times of day.

### Example installation using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/):
Here is how I would install this tool using virtualenvwrapper

```bash
git clone https://github.com/jakobgm/astrality $XDG_CONFIG_HOME
mkvirtualenv -p python3.6 -a $XDG_CONFIG_HOME/astrality astrality
pip install astral
deactivate
```

### Example initialization using the [i3 tiling window manager](https://github.com/i3/i3)
Add the following line to `$XDG_CONFIG_HOME/i3/config`:

```config
exec --no-startup-id "/path/to/python/with/installed/dependencies/python /path/to/astrality/src/main.py &"
```

Or more specifically, if you have used the virtualenvwrapper method of installing astrality:

```config
exec --no-startup-id "$WORKON_HOME/astrality/bin/python $XDG_CONFIG_HOME/astrality/src/main.py &"
```

## Configuration
The configuration directory for astrality is determined in the following way:

* If `$ASTRALITY_CONFIG_HOME` is set, use that folder as the configuration directory, else...
* If `$XDG_CONFIG_HOME` is set, use `$XDG_CONFIG_HOME/astrality`, else...
* Use `~/.config/astrality`.

The configuration file for astrality should be placed at the root of the astrality configuration directory and an example configuration can be found [here](https://github.com/JakobGM/astrality/blob/master/astrality.conf.example).

You can also copy the example configuration file from this repository:

```bash
cp /path/to/astrality/astrality.conf.example $XDG_CONFIG_HOME/astrality/astrality.conf
```

Edit the configuration file in order to add your current location, given by your GPS coordinates (longitude, latitude, and elevation). These coordinates can be obtained from [this website](https://www.latlong.net/).

The configuration file is parsed by the python module `[configparser](https://docs.python.org/3/library/configparser.html)`, and supports references to other configuration variables when setting new ones. Example:

```dosini
[filesystem]
username =  jakobgm
home-dir = /home/${username}

[configs]
vimrc = ${filesystem:home-dir}/.vimrc
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
Say you would want to create a new wallpaper theme called `nature`. First create a new subdirectory in `$XDG_CONFIG_HOME/astrality/wallpaper_themes` named `nature`:

```
mkdir -p $XDG_CONFIG_HOME/astrality/wallpaper_themes/nature
```

Then place pictures [supported by feh](http://search.cpan.org/~kryde/Image-Base-Imlib2-1/lib/Image/Base/Imlib2.pm#DESCRIPTION) in the newly created directory. You **have** to use the following filenames:

```
sunrise.*
morning.*
afternoon.*
sunset.*
night.*
```

Where the `*` suffixes can be any combination of file types supported by feh.

The images are not required to be different, in case if you do not have enough fitting wallpapers to choose from. You can use identical copies for some or all of the time periods, or even better, create a symbolic links. For example:

```bash
# Let sunrise be the same picture as sunset
ln -s sunrise.jpg sunrise.jpg
```

Then you have to add the following line to the `[Appearance]` section of `astrality.conf`:

```dosini
[Appearance]
...
WallpaperTheme = nature
...
```

Restart the astrality process in order to see the change of the wallpaper theme.

Pull requests containing new themes are very welcome!

## Inspirations for themes
Themes have been made by the help of several posts on the [/r/unixporn](https://reddit.com/r/unixporn) subreddit. Here are some of them:

* Default: Still on the lookout for where I got this theme originally
* Tower: Reddit user [/u/saors](https://reddit.com/u/soars): [/r/unixporn post](https://www.reddit.com/r/Rainmeter/comments/49phkc/firewatch_chrono_first_theme_includes_parallax/?st=jcktppsn&sh=792fe302)
* Tower: Reddit user [/u/TheFawxyOne](https://reddit.com/u/soars): [/r/unixporn post](https://www.reddit.com/r/Rainmeter/comments/49fpwz/ocupdate_firewatch_parallax_theme_v150_read/?st=jcktryl8&sh=4022418b)

In addition, the astrality logo is a modified version of a logo designed by [miscellaneous](https://www.shareicon.net/author/miscellaneous) from Flaticon.
