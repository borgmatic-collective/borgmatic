import pytest
from flexmock import flexmock

from borgmatic.config import paths as module


def test_expand_user_in_path_passes_through_plain_directory():
    flexmock(module.os.path).should_receive('expanduser').and_return('/home/foo')
    assert module.expand_user_in_path('/home/foo') == '/home/foo'


def test_expand_user_in_path_expands_tildes():
    flexmock(module.os.path).should_receive('expanduser').and_return('/home/foo')
    assert module.expand_user_in_path('~/foo') == '/home/foo'


def test_expand_user_in_path_handles_empty_directory():
    assert module.expand_user_in_path('') is None


def test_expand_user_in_path_handles_none_directory():
    assert module.expand_user_in_path(None) is None


def test_expand_user_in_path_handles_incorrectly_typed_directory():
    assert module.expand_user_in_path(3) is None


def test_get_borgmatic_source_directory_uses_config_option():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)

    assert module.get_borgmatic_source_directory({'borgmatic_source_directory': '/tmp'}) == '/tmp'


def test_get_borgmatic_source_directory_without_config_option_uses_default():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)

    assert module.get_borgmatic_source_directory({}) == '~/.borgmatic'


def test_replace_temporary_subdirectory_with_glob_transforms_path():
    assert (
        module.replace_temporary_subdirectory_with_glob('/tmp/borgmatic-aet8kn93/borgmatic')
        == '/tmp/borgmatic-*/borgmatic'
    )


def test_replace_temporary_subdirectory_with_glob_passes_through_non_matching_path():
    assert (
        module.replace_temporary_subdirectory_with_glob('/tmp/foo-aet8kn93/borgmatic')
        == '/tmp/foo-aet8kn93/borgmatic'
    )


def test_replace_temporary_subdirectory_with_glob_uses_custom_temporary_directory_prefix():
    assert (
        module.replace_temporary_subdirectory_with_glob(
            '/tmp/.borgmatic-aet8kn93/borgmatic', temporary_directory_prefix='.borgmatic-'
        )
        == '/tmp/.borgmatic-*/borgmatic'
    )


def test_runtime_directory_uses_config_option():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os).should_receive('makedirs')
    config = {'user_runtime_directory': '/run', 'borgmatic_source_directory': '/nope'}

    with module.Runtime_directory(config) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/./borgmatic'


def test_runtime_directory_uses_config_option_without_adding_duplicate_borgmatic_subdirectory():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os).should_receive('makedirs')
    config = {'user_runtime_directory': '/run/borgmatic', 'borgmatic_source_directory': '/nope'}

    with module.Runtime_directory(config) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/./borgmatic'


def test_runtime_directory_with_relative_config_option_errors():
    flexmock(module.os).should_receive('makedirs').never()
    config = {'user_runtime_directory': 'run', 'borgmatic_source_directory': '/nope'}

    with pytest.raises(ValueError):
        with module.Runtime_directory(
            config
        ) as borgmatic_runtime_directory:  # noqa: F841
            pass


def test_runtime_directory_falls_back_to_xdg_runtime_dir():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(
        '/run'
    )
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/./borgmatic'


def test_runtime_directory_falls_back_to_xdg_runtime_dir_without_adding_duplicate_borgmatic_subdirectory():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(
        '/run/borgmatic'
    )
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/./borgmatic'


def test_runtime_directory_with_relative_xdg_runtime_dir_errors():
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return('run')
    flexmock(module.os).should_receive('makedirs').never()

    with pytest.raises(ValueError):
        with module.Runtime_directory({}) as borgmatic_runtime_directory:  # noqa: F841
            pass


def test_runtime_directory_falls_back_to_runtime_directory():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        '/run'
    )
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/./borgmatic'


def test_runtime_directory_falls_back_to_runtime_directory_without_adding_duplicate_borgmatic_subdirectory():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        '/run/borgmatic'
    )
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/./borgmatic'


def test_runtime_directory_with_relative_runtime_directory_errors():
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        'run'
    )
    flexmock(module.os).should_receive('makedirs').never()

    with pytest.raises(ValueError):
        with module.Runtime_directory({}) as borgmatic_runtime_directory:  # noqa: F841
            pass


def test_runtime_directory_falls_back_to_tmpdir_and_adds_temporary_subdirectory_that_get_cleaned_up():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        None
    )
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return('/run')
    temporary_directory = flexmock(name='/run/borgmatic-1234')
    temporary_directory.should_receive('cleanup').once()
    flexmock(module.tempfile).should_receive('TemporaryDirectory').with_args(
        prefix='borgmatic-', dir='/run'
    ).and_return(temporary_directory)
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/borgmatic-1234/./borgmatic'


def test_runtime_directory_with_relative_tmpdir_errors():
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        None
    )
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return('run')
    flexmock(module.tempfile).should_receive('TemporaryDirectory').never()
    flexmock(module.os).should_receive('makedirs').never()

    with pytest.raises(ValueError):
        with module.Runtime_directory({}) as borgmatic_runtime_directory:  # noqa: F841
            pass


def test_runtime_directory_falls_back_to_temp_and_adds_temporary_subdirectory_that_get_cleaned_up():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        None
    )
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TEMP').and_return('/run')
    temporary_directory = flexmock(name='/run/borgmatic-1234')
    temporary_directory.should_receive('cleanup').once()
    flexmock(module.tempfile).should_receive('TemporaryDirectory').with_args(
        prefix='borgmatic-', dir='/run'
    ).and_return(temporary_directory)
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/run/borgmatic-1234/./borgmatic'


def test_runtime_directory_with_relative_temp_errors():
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        None
    )
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TEMP').and_return('run')
    flexmock(module.tempfile).should_receive('TemporaryDirectory').never()
    flexmock(module.os).should_receive('makedirs')

    with pytest.raises(ValueError):
        with module.Runtime_directory({}) as borgmatic_runtime_directory:  # noqa: F841
            pass


def test_runtime_directory_falls_back_to_hard_coded_tmp_path_and_adds_temporary_subdirectory_that_get_cleaned_up():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        None
    )
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TEMP').and_return(None)
    temporary_directory = flexmock(name='/tmp/borgmatic-1234')
    temporary_directory.should_receive('cleanup').once()
    flexmock(module.tempfile).should_receive('TemporaryDirectory').with_args(
        prefix='borgmatic-', dir='/tmp'
    ).and_return(temporary_directory)
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/tmp/borgmatic-1234/./borgmatic'


def test_runtime_directory_with_erroring_cleanup_does_not_raise():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('RUNTIME_DIRECTORY').and_return(
        None
    )
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TEMP').and_return(None)
    temporary_directory = flexmock(name='/tmp/borgmatic-1234')
    temporary_directory.should_receive('cleanup').and_raise(OSError).once()
    flexmock(module.tempfile).should_receive('TemporaryDirectory').with_args(
        prefix='borgmatic-', dir='/tmp'
    ).and_return(temporary_directory)
    flexmock(module.os).should_receive('makedirs')

    with module.Runtime_directory({}) as borgmatic_runtime_directory:
        assert borgmatic_runtime_directory == '/tmp/borgmatic-1234/./borgmatic'


@pytest.mark.parametrize(
    'borgmatic_runtime_directory,expected_glob',
    (
        ('/foo/bar/baz/./borgmatic', 'foo/bar/baz/borgmatic'),
        ('/foo/borgmatic/baz/./borgmatic', 'foo/borgmatic/baz/borgmatic'),
        ('/foo/borgmatic-jti8idds/./borgmatic', 'foo/*/borgmatic'),
    ),
)
def test_make_runtime_directory_glob(borgmatic_runtime_directory, expected_glob):
    assert module.make_runtime_directory_glob(borgmatic_runtime_directory) == expected_glob


def test_get_borgmatic_state_directory_uses_config_option():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').never()

    assert (
        module.get_borgmatic_state_directory(
            {'user_state_directory': '/tmp', 'borgmatic_source_directory': '/nope'}
        )
        == '/tmp/borgmatic'
    )


def test_get_borgmatic_state_directory_falls_back_to_xdg_state_home():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_STATE_HOME').and_return('/tmp')

    assert module.get_borgmatic_state_directory({}) == '/tmp/borgmatic'


def test_get_borgmatic_state_directory_falls_back_to_state_directory():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_STATE_HOME').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('STATE_DIRECTORY').and_return(
        '/tmp'
    )

    assert module.get_borgmatic_state_directory({}) == '/tmp/borgmatic'


def test_get_borgmatic_state_directory_defaults_to_hard_coded_path():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').and_return(None)
    assert module.get_borgmatic_state_directory({}) == '~/.local/state/borgmatic'
