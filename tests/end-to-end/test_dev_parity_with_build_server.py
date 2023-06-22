import ruamel.yaml


def test_dev_docker_compose_has_same_services_as_build_server_configuration():
    yaml = ruamel.yaml.YAML(typ='safe')
    dev_services = {
        name: service
        for name, service in yaml.load(open('tests/end-to-end/docker-compose.yaml').read())['services'].items()
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
