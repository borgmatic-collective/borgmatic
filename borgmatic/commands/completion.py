import shlex
from argparse import Action

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
            '        then cat << EOF\n{}\nEOF'.format(
                upgrade_message(
                    'bash',
                    'sudo sh -c "borgmatic --bash-completion > $BASH_SOURCE"',
                    '$BASH_SOURCE',
                )
            ),
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


def build_fish_flags(action: Action):
    '''
    Given an argparse.Action instance, return a string containing the fish flags for that action.
    '''
    if action.metavar and action.metavar == 'PATH' or action.metavar == 'FILENAME':
        return '-r -F'
    else:
        return '-f'


def fish_completion():
    '''
    Return a fish completion script for the borgmatic command. Produce this by introspecting
    borgmatic's command-line argument parsers.
    '''
    top_level_parser, subparsers = arguments.make_parsers()

    all_subparsers = ' '.join(action for action in subparsers.choices.keys())

    # Avert your eyes.
    return '\n'.join(
        (
            'function __borgmatic_check_version',
            '    set this_filename (status current-filename)',
            '    set this_script (cat $this_filename 2> /dev/null)',
            '    set installed_script (borgmatic --fish-completion 2> /dev/null)',
            '    if [ "$this_script" != "$installed_script" ] && [ "$installed_script" != "" ]',
            '        echo "{}"'.format(
                upgrade_message(
                    'fish',
                    'borgmatic --fish-completion | sudo tee $this_filename',
                    '$this_filename',
                )
            ),
            '    end',
            'end',
            '__borgmatic_check_version &',
        )
        + ('\n# subparser completions',)
        + tuple(
            '''complete -c borgmatic -a '%s' -d %s -f -n "not __fish_seen_subcommand_from %s"'''
            % (action_name, shlex.quote(subparser.description), all_subparsers)
            for action_name, subparser in subparsers.choices.items()
        )
        + ('\n# global flags',)
        + tuple(
            '''complete -c borgmatic -a '%s' -d %s %s'''
            % (' '.join(action.option_strings), shlex.quote(action.help), build_fish_flags(action))
            for action in top_level_parser._actions
        )
        + ('\n# subparser flags',)
        + tuple(
            '''complete -c borgmatic -a '%s' -d %s -n "__fish_seen_subcommand_from %s" %s'''
            % (
                ' '.join(action.option_strings),
                shlex.quote(action.help),
                action_name,
                build_fish_flags(action),
            )
            for action_name, subparser in subparsers.choices.items()
            for action in subparser._actions
        )
    )
