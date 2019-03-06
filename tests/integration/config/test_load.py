import sys

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
