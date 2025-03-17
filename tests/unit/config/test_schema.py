from borgmatic.config import schema as module


def test_get_properties_with_simple_object():
    schema = {
        'type': 'object',
        'properties': dict(
            [
                ('field1', {'example': 'Example'}),
            ]
        ),
    }

    assert module.get_properties(schema) == schema['properties']


def test_get_properties_merges_oneof_list_properties():
    schema = {
        'type': 'object',
        'oneOf': [
            {
                'properties': dict(
                    [
                        ('field1', {'example': 'Example 1'}),
                        ('field2', {'example': 'Example 2'}),
                    ]
                ),
            },
            {
                'properties': dict(
                    [
                        ('field2', {'example': 'Example 2'}),
                        ('field3', {'example': 'Example 3'}),
                    ]
                ),
            },
        ],
    }

    assert module.get_properties(schema) == dict(
        schema['oneOf'][0]['properties'], **schema['oneOf'][1]['properties']
    )


def test_get_properties_interleaves_oneof_list_properties():
    schema = {
        'type': 'object',
        'oneOf': [
            {
                'properties': dict(
                    [
                        ('field1', {'example': 'Example 1'}),
                        ('field2', {'example': 'Example 2'}),
                        ('field3', {'example': 'Example 3'}),
                    ]
                ),
            },
            {
                'properties': dict(
                    [
                        ('field4', {'example': 'Example 4'}),
                        ('field5', {'example': 'Example 5'}),
                    ]
                ),
            },
        ],
    }

    assert module.get_properties(schema) == dict(
        [
            ('field1', {'example': 'Example 1'}),
            ('field4', {'example': 'Example 4'}),
            ('field2', {'example': 'Example 2'}),
            ('field5', {'example': 'Example 5'}),
            ('field3', {'example': 'Example 3'}),
        ]
    )



