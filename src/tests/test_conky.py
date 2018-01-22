from conky import compile_conky_templates


def test_invocation_of_compile_conky_templates(conf):
    compile_conky_templates(conf, 'night')
