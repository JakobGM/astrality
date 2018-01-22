from conky import (
    compile_conky_templates,
    find_placeholders,
    generate_replacements,
    generate_replacer,
)


def test_invocation_of_compile_conky_templates(conf):
    compile_conky_templates(conf, 'night')

def test_generation_of_replacements(conf):
    replacements = generate_replacements(conf, 'night')
    assert replacements == {
        '${solarity:colors:1}': 'CACCFD',
        '${solarity:fonts:1}': 'FuraCode Nerd Font',
    }

def test_use_of_replacer(conf):
    replacements = generate_replacements(conf, 'night')
    replace = generate_replacer(replacements, 'night', conf)
    assert replace('${solarity:colors:1}') == 'CACCFD'

def test_find_placeholders():
    template = """
    Some text and then a valid template tag ${solarity:wallpaper:theme}
    some more text, and then another valid template tag
    ${solarity:conky:modules} even more text, and then several invalid tags
    stuff ${sollarity:conky:stuff} ${:conky:test} ${::} ${solarity::}
    ${solarity:somthing:} {solarity:wrong:tag} and then one last valid tag at
    the beginning of a line:
    ${solarity:valid:tag}
    """
    placeholders = find_placeholders(template)
    assert placeholders == set((
        '${solarity:wallpaper:theme}',
        '${solarity:conky:modules}',
        '${solarity:valid:tag}',
    ))


