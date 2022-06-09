from borgmatic.commands import arguments

UPGRADE_MESSAGE = '''
Your bash completions script is from a different version of borgmatic than is
currently installed. Please upgrade your script so your completions match the
command-line flags in your installed borgmatic! Try this to upgrade:

    sudo sh -c "borgmatic --bash-completion > $BASH_SOURCE"
    source $BASH_SOURCE
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
            '        then cat << EOF\n%s\nEOF' % UPGRADE_MESSAGE,
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
            '    COMPREPLY=($(compgen -W "%s %s" -- "${COMP_WORDS[COMP_CWORD]}"))'
            % (actions, global_flags),
            '    (check_version &)',
            '}',
            '\ncomplete -o bashdefault -o default -F complete_borgmatic borgmatic',
        )
    )
