import borgmatic.commands.arguments


def upgrade_message(language: str, upgrade_command: str, completion_file: str):
    return f'''
Your {language} completions script is from a different version of borgmatic than is
currently installed. Please upgrade your script so your completions match the
command-line flags in your installed borgmatic! Try this to upgrade:

    {upgrade_command}
    source {completion_file}
'''


def available_actions(subparsers, current_action=None):
    '''
    Given subparsers as an argparse._SubParsersAction instance and a current action name (if
    any), return the actions names that can follow the current action on a command-line.

    This takes into account which sub-actions that the current action supports. For instance, if
    "bootstrap" is a sub-action for "config", then "bootstrap" should be able to follow a current
    action of "config" but not "list".
    '''
    action_to_subactions = borgmatic.commands.arguments.get_subactions_for_actions(
        subparsers.choices
    )
    current_subactions = action_to_subactions.get(current_action)

    if current_subactions:
        return current_subactions

    all_subactions = set(
        subaction for subactions in action_to_subactions.values() for subaction in subactions
    )

    return tuple(action for action in subparsers.choices.keys() if action not in all_subactions)
