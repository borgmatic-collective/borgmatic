import shlex
from argparse import Action
from textwrap import dedent

from borgmatic.commands import arguments


def upgrade_message(language: str, upgrade_command: str, completion_file: str):
    return f'''
Your {language} completions script is from a different version of borgmatic than is
currently installed. Please upgrade your script so your completions match the
command-line flags in your installed borgmatic! Try this to upgrade:

    {upgrade_command}
    source {completion_file}
'''


def parser_flags(parser):
    '''
    Given an argparse.ArgumentParser instance, return its argument flags in a space-separated
    string.
    '''
    return ' '.join(option for action in parser._actions for option in action.option_strings)


def bash_completion():
    '''
    Return a bash completion script for the borgmatic command. Produce this by introspecting
    borgmatic's command-line argument parsers.
    '''
    top_level_parser, subparsers = arguments.make_parsers()
    global_flags = parser_flags(top_level_parser)
    actions = ' '.join(subparsers.choices.keys())

    # Avert your eyes.
    return '\n'.join(
        (
            'check_version() {',
            '    local this_script="$(cat "$BASH_SOURCE" 2> /dev/null)"',
            '    local installed_script="$(borgmatic --bash-completion 2> /dev/null)"',
            '    if [ "$this_script" != "$installed_script" ] && [ "$installed_script" != "" ];'
            f'''        then cat << EOF\n{upgrade_message(
                    'bash',
                    'sudo sh -c "borgmatic --bash-completion > $BASH_SOURCE"',
                    '$BASH_SOURCE',
                )}\nEOF''',
            '    fi',
            '}',
            'complete_borgmatic() {',
        )
        + tuple(
            '''    if [[ " ${COMP_WORDS[*]} " =~ " %s " ]]; then
        COMPREPLY=($(compgen -W "%s %s %s" -- "${COMP_WORDS[COMP_CWORD]}"))
        return 0
    fi'''
            % (action, parser_flags(subparser), actions, global_flags)
            for action, subparser in subparsers.choices.items()
        )
        + (
            '    COMPREPLY=($(compgen -W "%s %s" -- "${COMP_WORDS[COMP_CWORD]}"))'  # noqa: FS003
            % (actions, global_flags),
            '    (check_version &)',
            '}',
            '\ncomplete -o bashdefault -o default -F complete_borgmatic borgmatic',
        )
    )


# fish section


def has_file_options(action: Action):
    return action.metavar in (
        'FILENAME',
        'PATH',
    ) or action.dest in ('config_paths',)


def has_choice_options(action: Action):
    return action.choices is not None


def has_required_param_options(action: Action):
    return (
        action.required is True
        or action.nargs
        in (
            '+',
            '*',
        )
        or '--archive' in action.option_strings
        or action.metavar in ('PATTERN', 'KEYS', 'N')
        or (action.type is not None and action.default is None)
    )


def has_exact_options(action: Action):
    return (
        has_file_options(action) or has_choice_options(action) or has_required_param_options(action)
    )


def exact_options_completion(action: Action):
    '''
    Given an argparse.Action instance, return a completion invocation
    that forces file completion or options completion, if the action
    takes such an argument and was the last action on the command line.

    Otherwise, return an empty string.
    '''

    if not has_exact_options(action):
        return ''

    args = ' '.join(action.option_strings)

    if has_file_options(action):
        return f'''\ncomplete -c borgmatic -Fr -n "__borgmatic_last_arg {args}"'''

    if has_choice_options(action):
        return f'''\ncomplete -c borgmatic -f -a '{' '.join(map(str, action.choices))}' -n "__borgmatic_last_arg {args}"'''

    if has_required_param_options(action):
        return f'''\ncomplete -c borgmatic -x -n "__borgmatic_last_arg {args}"'''

    raise RuntimeError(
        f'Unexpected action: {action} passes has_exact_options but has no choices produced'
    )


def dedent_strip_as_tuple(string: str):
    return (dedent(string).strip('\n'),)


def fish_completion():
    '''
    Return a fish completion script for the borgmatic command. Produce this by introspecting
    borgmatic's command-line argument parsers.
    '''
    top_level_parser, subparsers = arguments.make_parsers()

    all_subparsers = ' '.join(action for action in subparsers.choices.keys())

    exact_option_args = tuple(
        ' '.join(action.option_strings)
        for subparser in subparsers.choices.values()
        for action in subparser._actions
        if has_exact_options(action)
    ) + tuple(
        ' '.join(action.option_strings)
        for action in top_level_parser._actions
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
                            echo "{upgrade_message(
                            'fish',
                            'borgmatic --fish-completion | sudo tee $this_filename',
                            '$this_filename',
                        )}"
                        end
                    end
                ' &
            end
            __borgmatic_check_version

            function __borgmatic_last_arg --description 'Check if any of the given arguments are the last on the command line'
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

            set --local subparser_condition "not __fish_seen_subcommand_from {all_subparsers}"
            set --local exact_option_condition "not __borgmatic_last_arg {' '.join(exact_option_args)}"
            '''
        )
        + ('\n# subparser completions',)
        + tuple(
            f'''complete -c borgmatic -f -n "$subparser_condition" -n "$exact_option_condition" -a '{action_name}' -d {shlex.quote(subparser.description)}'''
            for action_name, subparser in subparsers.choices.items()
        )
        + ('\n# global flags',)
        + tuple(
            f'''complete -c borgmatic -f -n "$exact_option_condition" -a '{' '.join(action.option_strings)}' -d {shlex.quote(action.help)}{exact_options_completion(action)}'''
            for action in top_level_parser._actions
            if len(action.option_strings) > 0
            if 'Deprecated' not in action.help
        )
        + ('\n# subparser flags',)
        + tuple(
            f'''complete -c borgmatic -f -n "$exact_option_condition" -a '{' '.join(action.option_strings)}' -d {shlex.quote(action.help)} -n "__fish_seen_subcommand_from {action_name}"{exact_options_completion(action)}'''
            for action_name, subparser in subparsers.choices.items()
            for action in subparser._actions
            if 'Deprecated' not in action.help
        )
    )
