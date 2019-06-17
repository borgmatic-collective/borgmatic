import sys

import pytest
import ruamel.yaml
from flexmock import flexmock

from borgmatic.config import load as module


def test_load_configuration_parses_contents():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('config.yaml').and_return('key: value')

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_inlines_include():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('include.yaml').and_return('value')
    builtins.should_receive('open').with_args('config.yaml').and_return(
        'key: !include include.yaml'
    )

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_merges_include():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('include.yaml').and_return(
        '''
        foo: bar
        baz: quux
        '''
    )
    builtins.should_receive('open').with_args('config.yaml').and_return(
        '''
        foo: override
        <<: !include include.yaml
        '''
    )

    assert module.load_configuration('config.yaml') == {'foo': 'override', 'baz': 'quux'}


def test_load_configuration_does_not_merge_include_list():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('include.yaml').and_return(
        '''
          - one
          - two
        '''
    )
    builtins.should_receive('open').with_args('config.yaml').and_return(
        '''
        foo: bar
        repositories:
          <<: !include include.yaml
        '''
    )

    with pytest.raises(ruamel.yaml.error.YAMLError):
        assert module.load_configuration('config.yaml')
