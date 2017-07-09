from collections import defaultdict, OrderedDict, namedtuple

from borgmatic.config import convert as module


Parsed_config = namedtuple('Parsed_config', ('location', 'storage', 'retention', 'consistency'))


def test_convert_legacy_parsed_config_transforms_source_config_to_mapping():
    source_config = Parsed_config(
        location=OrderedDict([('source_directories', '/home'), ('repository', 'hostname.borg')]),
        storage=OrderedDict([('encryption_passphrase', 'supersecret')]),
        retention=OrderedDict([('keep_daily', 7)]),
        consistency=OrderedDict([('checks', 'repository')]),
    )
    schema = {'map': defaultdict(lambda: {'map': {}})}

    destination_config = module.convert_legacy_parsed_config(source_config, schema)

    assert destination_config == OrderedDict([
        ('location', OrderedDict([('source_directories', ['/home']), ('repository', 'hostname.borg')])),
        ('storage', OrderedDict([('encryption_passphrase', 'supersecret')])),
        ('retention', OrderedDict([('keep_daily', 7)])),
        ('consistency', OrderedDict([('checks', ['repository'])])),
    ])


def test_convert_legacy_parsed_config_splits_space_separated_values():
    source_config = Parsed_config(
        location=OrderedDict([('source_directories', '/home /etc')]),
        storage=OrderedDict(),
        retention=OrderedDict(),
        consistency=OrderedDict([('checks', 'repository archives')]),
    )
    schema = {'map': defaultdict(lambda: {'map': {}})}

    destination_config = module.convert_legacy_parsed_config(source_config, schema) 

    assert destination_config == OrderedDict([
        ('location', OrderedDict([('source_directories', ['/home', '/etc'])])),
        ('storage', OrderedDict()),
        ('retention', OrderedDict()),
        ('consistency', OrderedDict([('checks', ['repository', 'archives'])])),
    ])
