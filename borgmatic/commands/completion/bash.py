import borgmatic.commands.arguments
import borgmatic.commands.completion.actions
import borgmatic.commands.completion.flag
import borgmatic.config.validate


def parser_flags(parser):
    '''
    Given an argparse.ArgumentParser instance, return its argument flags in a space-separated
    string.
    '''
    return ' '.join(
        flag_variant
        for action in parser._actions
        for flag_name in action.option_strings
        for flag_variant in borgmatic.commands.completion.flag.variants(flag_name)
    )


def bash_completion():
    '''
    Return a bash completion script for the borgmatic command. Produce this by introspecting
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
    global_flags = parser_flags(global_plus_action_parser)

    # Avert your eyes.
    return '\n'.join(
        (
            'check_version() {',
            '    local this_script="$(cat "$BASH_SOURCE" 2> /dev/null)"',
            '    local installed_script="$(borgmatic --bash-completion 2> /dev/null)"',
            '    if [ "$this_script" != "$installed_script" ] && [ "$installed_script" != "" ];'
            f'''        then cat << EOF\n{borgmatic.commands.completion.actions.upgrade_message(
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
            % (
                action,
                parser_flags(action_parser),
                ' '.join(
                    borgmatic.commands.completion.actions.available_actions(action_parsers, action)
                ),
                global_flags,
            )
            for action, action_parser in reversed(action_parsers.choices.items())
        )
        + (
            '    COMPREPLY=($(compgen -W "%s %s" -- "${COMP_WORDS[COMP_CWORD]}"))'  # noqa: FS003
            % (
                ' '.join(borgmatic.commands.completion.actions.available_actions(action_parsers)),
                global_flags,
            ),
            '    (check_version &)',
            '}',
            '\ncomplete -o bashdefault -o default -F complete_borgmatic borgmatic',
        )
    )
