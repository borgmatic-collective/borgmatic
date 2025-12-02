from subprocess import CalledProcessError

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import config as module


def test_resolve_database_option_uses_config_value():
    data_source = {'option': 'original_value', 'restore_option': 'restore_value'}

    assert module.resolve_database_option('option', data_source) == 'original_value'


def test_resolve_database_option_with_restore_uses_restore_value():
    data_source = {'option': 'original_value', 'restore_option': 'restore_value'}

    assert module.resolve_database_option('option', data_source, restore=True) == 'restore_value'


def test_resolve_database_option_with_connection_params_uses_connection_params_value():
    data_source = {'option': 'original_value', 'restore_option': 'restore_value'}
    connection_params = {'option': 'connection_value'}

    assert (
        module.resolve_database_option('option', data_source, connection_params)
        == 'connection_value'
    )


def test_resolve_database_option_with_restore_and_connection_params_uses_connection_params_value():
    data_source = {'option': 'original_value', 'restore_option': 'restore_value'}
    connection_params = {'option': 'connection_value'}

    assert (
        module.resolve_database_option('option', data_source, connection_params, restore=True)
        == 'connection_value'
    )


def test_resolve_database_option_with_hostname_uses_hostname_specific_function():
    data_source = {'hostname': 'original_value'}
    connection_params = {'hostname': 'connection_value'}

    flexmock(module).should_receive('get_hostname_from_config').and_return('special_value').once()

    assert (
        module.resolve_database_option('hostname', data_source, connection_params, restore=True)
        == 'special_value'
    )


def test_get_hostname_from_config_gets_container_ip():
    data_source = {
        'container': 'original_container',
        'hostname': 'original_hostname',
        'restore_container': 'restore_container',
        'restore_hostname': 'restore_hostname',
    }

    flexmock(module).should_receive('get_ip_from_container').with_args(
        'original_container'
    ).and_return('container_ip_1')

    assert module.get_hostname_from_config(data_source) == 'container_ip_1'


def test_get_hostname_from_config_gets_connection_params_container_ip():
    data_source = {
        'container': 'original_container',
        'hostname': 'original_hostname',
        'restore_container': 'restore_container',
        'restore_hostname': 'restore_hostname',
    }
    connection_params = {'container': 'connection_container', 'hostname': 'connection_hostname'}

    flexmock(module).should_receive('get_ip_from_container').with_args('original_container').never()
    flexmock(module).should_receive('get_ip_from_container').with_args(
        'connection_container'
    ).and_return('container_ip_2')

    assert module.get_hostname_from_config(data_source, connection_params) == 'container_ip_2'


def test_get_hostname_from_config_gets_restore_container_ip():
    data_source = {
        'container': 'original_container',
        'hostname': 'original_hostname',
        'restore_container': 'restore_container',
        'restore_hostname': 'restore_hostname',
    }

    flexmock(module).should_receive('get_ip_from_container').with_args('original_container').never()
    flexmock(module).should_receive('get_ip_from_container').with_args(
        'restore_container'
    ).and_return('container_ip_3')

    assert module.get_hostname_from_config(data_source, restore=True) == 'container_ip_3'


def test_get_ip_from_container_without_engines_errors():
    flexmock(module.shutil).should_receive('which').and_return(None).and_return(None)

    with pytest.raises(ValueError):
        module.get_ip_from_container('yolo')


def test_get_ip_from_container_parses_top_level_ip_address():
    flexmock(module.shutil).should_receive('which').and_return(None).and_return('/usr/bin/podman')

    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '{"IPAddress": "1.2.3.4"}'
    )

    assert module.get_ip_from_container('yolo') == '1.2.3.4'


def test_get_ip_from_container_parses_network_ip_address():
    flexmock(module.shutil).should_receive('which').and_return(None).and_return('/usr/bin/podman')

    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '{"Networks": {"my_network": {"IPAddress": "5.6.7.8"}}}'
    )

    assert module.get_ip_from_container('yolo') == '5.6.7.8'


def test_get_ip_from_container_without_container_errors():
    flexmock(module.shutil).should_receive('which').and_return('/usr/bin/podman')
    flexmock(module).should_receive('execute_command_and_capture_output').and_raise(
        CalledProcessError, 1, ['/usr/bin/podman', 'inspect', 'yolo'], None, 'No such object'
    )

    with pytest.raises(CalledProcessError):
        module.get_ip_from_container('does not exist')


def test_get_ip_from_container_without_network_errors():
    flexmock(module.shutil).should_receive('which').and_return(None).and_return('/usr/bin/podman')

    flexmock(module).should_receive('execute_command_and_capture_output').and_return('{}')

    with pytest.raises(ValueError) as exc_info:
        module.get_ip_from_container('yolo')

    assert 'Could not determine ip address for container' in str(exc_info.value)


def test_get_ip_from_container_with_broken_output_errors():
    flexmock(module.shutil).should_receive('which').and_return(None).and_return('/usr/bin/podman')

    flexmock(module).should_receive('execute_command_and_capture_output').and_return('abc')

    with pytest.raises(ValueError) as exc_info:
        module.get_ip_from_container('yolo')

    assert 'Could not decode JSON output' in str(exc_info.value)


def test_inject_pattern_prepends_pattern_in_list():
    patterns = [
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
    ]

    module.inject_pattern(
        patterns,
        module.borgmatic.borg.pattern.Pattern(
            '/foo/bar',
            type=module.borgmatic.borg.pattern.Pattern_type.EXCLUDE,
        ),
    )

    assert patterns == [
        module.borgmatic.borg.pattern.Pattern(
            '/foo/bar',
            type=module.borgmatic.borg.pattern.Pattern_type.EXCLUDE,
        ),
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
    ]


def test_inject_pattern_with_root_pattern_prepends_it_along_with_corresponding_include_pattern():
    patterns = [
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
    ]

    module.inject_pattern(
        patterns,
        module.borgmatic.borg.pattern.Pattern('/foo/bar'),
    )

    assert patterns == [
        module.borgmatic.borg.pattern.Pattern('/foo/bar'),
        module.borgmatic.borg.pattern.Pattern(
            '/foo/bar',
            type=module.borgmatic.borg.pattern.Pattern_type.INCLUDE,
        ),
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
    ]


def test_inject_pattern_with_root_pattern_and_override_excludes_false_omits_include_pattern():
    patterns = [
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
    ]

    module.inject_pattern(
        patterns,
        module.borgmatic.borg.pattern.Pattern('/foo/bar'),
        override_excludes=False,
    )

    assert patterns == [
        module.borgmatic.borg.pattern.Pattern('/foo/bar'),
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
    ]


def test_replace_pattern_swaps_out_pattern_in_place():
    patterns = [
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
        module.borgmatic.borg.pattern.Pattern('/lib'),
    ]

    module.replace_pattern(
        patterns,
        module.borgmatic.borg.pattern.Pattern('/var'),
        module.borgmatic.borg.pattern.Pattern(
            '/foo/bar',
            type=module.borgmatic.borg.pattern.Pattern_type.EXCLUDE,
        ),
    )

    assert patterns == [
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern(
            '/foo/bar',
            type=module.borgmatic.borg.pattern.Pattern_type.EXCLUDE,
        ),
        module.borgmatic.borg.pattern.Pattern('/lib'),
    ]


def test_replace_pattern_with_unknown_pattern_falls_back_to_injecting():
    patterns = [
        module.borgmatic.borg.pattern.Pattern('/etc'),
        module.borgmatic.borg.pattern.Pattern('/var'),
        module.borgmatic.borg.pattern.Pattern('/lib'),
    ]
    flexmock(module).should_receive('inject_pattern').with_args(
        patterns,
        module.borgmatic.borg.pattern.Pattern('/foo/bar'),
        override_excludes=False,
    ).once()

    module.replace_pattern(
        patterns,
        module.borgmatic.borg.pattern.Pattern('/unknown'),
        module.borgmatic.borg.pattern.Pattern('/foo/bar'),
    )
