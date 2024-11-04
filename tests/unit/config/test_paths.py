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


def test_get_borgmatic_source_directory_uses_config_option():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)

    assert module.get_borgmatic_source_directory({'borgmatic_source_directory': '/tmp'}) == '/tmp'


def test_get_borgmatic_source_directory_without_config_option_uses_default():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)

    assert module.get_borgmatic_source_directory({}) == '~/.borgmatic'


def test_get_borgmatic_runtime_directory_uses_config_option():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)

    assert (
        module.get_borgmatic_runtime_directory(
            {'user_runtime_directory': '/tmp', 'borgmatic_source_directory': '/nope'}
        )
        == '/tmp/./borgmatic'
    )


def test_get_borgmatic_runtime_directory_falls_back_to_linux_environment_variable():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(
        '/tmp'
    )

    assert module.get_borgmatic_runtime_directory({}) == '/tmp/./borgmatic'


def test_get_borgmatic_runtime_directory_falls_back_to_macos_environment_variable():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return('/tmp')

    assert module.get_borgmatic_runtime_directory({}) == '/tmp/./borgmatic'


def test_get_borgmatic_runtime_directory_falls_back_to_other_environment_variable():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args('XDG_RUNTIME_DIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TMPDIR').and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('TEMP').and_return('/tmp')

    assert module.get_borgmatic_runtime_directory({}) == '/tmp/./borgmatic'


def test_get_borgmatic_runtime_directory_defaults_to_hard_coded_path():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').and_return('/run/user/0')
    flexmock(module.os).should_receive('getuid').and_return(0)

    assert module.get_borgmatic_runtime_directory({}) == '/run/user/0/./borgmatic'


def test_get_borgmatic_state_directory_uses_config_option():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)

    assert (
        module.get_borgmatic_state_directory(
            {'user_state_directory': '/tmp', 'borgmatic_source_directory': '/nope'}
        )
        == '/tmp/borgmatic'
    )


def test_get_borgmatic_state_directory_falls_back_to_environment_variable():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').with_args(
        'XDG_STATE_HOME', object
    ).and_return('/tmp')

    assert module.get_borgmatic_state_directory({}) == '/tmp/borgmatic'


def test_get_borgmatic_state_directory_defaults_to_hard_coded_path():
    flexmock(module).should_receive('expand_user_in_path').replace_with(lambda path: path)
    flexmock(module.os.environ).should_receive('get').and_return('/root/.local/state')
    assert module.get_borgmatic_state_directory({}) == '/root/.local/state/borgmatic'
