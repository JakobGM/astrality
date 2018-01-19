def test_config_directory_name(conf):
    assert conf['config-directory'][-9:] == '/solarity'


def test_name_of_config_file(conf):
    assert conf['config-file'][-14:] == '/solarity.conf'


def test_conky_module_paths(conf, conf_path):
    conky_module_paths = conf['conky-module-paths']
    assert conky_module_paths == {
        'performance': conf_path + '/conky_themes/performance',
        'time': conf_path + '/conky_themes/time',
    }

def test_loation(conf):
    location = conf['location']['astral']
    assert str(location) == 'CityNotImportant/RegionIsNotImportantEither, tz=Europe/Oslo, lat=63.45, lon=10.42'


def test_refresh_period(conf):
    assert conf['behaviour']['refresh-period'] == '60'


def test_wallpaper_theme(conf):
    assert conf['wallpaper']['theme'] == 'default'


def test_wallpaper_paths(conf, conf_path):
    base_path = conf_path + '/wallpaper_themes/default/'
    assert conf['wallpaper-paths'] == {
        'sunrise': base_path + 'sunrise.jpg',
        'morning': base_path + 'morning.jpg',
        'afternoon': base_path + 'afternoon.jpg',
        'sunset': base_path + 'sunset.jpg',
        'night': base_path + 'night.jpg',
    }

def test_that_colors_are_correctly_imported_based_on_wallpaper_theme(conf):
    assert conf['colors'] == {
        'primary': {
            'afternoon': '#FC6F42',
            'morning': '#5BA276',
            'night': '#CACCFD',
            'sunrise': '#FC6F42',
            'sunset': '#FEE676',
        },
        'secondary': {
            'afternoon': '#DB4E38',
            'morning': '#76B087',
            'night': '#3F72E8',
            'sunrise': '#DB4E38',
            'sunset': '#9B3A1A',
        }
    }
