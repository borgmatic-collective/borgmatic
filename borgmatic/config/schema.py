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


SCHEMA_TYPE_TO_PYTHON_TYPE = {
    'array': list,
    'boolean': bool,
    'integer': int,
    'number': decimal.Decimal,
    'object': dict,
    'string': str,
}


def parse_type(schema_type, **overrides):
    '''
    Given a schema type as a string, return the corresponding Python type.

    If any overrides are given in the from of a schema type string to a Python type, then override
    the default type mapping with them.

    Raise ValueError if the schema type is unknown.
    '''
    try:
        return dict(
            SCHEMA_TYPE_TO_PYTHON_TYPE,
            **overrides,
        )[schema_type]
    except KeyError:
        raise ValueError(f'Unknown type in configuration schema: {schema_type}')


def compare_types(schema_type, target_types, match=any):
    '''
    Given a schema type as a string or a list of strings (representing multiple types) and a set of
    target type strings, return whether every schema type is in the set of target types.

    If the schema type is a list of strings, use the given match function (such as any or all) to
    compare elements. For instance, if match is given as all, then every element of the schema_type
    list must be in the target types.
    '''
    if isinstance(schema_type, list):
        if match(element_schema_type in target_types for element_schema_type in schema_type):
            return True

        return False

    if schema_type in target_types:
        return True

    return False
