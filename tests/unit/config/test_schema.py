import pytest

from borgmatic.config import schema as module


def test_get_properties_with_simple_object():
    schema = {
        'type': 'object',
        'properties': dict(
            [
                ('field1', {'example': 'Example'}),
            ],
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
                    ],
                ),
            },
            {
                'properties': dict(
                    [
                        ('field2', {'example': 'Example 2'}),
                        ('field3', {'example': 'Example 3'}),
                    ],
                ),
            },
        ],
    }

    assert module.get_properties(schema) == dict(
        schema['oneOf'][0]['properties'],
        **schema['oneOf'][1]['properties'],
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
                    ],
                ),
            },
            {
                'properties': dict(
                    [
                        ('field4', {'example': 'Example 4'}),
                        ('field5', {'example': 'Example 5'}),
                    ],
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
        ],
    )


def test_parse_type_maps_schema_type_to_python_type():
    assert module.parse_type('boolean') is bool


def test_parse_type_with_unknown_schema_type_raises():
    with pytest.raises(ValueError):
        module.parse_type('what')


def test_parse_type_respect_overrides_when_mapping_types():
    assert module.parse_type('boolean', boolean=int) is int


@pytest.mark.parametrize(
    'schema_type,target_types,match,expected_result',
    (
        (
            'string',
            {'integer', 'string', 'boolean'},
            None,
            True,
        ),
        (
            'string',
            {'integer', 'boolean'},
            None,
            False,
        ),
        (
            'string',
            {'integer', 'string', 'boolean'},
            all,
            True,
        ),
        (
            'string',
            {'integer', 'boolean'},
            all,
            False,
        ),
        (
            ['string', 'array'],
            {'integer', 'string', 'boolean'},
            None,
            True,
        ),
        (
            ['string', 'array'],
            {'integer', 'boolean'},
            None,
            False,
        ),
        (
            ['string', 'array'],
            {'integer', 'string', 'boolean', 'array'},
            all,
            True,
        ),
        (
            ['string', 'array'],
            {'integer', 'string', 'boolean'},
            all,
            False,
        ),
        (
            ['string', 'array'],
            {'integer', 'boolean'},
            all,
            False,
        ),
    ),
)
def test_compare_types_returns_whether_schema_type_matches_target_types(
    schema_type,
    target_types,
    match,
    expected_result,
):
    if match:
        assert module.compare_types(schema_type, target_types, match) == expected_result
    else:
        assert module.compare_types(schema_type, target_types) == expected_result
