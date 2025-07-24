import json
import shutil
import subprocess

from borgmatic.execute import execute_command_and_capture_output

IS_A_HOOK = False


def get_hostname_from_config(database):
    if 'container' in database:
        return get_ip_from_container(database['container'])
    return database.get('hostname', '')


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
