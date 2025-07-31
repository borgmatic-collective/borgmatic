from subprocess import CalledProcessError

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import config


def test_get_database_option():
    data_source = {'option': 'original_value', 'restore_option': 'restore_value'}
    connection_params = {'option': 'connection_value'}

    assert config.resolve_database_option('option', data_source) == 'original_value'
    assert config.resolve_database_option('option', data_source, restore=True) == 'restore_value'
    assert (
        config.resolve_database_option('option', data_source, connection_params)
        == 'connection_value'
    )
    assert (
        config.resolve_database_option('option', data_source, connection_params, restore=True)
        == 'connection_value'
    )


def test_get_hostname_option_via_container():
    data_source = {
        'container': 'original_container',
        'hostname': 'original_hostname',
        'restore_container': 'restore_container',
        'restore_hostname': 'restore_hostname',
    }
    connection_params = {'container': 'connection_container', 'hostname': 'connection_hostname'}

    flexmock(config).should_receive('get_ip_from_container').with_args(
        'original_container'
    ).and_return('container_ip_1')
    flexmock(config).should_receive('get_ip_from_container').with_args(
        'connection_container'
    ).and_return('container_ip_2')
    flexmock(config).should_receive('get_ip_from_container').with_args(
        'restore_container'
    ).and_return('container_ip_3')

    assert config.resolve_database_option('hostname', data_source) == 'container_ip_1'
    assert (
        config.resolve_database_option('hostname', data_source, connection_params)
        == 'container_ip_2'
    )
    assert config.resolve_database_option('hostname', data_source, restore=True) == 'container_ip_3'


def test_get_container_ip_without_engines():
    flexmock(config.shutil).should_receive('which').and_return(None).and_return(None)

    with pytest.raises(ValueError):
        config.get_ip_from_container('yolo')


def test_get_container_ip_success():
    flexmock(config.shutil).should_receive('which').and_return(None).and_return('/usr/bin/podman')

    flexmock(config).should_receive('execute_command_and_capture_output').and_return(
        '{"IPAddress": "1.2.3.4"}'
    )

    addr = config.get_ip_from_container('yolo')
    assert addr == '1.2.3.4'

    flexmock(config).should_receive('execute_command_and_capture_output').and_return(
        '{"Networks": {"my_network": {"IPAddress": "5.6.7.8"}}}'
    )

    assert config.get_ip_from_container('yolo') == '5.6.7.8'


def test_get_container_ip_container_not_found():
    flexmock(config.shutil).should_receive('which').and_return('/usr/bin/podman')
    flexmock(config).should_receive('execute_command_and_capture_output').and_raise(
        CalledProcessError, 1, ['/usr/bin/podman', 'inspect', 'yolo'], None, 'No such object'
    )

    with pytest.raises(CalledProcessError):
        config.get_ip_from_container('does not exist')


def test_get_container_ip_container_no_network():
    flexmock(config.shutil).should_receive('which').and_return(None).and_return('/usr/bin/podman')

    flexmock(config).should_receive('execute_command_and_capture_output').and_return('{}')

    with pytest.raises(ValueError) as exc_info:
        config.get_ip_from_container('yolo')
    assert 'Could not determine ip address for container' in str(exc_info.value)
