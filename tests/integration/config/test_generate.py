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

    assert module._comment_out_line(line) == '# ' + line


def test_comment_out_line_comments_indented_option():
    line = '    enabled: true'

    assert module._comment_out_line(line) == '    # enabled: true'


def test_comment_out_line_comments_twice_indented_option():
    line = '        - item'

    assert module._comment_out_line(line) == '        # - item'


def test_comment_out_optional_configuration_comments_optional_config_only():
    # The "# COMMENT_OUT" comment is a sentinel used to express that the following key is optional.
    # It's stripped out of the final output.
    flexmock(module)._comment_out_line = lambda line: '# ' + line
    config = '''
# COMMENT_OUT
foo:
    # COMMENT_OUT
    bar:
        - baz
        - quux

location:
    repositories:
        - one
        - two

    # This comment should be kept.
    # COMMENT_OUT
    other: thing
    '''

    # flake8: noqa
    expected_config = '''
# foo:
#     bar:
#         - baz
#         - quux

location:
    repositories:
        - one
        - two

    # This comment should be kept.
#     other: thing
    '''

    assert module._comment_out_optional_configuration(config.strip()) == expected_config.strip()


def test_render_configuration_converts_configuration_to_yaml_string():
    yaml_string = module.render_configuration({'foo': 'bar'})

    assert yaml_string == 'foo: bar\n'


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


def test_write_configuration_with_already_existing_file_and_overwrite_does_not_raise():
    flexmock(os.path).should_receive('exists').and_return(True)

    module.write_configuration('/tmp/config.yaml', 'config: yaml', overwrite=True)


def test_write_configuration_with_already_existing_directory_does_not_raise():
    flexmock(os.path).should_receive('exists').and_return(False)
    flexmock(os).should_receive('makedirs').and_raise(FileExistsError)
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').and_return(StringIO())
    flexmock(os).should_receive('chmod')

    module.write_configuration('config.yaml', 'config: yaml')


def test_add_comments_to_configuration_sequence_of_strings_does_not_raise():
    config = module.yaml.comments.CommentedSeq(['foo', 'bar'])
    schema = {'type': 'array', 'items': {'type': 'string'}}

    module.add_comments_to_configuration_sequence(config, schema)


def test_add_comments_to_configuration_sequence_of_maps_does_not_raise():
    config = module.yaml.comments.CommentedSeq([module.yaml.comments.CommentedMap([('foo', 'yo')])])
    schema = {
        'type': 'array',
        'items': {'type': 'object', 'properties': {'foo': {'description': 'yo'}}},
    }

    module.add_comments_to_configuration_sequence(config, schema)


def test_add_comments_to_configuration_sequence_of_maps_without_description_does_not_raise():
    config = module.yaml.comments.CommentedSeq([module.yaml.comments.CommentedMap([('foo', 'yo')])])
    schema = {'type': 'array', 'items': {'type': 'object', 'properties': {'foo': {}}}}

    module.add_comments_to_configuration_sequence(config, schema)


def test_add_comments_to_configuration_object_does_not_raise():
    # Ensure that it can deal with fields both in the schema and missing from the schema.
    config = module.yaml.comments.CommentedMap([('foo', 33), ('bar', 44), ('baz', 55)])
    schema = {
        'type': 'object',
        'properties': {'foo': {'description': 'Foo'}, 'bar': {'description': 'Bar'}},
    }

    module.add_comments_to_configuration_object(config, schema)


def test_add_comments_to_configuration_object_with_skip_first_does_not_raise():
    config = module.yaml.comments.CommentedMap([('foo', 33)])
    schema = {'type': 'object', 'properties': {'foo': {'description': 'Foo'}}}

    module.add_comments_to_configuration_object(config, schema, skip_first=True)


def test_remove_commented_out_sentinel_keeps_other_comments():
    field_name = 'foo'
    config = module.yaml.comments.CommentedMap([(field_name, 33)])
    config.yaml_set_comment_before_after_key(key=field_name, before='Actual comment.\nCOMMENT_OUT')

    module.remove_commented_out_sentinel(config, field_name)

    comments = config.ca.items[field_name][module.RUAMEL_YAML_COMMENTS_INDEX]
    assert len(comments) == 1
    assert comments[0].value == '# Actual comment.\n'


def test_remove_commented_out_sentinel_without_sentinel_keeps_other_comments():
    field_name = 'foo'
    config = module.yaml.comments.CommentedMap([(field_name, 33)])
    config.yaml_set_comment_before_after_key(key=field_name, before='Actual comment.')

    module.remove_commented_out_sentinel(config, field_name)

    comments = config.ca.items[field_name][module.RUAMEL_YAML_COMMENTS_INDEX]
    assert len(comments) == 1
    assert comments[0].value == '# Actual comment.\n'


def test_remove_commented_out_sentinel_on_unknown_field_does_not_raise():
    field_name = 'foo'
    config = module.yaml.comments.CommentedMap([(field_name, 33)])
    config.yaml_set_comment_before_after_key(key=field_name, before='Actual comment.')

    module.remove_commented_out_sentinel(config, 'unknown')


def test_generate_sample_configuration_does_not_raise():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('schema.yaml').and_return('')
    flexmock(module.yaml).should_receive('round_trip_load')
    flexmock(module).should_receive('_schema_to_sample_configuration')
    flexmock(module).should_receive('merge_source_configuration_into_destination')
    flexmock(module).should_receive('render_configuration')
    flexmock(module).should_receive('_comment_out_optional_configuration')
    flexmock(module).should_receive('write_configuration')

    module.generate_sample_configuration(None, 'dest.yaml', 'schema.yaml')


def test_generate_sample_configuration_with_source_filename_does_not_raise():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('schema.yaml').and_return('')
    flexmock(module.yaml).should_receive('round_trip_load')
    flexmock(module.load).should_receive('load_configuration')
    flexmock(module.normalize).should_receive('normalize')
    flexmock(module).should_receive('_schema_to_sample_configuration')
    flexmock(module).should_receive('merge_source_configuration_into_destination')
    flexmock(module).should_receive('render_configuration')
    flexmock(module).should_receive('_comment_out_optional_configuration')
    flexmock(module).should_receive('write_configuration')

    module.generate_sample_configuration('source.yaml', 'dest.yaml', 'schema.yaml')
