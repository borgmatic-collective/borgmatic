import pkgutil

import borgmatic.actions
import borgmatic.config.load
import borgmatic.config.validate

MAXIMUM_LINE_LENGTH = 80


def test_schema_line_length_stays_under_limit():
    schema_file = open(borgmatic.config.validate.schema_filename())

    for line in schema_file.readlines():
        assert len(line.rstrip('\n')) <= MAXIMUM_LINE_LENGTH


ACTIONS_MODULE_NAMES_TO_OMIT = {'arguments', 'change_passphrase', 'export_key', 'json'}
ACTIONS_MODULE_NAMES_TO_ADD = {'key', 'umount'}


def test_schema_skip_actions_correspond_to_supported_actions():
    '''
    Ensure that the allowed actions in the schema's "skip_actions" option don't drift from
    borgmatic's actual supported actions.
    '''
    schema = borgmatic.config.load.load_configuration(borgmatic.config.validate.schema_filename())
    schema_skip_actions = set(schema['properties']['skip_actions']['items']['enum'])
    supported_actions = {
        module.name.replace('_', '-')
        for module in pkgutil.iter_modules(borgmatic.actions.__path__)
        if module.name not in ACTIONS_MODULE_NAMES_TO_OMIT
    }.union(ACTIONS_MODULE_NAMES_TO_ADD)

    assert schema_skip_actions == supported_actions
