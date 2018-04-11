from astrality.actions import CompileAction

def test_compilation_of_template_to_temporary_file(template_directory):
    """Compile template to temporary file in absence of `target`."""
    compile_dict = {
        'template': 'no_context.template',
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )
    target = compile_action.execute()

    assert target.read_text() == 'one\ntwo\nthree'
