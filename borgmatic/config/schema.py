import itertools


def get_properties(schema):
    '''
    Given a schema dict, return its properties. But if it's got sub-schemas with multiple different
    potential properties, returned their merged properties instead (interleaved so the first
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
