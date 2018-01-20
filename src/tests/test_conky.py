from conky import generate_replacements, generate_replacer, compile_conky_templates

def test_invocation_of_compile_conky_templates(conf):
    compile_conky_templates(conf, 'night')

def test_generation_of_replacements(conf):
    replacements = generate_replacements(conf, 'night')
    assert replacements == {
        '${solarity:colors:primary}': 'CACCFD',
        '${solarity:colors:secondary}': '3F72E8',
    }

def test_use_of_replacer(conf):
    replacements = generate_replacements(conf, 'night')
    replace = generate_replacer(replacements)
    assert replace('${solarity:colors:primary}') == 'CACCFD'
