from flexmock import flexmock

from borgmatic.borg import flags as module


def test_make_flags_formats_string_value():
    assert module.make_flags('foo', 'bar') == ('--foo', 'bar')


def test_make_flags_formats_integer_value():
    assert module.make_flags('foo', 3) == ('--foo', '3')


def test_make_flags_formats_true_value():
    assert module.make_flags('foo', True) == ('--foo',)


def test_make_flags_omits_false_value():
    assert module.make_flags('foo', False) == ()


def test_make_flags_formats_name_with_underscore():
    assert module.make_flags('posix_me_harder', 'okay') == ('--posix-me-harder', 'okay')


def test_make_flags_from_arguments_flattens_and_sorts_multiple_arguments():
    flexmock(module).should_receive('make_flags').with_args('foo', 'bar').and_return(('foo', 'bar'))
    flexmock(module).should_receive('make_flags').with_args('baz', 'quux').and_return(
        ('baz', 'quux')
    )
    arguments = flexmock(foo='bar', baz='quux')

    assert module.make_flags_from_arguments(arguments) == ('baz', 'quux', 'foo', 'bar')


def test_make_flags_from_arguments_excludes_underscored_argument_names():
    flexmock(module).should_receive('make_flags').with_args('foo', 'bar').and_return(('foo', 'bar'))
    arguments = flexmock(foo='bar', _baz='quux')

    assert module.make_flags_from_arguments(arguments) == ('foo', 'bar')


def test_make_flags_from_arguments_omits_excludes():
    flexmock(module).should_receive('make_flags').with_args('foo', 'bar').and_return(('foo', 'bar'))
    arguments = flexmock(foo='bar', baz='quux')

    assert module.make_flags_from_arguments(arguments, excludes=('baz', 'other')) == ('foo', 'bar')
