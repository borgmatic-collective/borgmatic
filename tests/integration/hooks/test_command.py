from flexmock import flexmock

from borgmatic.hooks import command as module


def test_interpolate_context_passes_through_command_without_variable():
    assert module.interpolate_context('pre-backup', 'ls', {'foo': 'bar'}) == 'ls'


def test_interpolate_context_warns_and_passes_through_command_with_unknown_variable():
    command = 'ls {baz}'
    flexmock(module.logger).should_receive('warning').once()

    assert module.interpolate_context('pre-backup', command, {'foo': 'bar'}) == command


def test_interpolate_context_does_not_warn_and_passes_through_command_with_unknown_variable_matching_borg_placeholder():
    command = 'ls {hostname}'
    flexmock(module.logger).should_receive('warning').never()

    assert module.interpolate_context('pre-backup', command, {'foo': 'bar'}) == command


def test_interpolate_context_interpolates_variables():
    command = 'ls {foo}{baz} {baz}'
    context = {'foo': 'bar', 'baz': 'quux'}

    assert module.interpolate_context('pre-backup', command, context) == 'ls barquux quux'


def test_interpolate_context_escapes_interpolated_variables():
    command = 'ls {foo} {inject}'
    context = {'foo': 'bar', 'inject': 'hi; naughty-command'}

    assert (
        module.interpolate_context('pre-backup', command, context) == "ls bar 'hi; naughty-command'"
    )


def test_interpolate_context_strips_backslashed_names_and_does_not_intepolate_them():
    command = r'ls \{foo\}\{baz\} \{baz\}'
    context = {'foo': 'bar', 'baz': 'quux'}

    assert module.interpolate_context('pre-backup', command, context) == 'ls {foo}{baz} {baz}'
