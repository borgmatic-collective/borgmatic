import pkgutil

import borgmatic.actions
import borgmatic.config.load
import borgmatic.config.validate

MAXIMUM_LINE_LENGTH = 80


def test_schema_line_length_stays_under_limit():
    schema_file = open(borgmatic.config.validate.schema_filename())

    for line in schema_file.readlines():
        assert len(line.rstrip('\n')) <= MAXIMUM_LINE_LENGTH


ACTIONS_MODULE_NAMES_TO_OMIT = {
    'arguments',
    'change_passphrase',
    'export_key',
    'import_key',
    'json',
    'pattern',
}
ACTIONS_MODULE_NAMES_TO_ADD = {'key', 'umount'}


def test_schema_actions_correspond_to_supported_actions():
    '''
    Ensure that the allowed actions in the schema's various options don't drift from borgmatic's
    actual supported actions.
    '''
    schema = borgmatic.config.load.load_configuration(borgmatic.config.validate.schema_filename())
    supported_actions = {
        module.name.replace('_', '-')
        for module in pkgutil.iter_modules(borgmatic.actions.__path__)
        if module.name not in ACTIONS_MODULE_NAMES_TO_OMIT
    }.union(ACTIONS_MODULE_NAMES_TO_ADD)
    properties = schema['properties']
    commands_one_of = properties['commands']['items']['oneOf']

    for schema_actions in (
        set(properties['skip_actions']['items']['enum']),
        set(commands_one_of[0]['properties']['when']['items']['enum']),
        set(commands_one_of[1]['properties']['when']['items']['enum']),
    ):
        assert schema_actions == supported_actions
