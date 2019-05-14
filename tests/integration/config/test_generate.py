import os
import sys
from io import StringIO

import pytest
from flexmock import flexmock

from borgmatic.config import generate as module


def test_insert_newline_before_comment_does_not_raise():
    field_name = 'foo'
    config = module.yaml.comments.CommentedMap([(field_name, 33)])
    config.yaml_set_comment_before_after_key(key=field_name, before='Comment')

    module._insert_newline_before_comment(config, field_name)


def test_comment_out_line_skips_blank_line():
    line = '    \n'

    assert module._comment_out_line(line) == line


def test_comment_out_line_skips_already_commented_out_line():
    line = '    # foo'

    assert module._comment_out_line(line) == line


def test_comment_out_line_comments_section_name():
    line = 'figgy-pudding:'

    assert module._comment_out_line(line) == '#' + line


def test_comment_out_line_comments_indented_option():
    line = '    enabled: true'

    assert module._comment_out_line(line) == '    #enabled: true'


def test_comment_out_optional_configuration_comments_optional_config_only():
    flexmock(module)._comment_out_line = lambda line: '#' + line
    config = '''
foo:
    bar:
        - baz
        - quux

location:
    repositories:
        - one
        - two

    other: thing
    '''

    expected_config = '''
#foo:
#    bar:
#        - baz
#        - quux
#
location:
    repositories:
        - one
        - two
#
#    other: thing
    '''

    assert module._comment_out_optional_configuration(config.strip()) == expected_config.strip()


def test_render_configuration_does_not_raise():
    flexmock(module.yaml).should_receive('round_trip_dump')

    module._render_configuration({})


def test_write_configuration_does_not_raise():
    flexmock(os.path).should_receive('exists').and_return(False)
    flexmock(os).should_receive('makedirs')
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').and_return(StringIO())
    flexmock(os).should_receive('chmod')

    module.write_configuration('config.yaml', 'config: yaml')


def test_write_configuration_with_already_existing_file_raises():
    flexmock(os.path).should_receive('exists').and_return(True)

    with pytest.raises(FileExistsError):
        module.write_configuration('config.yaml', 'config: yaml')


def test_write_configuration_with_already_existing_directory_does_not_raise():
    flexmock(os.path).should_receive('exists').and_return(False)
    flexmock(os).should_receive('makedirs').and_raise(FileExistsError)
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').and_return(StringIO())
    flexmock(os).should_receive('chmod')

    module.write_configuration('config.yaml', 'config: yaml')


def test_add_comments_to_configuration_does_not_raise():
    # Ensure that it can deal with fields both in the schema and missing from the schema.
    config = module.yaml.comments.CommentedMap([('foo', 33), ('bar', 44), ('baz', 55)])
    schema = {'map': {'foo': {'desc': 'Foo'}, 'bar': {'desc': 'Bar'}}}

    module.add_comments_to_configuration(config, schema)


def test_generate_sample_configuration_does_not_raise():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('schema.yaml').and_return('')
    flexmock(module).should_receive('_schema_to_sample_configuration')
    flexmock(module).should_receive('_render_configuration')
    flexmock(module).should_receive('_comment_out_optional_configuration')
    flexmock(module).should_receive('write_configuration')

    module.generate_sample_configuration('config.yaml', 'schema.yaml')
