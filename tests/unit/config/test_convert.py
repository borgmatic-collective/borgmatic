from collections import defaultdict, OrderedDict, namedtuple
import os

from flexmock import flexmock
import pytest

from borgmatic.config import convert as module


Parsed_config = namedtuple('Parsed_config', ('location', 'storage', 'retention', 'consistency'))


def test_convert_section_generates_integer_value_for_integer_type_in_schema():
    flexmock(module.yaml.comments).should_receive('CommentedMap').replace_with(OrderedDict)
    source_section_config = OrderedDict([('check_last', '3')])
    section_schema = {'map': {'check_last': {'type': 'int'}}}

    destination_config = module._convert_section(source_section_config, section_schema)

    assert destination_config == OrderedDict([('check_last', 3)])


def test_convert_legacy_parsed_config_transforms_source_config_to_mapping():
    flexmock(module.yaml.comments).should_receive('CommentedMap').replace_with(OrderedDict)
    source_config = Parsed_config(
        location=OrderedDict([('source_directories', '/home'), ('repository', 'hostname.borg')]),
        storage=OrderedDict([('encryption_passphrase', 'supersecret')]),
        retention=OrderedDict([('keep_daily', 7)]),
        consistency=OrderedDict([('checks', 'repository')]),
    )
    source_excludes = ['/var']
    schema = {'map': defaultdict(lambda: {'map': {}})}

    destination_config = module.convert_legacy_parsed_config(source_config, source_excludes, schema)

    assert destination_config == OrderedDict(
        [
            (
                'location',
                OrderedDict(
                    [
                        ('source_directories', ['/home']),
                        ('repositories', ['hostname.borg']),
                        ('exclude_patterns', ['/var']),
                    ]
                ),
            ),
            ('storage', OrderedDict([('encryption_passphrase', 'supersecret')])),
            ('retention', OrderedDict([('keep_daily', 7)])),
            ('consistency', OrderedDict([('checks', ['repository'])])),
        ]
    )


def test_convert_legacy_parsed_config_splits_space_separated_values():
    flexmock(module.yaml.comments).should_receive('CommentedMap').replace_with(OrderedDict)
    source_config = Parsed_config(
        location=OrderedDict(
            [('source_directories', '/home /etc'), ('repository', 'hostname.borg')]
        ),
        storage=OrderedDict(),
        retention=OrderedDict(),
        consistency=OrderedDict([('checks', 'repository archives')]),
    )
    source_excludes = ['/var']
    schema = {'map': defaultdict(lambda: {'map': {}})}

    destination_config = module.convert_legacy_parsed_config(source_config, source_excludes, schema)

    assert destination_config == OrderedDict(
        [
            (
                'location',
                OrderedDict(
                    [
                        ('source_directories', ['/home', '/etc']),
                        ('repositories', ['hostname.borg']),
                        ('exclude_patterns', ['/var']),
                    ]
                ),
            ),
            ('storage', OrderedDict()),
            ('retention', OrderedDict()),
            ('consistency', OrderedDict([('checks', ['repository', 'archives'])])),
        ]
    )


def test_guard_configuration_upgraded_raises_when_only_source_config_present():
    flexmock(os.path).should_receive('exists').with_args('config').and_return(True)
    flexmock(os.path).should_receive('exists').with_args('config.yaml').and_return(False)
    flexmock(os.path).should_receive('exists').with_args('other.yaml').and_return(False)

    with pytest.raises(module.LegacyConfigurationNotUpgraded):
        module.guard_configuration_upgraded('config', ('config.yaml', 'other.yaml'))


def test_guard_configuration_upgraded_does_not_raise_when_only_destination_config_present():
    flexmock(os.path).should_receive('exists').with_args('config').and_return(False)
    flexmock(os.path).should_receive('exists').with_args('config.yaml').and_return(False)
    flexmock(os.path).should_receive('exists').with_args('other.yaml').and_return(True)

    module.guard_configuration_upgraded('config', ('config.yaml', 'other.yaml'))


def test_guard_configuration_upgraded_does_not_raise_when_both_configs_present():
    flexmock(os.path).should_receive('exists').with_args('config').and_return(True)
    flexmock(os.path).should_receive('exists').with_args('config.yaml').and_return(False)
    flexmock(os.path).should_receive('exists').with_args('other.yaml').and_return(True)

    module.guard_configuration_upgraded('config', ('config.yaml', 'other.yaml'))


def test_guard_configuration_upgraded_does_not_raise_when_neither_config_present():
    flexmock(os.path).should_receive('exists').with_args('config').and_return(False)
    flexmock(os.path).should_receive('exists').with_args('config.yaml').and_return(False)
    flexmock(os.path).should_receive('exists').with_args('other.yaml').and_return(False)

    module.guard_configuration_upgraded('config', ('config.yaml', 'other.yaml'))
