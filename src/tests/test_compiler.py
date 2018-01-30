from pathlib import Path

from compiler import (
    find_placeholders,
    generate_replacements,
    generate_replacer,
)

def test_generation_of_replacements(conf):
    conf['colors'] = {'1': 'CACCFD'}
    replacements = generate_replacements(
        Path(__file__).parents[2] / 'conky_themes' / 'time-1920x1080' / 'template.conf',
        conf,
    )
    assert replacements == {
        '${ast:colors:1}': 'CACCFD',
        '${ast:fonts:1}': 'FuraCode Nerd Font',
    }

def test_use_of_replacer(conf):
    conf['colors'] = {'1': 'CACCFD'}
    replacements = generate_replacements(
        Path(__file__).parents[2] / 'conky_themes' / 'time-1920x1080' / 'template.conf',
        conf,
    )
    replace = generate_replacer(replacements)
    assert replace('${ast:colors:1}') == 'CACCFD'

def test_find_placeholders():
    template = """
    Some text and then a valid template tag ${ast:wallpaper:theme}
    some more text, and then another valid template tag
    ${ast:conky:modules} even more text, and then several invalid tags
    stuff ${astrality:conky:stuff} ${:conky:test} ${::} ${ast::}
    ${ast:somthing:} {ast:wrong:tag} and then one last valid tag at
    the beginning of a line:
    ${ast:valid:tag}
    """
    placeholders = find_placeholders(template)
    assert placeholders == set((
        '${ast:wallpaper:theme}',
        '${ast:conky:modules}',
        '${ast:valid:tag}',
    ))
