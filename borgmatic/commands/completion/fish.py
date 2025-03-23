import shlex
from argparse import Action
from textwrap import dedent

import borgmatic.commands.arguments
import borgmatic.commands.completion.actions
import borgmatic.config.validate


def has_file_options(action: Action):
    '''
    Given an argparse.Action instance, return True if it takes a file argument.
    '''
    return action.metavar in (
        'FILENAME',
        'PATH',
    ) or action.dest in ('config_paths',)


def has_choice_options(action: Action):
    '''
    Given an argparse.Action instance, return True if it takes one of a predefined set of arguments.
    '''
    return action.choices is not None


def has_unknown_required_param_options(action: Action):
    '''
    A catch-all for options that take a required parameter, but we don't know what the parameter is.
    This should be used last. These are actions that take something like a glob, a list of numbers,
    or a string.

    Actions that match this pattern should not show the normal arguments, because those are unlikely
    to be valid.
    '''
    return (
        action.required is True
        or action.nargs
        in (
            '+',
            '*',
        )
        or action.metavar in ('PATTERN', 'KEYS', 'N')
        or (action.type is not None and action.default is None)
    )


def has_exact_options(action: Action):
    return (
        has_file_options(action)
        or has_choice_options(action)
        or has_unknown_required_param_options(action)
    )


def exact_options_completion(action: Action):
    '''
    Given an argparse.Action instance, return a completion invocation that forces file completions,
    options completion, or just that some value follow the action, if the action takes such an
    argument and was the last action on the command line prior to the cursor.

    Otherwise, return an empty string.
    '''

    if not has_exact_options(action):
        return ''

    args = ' '.join(action.option_strings)

    if has_file_options(action):
        return f'''\ncomplete -c borgmatic -Fr -n "__borgmatic_current_arg {args}"'''

    if has_choice_options(action):
        return f'''\ncomplete -c borgmatic -f -a '{' '.join(map(str, action.choices))}' -n "__borgmatic_current_arg {args}"'''

    if has_unknown_required_param_options(action):
        return f'''\ncomplete -c borgmatic -x -n "__borgmatic_current_arg {args}"'''

    raise ValueError(
        f'Unexpected action: {action} passes has_exact_options but has no choices produced'
    )


def dedent_strip_as_tuple(string: str):
    '''
    Dedent a string, then strip it to avoid requiring your first line to have content, then return a
    tuple of the string. Makes it easier to write multiline strings for completions when you join
    them with a tuple.
    '''
    return (dedent(string).strip('\n'),)


def fish_completion():
    '''
    Return a fish completion script for the borgmatic command. Produce this by introspecting
    borgmatic's command-line argument parsers.
    '''
    (
        unused_global_parser,
        action_parsers,
        global_plus_action_parser,
    ) = borgmatic.commands.arguments.make_parsers(
        schema=borgmatic.config.validate.load_schema(borgmatic.config.validate.schema_filename()),
        unparsed_arguments=(),
    )

    all_action_parsers = ' '.join(action for action in action_parsers.choices.keys())

    exact_option_args = tuple(
        ' '.join(action.option_strings)
        for action_parser in action_parsers.choices.values()
        for action in action_parser._actions
        if has_exact_options(action)
    ) + tuple(
        ' '.join(action.option_strings)
        for action in global_plus_action_parser._actions
        if len(action.option_strings) > 0
        if has_exact_options(action)
    )

    # Avert your eyes.
    return '\n'.join(
        dedent_strip_as_tuple(
            f'''
            function __borgmatic_check_version
                set -fx this_filename (status current-filename)
                fish -c '
                    if test -f "$this_filename"
                        set this_script (cat $this_filename 2> /dev/null)
                        set installed_script (borgmatic --fish-completion 2> /dev/null)
                        if [ "$this_script" != "$installed_script" ] && [ "$installed_script" != "" ]
                            echo "{borgmatic.commands.completion.actions.upgrade_message(
                            'fish',
                            'borgmatic --fish-completion | sudo tee $this_filename',
                            '$this_filename',
                        )}"
                        end
                    end
                ' &
            end
            __borgmatic_check_version

            function __borgmatic_current_arg --description 'Check if any of the given arguments are the last on the command line before the cursor'
                set -l all_args (commandline -poc)
                # premature optimization to avoid iterating all args if there aren't enough
                # to have a last arg beyond borgmatic
                if [ (count $all_args) -lt 2 ]
                    return 1
                end
                for arg in $argv
                    if [ "$arg" = "$all_args[-1]" ]
                        return 0
                    end
                end
                return 1
            end

            set --local action_parser_condition "not __fish_seen_subcommand_from {all_action_parsers}"
            set --local exact_option_condition "not __borgmatic_current_arg {' '.join(exact_option_args)}"
            '''
        )
        + ('\n# action_parser completions',)
        + tuple(
            f'''complete -c borgmatic -f -n "$action_parser_condition" -n "$exact_option_condition" -a '{action_name}' -d {shlex.quote(action_parser.description)}'''
            for action_name, action_parser in action_parsers.choices.items()
        )
        + ('\n# global flags',)
        + tuple(
            # -n is checked in order, so put faster / more likely to be true checks first
            f'''complete -c borgmatic -f -n "$exact_option_condition" -a '{' '.join(action.option_strings)}' -d {shlex.quote(action.help)}{exact_options_completion(action)}'''
            for action in global_plus_action_parser._actions
            # ignore the noargs action, as this is an impossible completion for fish
            if len(action.option_strings) > 0
            if 'Deprecated' not in action.help
        )
        + ('\n# action_parser flags',)
        + tuple(
            f'''complete -c borgmatic -f -n "$exact_option_condition" -a '{' '.join(action.option_strings)}' -d {shlex.quote(action.help)} -n "__fish_seen_subcommand_from {action_name}"{exact_options_completion(action)}'''
            for action_name, action_parser in action_parsers.choices.items()
            for action in action_parser._actions
            if 'Deprecated' not in (action.help or ())
        )
    )
