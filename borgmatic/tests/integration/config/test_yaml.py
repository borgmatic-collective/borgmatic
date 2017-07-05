import io
import string
import sys
import os

from flexmock import flexmock
import pytest

from borgmatic.config import yaml as module


def test_schema_filename_returns_plausable_path():
    schema_path = module.schema_filename()    

    assert schema_path.endswith('/schema.yaml')


def mock_config_and_schema(config_yaml):
    '''
    Set up mocks for the config config YAML string and the default schema so that pykwalify consumes
    them when parsing the configuration. This is a little brittle in that it's relying on pykwalify
    to open() the respective files in a particular order.
    '''
    config_stream = io.StringIO(config_yaml)
    schema_stream = open(module.schema_filename())
    builtins = flexmock(sys.modules['builtins']).should_call('open').mock
    builtins.should_receive('open').and_return(config_stream).and_return(schema_stream)
    flexmock(os.path).should_receive('exists').and_return(True)


def test_parse_configuration_transforms_file_into_mapping():
    mock_config_and_schema(
        '''
        location:
            source_directories:
                - /home
                - /etc

            repository: hostname.borg

        retention:
            keep_daily: 7

        consistency:
            checks:
                - repository
                - archives
        '''
    )

    result = module.parse_configuration('config.yaml', 'schema.yaml')

    assert result == {
        'location': {'source_directories': ['/home', '/etc'], 'repository': 'hostname.borg'},
        'retention': {'keep_daily': 7},
        'consistency': {'checks': ['repository', 'archives']},
    }


def test_parse_configuration_passes_through_quoted_punctuation():
    escaped_punctuation = string.punctuation.replace('\\', r'\\').replace('"', r'\"')

    mock_config_and_schema(
        '''
        location:
            source_directories:
                - /home

            repository: "{}.borg"
        '''.format(escaped_punctuation)
    )

    result = module.parse_configuration('config.yaml', 'schema.yaml')

    assert result == {
        'location': {
            'source_directories': ['/home'],
            'repository': '{}.borg'.format(string.punctuation),
        },
    }


def test_parse_configuration_raises_for_missing_config_file():
    with pytest.raises(FileNotFoundError):
        module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_missing_schema_file():
    mock_config_and_schema('')
    flexmock(os.path).should_receive('exists').with_args('schema.yaml').and_return(False)

    with pytest.raises(FileNotFoundError):
        module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_syntax_error():
    mock_config_and_schema('invalid = yaml')

    with pytest.raises(module.Validation_error):
        module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_validation_error():
    mock_config_and_schema(
        '''
        location:
            source_directories: yes
            repository: hostname.borg
        '''
    )

    with pytest.raises(module.Validation_error):
        module.parse_configuration('config.yaml', 'schema.yaml')
