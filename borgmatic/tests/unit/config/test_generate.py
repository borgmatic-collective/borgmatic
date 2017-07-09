from collections import OrderedDict

from flexmock import flexmock

from borgmatic.config import generate as module


def test_schema_to_sample_configuration_generates_config_with_examples():
    flexmock(module.yaml.comments).should_receive('CommentedMap').replace_with(OrderedDict)
    flexmock(module).should_receive('add_comments_to_configuration')
    schema = {
        'map': OrderedDict([
            (
                'section1', {
                    'map': {
                        'field1': OrderedDict([
                            ('example', 'Example 1')
                        ]),
                    },
                },
            ),
            (
                'section2', {
                    'map': OrderedDict([
                        ('field2', {'example': 'Example 2'}),
                        ('field3', {'example': 'Example 3'}),
                    ]),
                }
            ),
        ])
    }

    config = module._schema_to_sample_configuration(schema)

    assert config == OrderedDict([
        (
            'section1',
            OrderedDict([
                ('field1', 'Example 1'),
            ]),
        ),
        (
            'section2',
            OrderedDict([
                ('field2', 'Example 2'),
                ('field3', 'Example 3'),
            ]),
        )
    ])
