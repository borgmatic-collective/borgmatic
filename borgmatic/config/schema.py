import decimal
import itertools


def get_properties(schema):
    '''
    Given a schema dict, return its properties. But if it's got sub-schemas with multiple different
    potential properties, return their merged properties instead (interleaved so the first
    properties of each sub-schema come first). The idea is that the user should see all possible
    options even if they're not all possible together.
    '''
    if 'oneOf' in schema:
        return dict(
            item
            for item in itertools.chain(
                *itertools.zip_longest(
                    *[sub_schema['properties'].items() for sub_schema in schema['oneOf']]
                )
            )
            if item is not None
        )

    return schema.get('properties', {})


def parse_type(schema_type):
    '''
    Given a schema type as a string, return the corresponding Python type.

    Raise ValueError if the schema type is unknown.
    '''
    try:
        return {
            'string': str,
            'integer': int,
            'number': decimal.Decimal,
            'boolean': bool,
            'array': str,
        }[schema_type]
    except KeyError:
        raise ValueError(f'Unknown type in configuration schema: {schema_type}')
