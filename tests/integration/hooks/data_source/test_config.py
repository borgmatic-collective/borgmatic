from flexmock import flexmock

from borgmatic.hooks.data_source import config as module


def test_resolve_database_option_gets_hostname_from_container_ip():
    data_source = {
        'container': 'original_container',
        'hostname': 'original_hostname',
        'restore_container': 'restore_container',
        'restore_hostname': 'restore_hostname',
    }

    flexmock(module).should_receive('get_ip_from_container').with_args(
        'original_container'
    ).and_return('container_ip_1')

    assert module.resolve_database_option('hostname', data_source) == 'container_ip_1'


def test_resolve_database_option_gets_hostname_from_connection_params_container_ip():
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

    assert (
        module.resolve_database_option('hostname', data_source, connection_params)
        == 'container_ip_2'
    )


def test_resolve_database_option_gets_hostname_from_restore_container_ip():
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

    assert module.resolve_database_option('hostname', data_source, restore=True) == 'container_ip_3'
