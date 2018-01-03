import io
import string
import sys
import os

from flexmock import flexmock
import pytest

from borgmatic.config import validate as module


def test_schema_filename_returns_plausable_path():
    schema_path = module.schema_filename()    

    assert schema_path.endswith('/schema.yaml')


def mock_config_and_schema(config_yaml, schema_yaml=None):
    '''
    Set up mocks for the given config config YAML string and the schema YAML string, or the default
    schema if no schema is provided. The idea is that that the code under test consumes these mocks
    when parsing the configuration.
    '''
    config_stream = io.StringIO(config_yaml)
    if schema_yaml is None:
        schema_stream = open(module.schema_filename())
    else:
        schema_stream = io.StringIO(schema_yaml)

    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('config.yaml').and_return(config_stream)
    builtins.should_receive('open').with_args('schema.yaml').and_return(schema_stream)


def test_parse_configuration_transforms_file_into_mapping():
    mock_config_and_schema(
        '''
        location:
            source_directories:
                - /home
                - /etc

            repositories:
                - hostname.borg

        retention:
            keep_minutely: 60
            keep_hourly: 24
            keep_daily: 7

        consistency:
            checks:
                - repository
                - archives
        '''
    )

    result = module.parse_configuration('config.yaml', 'schema.yaml')

    assert result == {
        'location': {'source_directories': ['/home', '/etc'], 'repositories': ['hostname.borg']},
        'retention': {'keep_daily': 7, 'keep_hourly': 24, 'keep_minutely': 60},
        'consistency': {'checks': ['repository', 'archives']},
    }


def test_parse_configuration_passes_through_quoted_punctuation():
    escaped_punctuation = string.punctuation.replace('\\', r'\\').replace('"', r'\"')

    mock_config_and_schema(
        '''
        location:
            source_directories:
                - /home

            repositories:
                - "{}.borg"
        '''.format(escaped_punctuation)
    )

    result = module.parse_configuration('config.yaml', 'schema.yaml')

    assert result == {
        'location': {
            'source_directories': ['/home'],
            'repositories': ['{}.borg'.format(string.punctuation)],
        },
    }


def test_parse_configuration_with_schema_lacking_examples_does_not_raise():
    mock_config_and_schema(
        '''
        location:
            source_directories:
                - /home

            repositories:
                - hostname.borg
        ''',
        '''
        map:
            location:
                required: true
                map:
                    source_directories:
                        required: true
                        seq:
                            - type: scalar
                    repositories:
                        required: true
                        seq:
                            - type: scalar
        '''
    )

    module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_missing_config_file():
    with pytest.raises(FileNotFoundError):
        module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_missing_schema_file():
    mock_config_and_schema('')
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('schema.yaml').and_raise(FileNotFoundError)

    with pytest.raises(FileNotFoundError):
        module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_syntax_error():
    mock_config_and_schema('foo:\nbar')

    with pytest.raises(ValueError):
        module.parse_configuration('config.yaml', 'schema.yaml')


def test_parse_configuration_raises_for_validation_error():
    mock_config_and_schema(
        '''
        location:
            source_directories: yes
            repositories:
                - hostname.borg
        '''
    )

    with pytest.raises(module.Validation_error):
        module.parse_configuration('config.yaml', 'schema.yaml')
