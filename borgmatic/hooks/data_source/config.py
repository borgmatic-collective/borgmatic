import json
import logging
import shutil
import subprocess

from borgmatic.execute import execute_command_and_capture_output

IS_A_HOOK = False

logger = logging.getLogger(__name__)


def resolve_database_option(option, data_source, connection_params=None, restore=False):
    '''
    Resolves a database option from the given data source configuration dict and
    connection parameters dict. If restore is set to True it will consider the
    `restore_<option>` instead.

    Returns the resolved option or None. Can raise a ValueError if the hostname lookup
    results in a container IP check.
    '''
    # Special case `hostname` since it overlaps with `container`
    if option == 'hostname':
        return get_hostname_from_config(data_source, connection_params, restore)
    if connection_params and (value := connection_params.get(option)):
        return value
    if restore and f'restore_{option}' in data_source:
        return data_source[f'restore_{option}']

    return data_source.get(option)


def get_hostname_from_config(data_source, connection_params=None, restore=False):
    '''
    Specialisation of `resolve_database_option` to handle the extra complexity of
    the hostname option to also handle containers.

    Returns a hostname/IP or raises an ValueError if a container IP lookup fails.
    '''
    # connection params win, full stop
    if connection_params:
        if container := connection_params.get('container'):
            return get_ip_from_container(container)
        if hostname := connection_params.get('hostname'):
            return hostname
    # ... then try the restore config
    if restore:
        if 'restore_container' in data_source:
            return get_ip_from_container(data_source['restore_container'])
        if 'restore_hostname' in data_source:
            return data_source['restore_hostname']
    # ... and finally fall back to the normal options
    if 'container' in data_source:
        return get_ip_from_container(data_source['container'])

    return data_source.get('hostname')


def get_ip_from_container(container):
    '''
    Determine the IP for a given container name via podman and docker.

    Returns an IP or raises a ValueError if the lookup fails.
    '''
    engines = (shutil.which(engine) for engine in ('docker', 'podman'))
    engines = [engine for engine in engines if engine]

    if not engines:
        raise ValueError("Neither 'docker' nor 'podman' could be found on the system")

    last_error = None
    for engine in engines:
        try:
            output = execute_command_and_capture_output(
                (
                    engine,
                    'container',
                    'inspect',
                    '--format={{json .NetworkSettings}}',
                    container,
                )
            )
        except subprocess.CalledProcessError as error:
            last_error = error
            logger.debug(f"Could not find container '{container}' with engine '{engine}'")
            continue  # Container does not exist

        try:
            network_data = json.loads(output.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f'Could not decode JSON output from {engine}') from e
        if main_ip := network_data.get('IPAddress'):
            return main_ip
        # No main IP found, try the networks
        for network in network_data.get('Networks', {}).values():
            if ip := network.get('IPAddress'):
                return ip

    if last_error:
        raise last_error

    raise ValueError(
        f"Could not determine ip address for container '{container}'; running in host mode or userspace networking?"
    )
