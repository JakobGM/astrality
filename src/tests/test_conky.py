from conky import generate_replacements, generate_replacer, update_conky

def test_invocation_of_update_conky(conf):
    update_conky(conf, 'night')

def test_generation_of_replacements(conf):
    replacements = generate_replacements(conf, 'night')
    assert replacements == {
        '${solarity:color:primary}': '#CACCFD',
        '${solarity:color:secondary}': '#3F72E8',
    }

def test_use_of_replacer(conf):
    replacements = generate_replacements(conf, 'night')
    replace = generate_replacer(replacements)
    assert replace('${solarity:color:primary}') == '#CACCFD'
