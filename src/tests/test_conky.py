from conky import generate_replacements, Replacement


def test_generation_of_replacements(conf):
    replacements = generate_replacements(conf, 'night')
    assert tuple(replacements) == (
        Replacement(placeholder='${solarity:color:primary}', replacement='#CACCFD'),
        Replacement(placeholder='${solarity:color:secondary}', replacement='#3F72E8')
    )
