import json
import shutil
import subprocess

from borgmatic.execute import execute_command_and_capture_output

IS_A_HOOK = False


def resolve_database_option(option, data_source, connection_params=None, restore=False):
    # Special case `hostname` since it overlaps with `container`
    if option == 'hostname':
        return _get_hostname_from_config(data_source, connection_params, restore)
    if connection_params and (value := connection_params.get(option)):
        return value
    if restore and f'restore_{option}' in data_source:
        return data_source[f'restore_{option}']
    return data_source.get(option)


def _get_hostname_from_config(data_source, connection_params=None, restore=False):
    # connection params win, full stop
    if connection_params:
        if container := connection_params.get('container'):
            return container
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
    return data_source.get('hostname', '')


def get_ip_from_container(container):
    engines = (shutil.which(engine) for engine in ('docker', 'podman'))
    engines = [engine for engine in engines if engine]

    if not engines:
        raise xxx  # TODO: What to raise here, tell the user to install docker/podman

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
        except subprocess.CalledProcessError:
            continue  # Container does not exist

        network_data = json.loads(output.strip())
        main_ip = network_data.get('IPAddress')
        if main_ip:
            return main_ip
        # No main IP found, try the networks
        for network in network_data.get('Networks', {}).values():
            ip = network.get('IPAddress')
            if ip:
                return ip

    raise xxx  # No container ip found, what to raise here
