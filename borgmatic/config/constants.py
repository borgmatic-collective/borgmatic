def coerce_scalar(value):
    '''
    Given a configuration value, coerce it to an integer or a boolean as appropriate and return the
    result.
    '''
    try:
        return int(value)
    except (TypeError, ValueError):
        pass

    if value == 'true' or value == 'True':
        return True
    if value == 'false' or value == 'False':
        return False

    return value


def apply_constants(value, constants):
    '''
    Given a configuration value (bool, dict, int, list, or string) and a dict of named constants,
    replace any configuration string values of the form "{constant}" (or containing it) with the
    value of the correspondingly named key from the constants. Recurse as necessary into nested
    configuration to find values to replace.

    For instance, if a configuration value contains "{foo}", replace it with the value of the "foo"
    key found within the configuration's "constants".

    Return the configuration value and modify the original.
    '''
    if not value or not constants:
        return value

    if isinstance(value, str):
        for constant_name, constant_value in constants.items():
            value = value.replace('{' + constant_name + '}', str(constant_value))

        # Support constants within non-string scalars by coercing the value to its appropriate type.
        value = coerce_scalar(value)
    elif isinstance(value, list):
        for index, list_value in enumerate(value):
            value[index] = apply_constants(list_value, constants)
    elif isinstance(value, dict):
        for option_name, option_value in value.items():
            value[option_name] = apply_constants(option_value, constants)

    return value
