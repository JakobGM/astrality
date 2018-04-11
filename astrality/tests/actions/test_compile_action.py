from pathlib import Path

from astrality.actions import CompileAction

def test_null_object_pattern():
    """Compilation action with no parameters should be a null object."""
    compile_action = CompileAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
    )
    target = compile_action.execute()
    assert target is None


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
