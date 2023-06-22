import ruamel.yaml


def test_dev_docker_compose_has_same_services_as_build_server_configuration():
    '''
    The end-to-end test configuration for local development and the build server's test
    configuration use two different mechanisms for configuring and spinning up "services"—the
    database containers upon which the end-to-end tests are reliant. The dev configuration uses
    Docker Compose, while the Drone build server configuration uses its own similar-but-different
    configuration file format.

    Therefore, to ensure dev-build parity, these tests assert that the services are the same across
    the dev and build configurations. This includes service name, container image, environment
    variables, and commands.

    This test only compares services and does not assert anything else about the respective testing
    environments.
    '''
    yaml = ruamel.yaml.YAML(typ='safe')
    dev_services = {
        name: service
        for name, service in yaml.load(open('tests/end-to-end/docker-compose.yaml').read())[
            'services'
        ].items()
        if name != 'tests'
    }
    build_server_services = tuple(yaml.load_all(open('.drone.yml').read()))[0]['services']

    assert len(dev_services) == len(build_server_services)

    for build_service in build_server_services:
        dev_service = dev_services[build_service['name']]
        assert dev_service['image'] == build_service['image']
        assert dev_service['environment'] == build_service['environment']

        if 'command' in dev_service or 'commands' in build_service:
            assert len(build_service['commands']) <= 1
            assert dev_service['command'] == build_service['commands'][0]
