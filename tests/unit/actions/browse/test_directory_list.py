import rich.console
import rich.text
from flexmock import flexmock

from borgmatic.actions.browse import directory_list as module


def rendered_text(renderable):
    '''
    Given a Rich renderable, return its rendered plain text.
    '''
    console = rich.console.Console(width=60, color_system=None)

    with console.capture() as capture:
        console.print(renderable, end='')

    return capture.get()


def test_get_relative_archive_path_components_strips_off_current_directory():
    assert module.get_relative_archive_path_components(
        flexmock(file_path='foo/bar/baz/quux.txt'), ('foo', 'bar')
    ) == ('baz', 'quux.txt')


def test_get_relative_archive_path_components_with_root_current_directory_strips_off_nothing():
    assert module.get_relative_archive_path_components(
        flexmock(file_path='foo/bar/baz/quux.txt'), ()
    ) == ('foo', 'bar', 'baz', 'quux.txt')


def test_get_relative_archive_path_components_with_non_matching_paths_returns_none():
    assert (
        module.get_relative_archive_path_components(
            flexmock(file_path='foo/bar/baz/quux.txt'), ('etc',)
        )
        is None
    )


def test_make_size_path_prompt_with_size_renders_size_then_path():
    prompt = module.make_size_path_prompt(1024, '📄 baz.txt')

    assert isinstance(prompt, rich.text.Text)

    text = rendered_text(prompt)

    assert text.index('1.02 kB') < text.index('📄 baz.txt')


def test_make_size_path_prompt_with_no_size_renders_just_path():
    prompt = module.make_size_path_prompt(None, '📁 ..')

    assert '📁 ..' in rendered_text(prompt)


def test_make_size_path_prompt_aligns_paths_regardless_of_size_length():
    assert rendered_text(module.make_size_path_prompt(0, 'path')).index('path') == rendered_text(
        module.make_size_path_prompt(1024, 'path')
    ).index('path')


def test_make_size_path_prompt_aligns_bytes_number_with_larger_size_numbers():
    bytes_text = rendered_text(module.make_size_path_prompt(358, 'path'))
    kilobytes_text = rendered_text(module.make_size_path_prompt(1024, 'path'))

    assert bytes_text.index('358') + len('358') == kilobytes_text.index('1.02') + len('1.02')


def test_make_size_path_prompt_does_not_pad_larger_sizes():
    assert '1.02 kB  path' in rendered_text(module.make_size_path_prompt(1024, 'path'))


def test_make_directory_list_option_with_file_path_makes_file_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='-', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',), 1024
    )

    assert option.prompt_text == '📄 baz.txt (1.02 kB)'
    assert option.path_type == '-'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_directory_path_makes_directory_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='d', file_path='foo/bar/baz', link_target=''), ('baz',), 2048
    )

    assert option.prompt_text == '📁 baz (2.05 kB)'
    assert option.path_type == 'd'
    assert option.id == 'baz'


def test_make_directory_list_option_with_contained_file_path_makes_directory_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='d', file_path='foo/bar/baz.txt', link_target=''),
        (
            'bar',
            'baz.txt',
        ),
        0,
    )

    assert option.prompt_text == '📁 bar (0 B)'
    assert option.path_type == 'd'
    assert option.id == 'bar'


def test_make_directory_list_option_with_contained_symlink_path_has_no_link_target():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='l', file_path='mnt/link', link_target='/home/foo/.git'),
        (
            'mnt',
            'link',
        ),
        0,
    )

    assert option.prompt_text == '📁 mnt (0 B)'
    assert option.path_type == 'd'
    assert option.id == 'mnt'


def test_make_directory_list_option_with_link_path_makes_link_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='l', file_path='foo/bar/baz.txt', link_target='quux.txt'),
        ('baz.txt',),
        0,
    )

    assert option.prompt_text == '🔗 baz.txt → quux.txt (0 B)'
    assert option.path_type == 'l'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_pipe_path_makes_pipe_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='p', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',), 0
    )

    assert option.prompt_text == '🚰 baz.txt (0 B)'
    assert option.path_type == 'p'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_unknown_path_makes_unknown_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='wtf', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',), 0
    )

    assert option.prompt_text == '❓ baz.txt (0 B)'
    assert option.path_type == 'wtf'
    assert option.id == 'baz.txt'
