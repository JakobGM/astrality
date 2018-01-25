from compiler import (
    find_placeholders,
    generate_replacements,
    generate_replacer,
)

def test_generation_of_replacements(conf):
    replacements = generate_replacements(conf, 'night')
    assert replacements == {
        '${astrality:colors:1}': 'CACCFD',
        '${astrality:fonts:1}': 'FuraCode Nerd Font',
    }

def test_use_of_replacer(conf):
    replacements = generate_replacements(conf, 'night')
    replace = generate_replacer(replacements, 'night', conf)
    assert replace('${astrality:colors:1}') == 'CACCFD'

def test_find_placeholders():
    template = """
    Some text and then a valid template tag ${astrality:wallpaper:theme}
    some more text, and then another valid template tag
    ${astrality:conky:modules} even more text, and then several invalid tags
    stuff ${astrallity:conky:stuff} ${:conky:test} ${::} ${astrality::}
    ${astrality:somthing:} {astrality:wrong:tag} and then one last valid tag at
    the beginning of a line:
    ${astrality:valid:tag}
    """
    placeholders = find_placeholders(template)
    assert placeholders == set((
        '${astrality:wallpaper:theme}',
        '${astrality:conky:modules}',
        '${astrality:valid:tag}',
    ))
