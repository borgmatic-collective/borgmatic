import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.actions import pattern as module
from borgmatic.borg.pattern import Pattern, Pattern_source, Pattern_style, Pattern_type


@pytest.mark.parametrize(
    'pattern_line,expected_pattern',
    (
        ('R /foo', Pattern('/foo', source=Pattern_source.CONFIG)),
        ('P sh', Pattern('sh', Pattern_type.PATTERN_STYLE, source=Pattern_source.CONFIG)),
        ('+ /foo*', Pattern('/foo*', Pattern_type.INCLUDE, source=Pattern_source.CONFIG)),
        (
            '+ sh:/foo*',
            Pattern(
                '/foo*',
                Pattern_type.INCLUDE,
                Pattern_style.SHELL,
                source=Pattern_source.CONFIG,
            ),
        ),
    ),
)
def test_parse_pattern_transforms_pattern_line_to_instance(pattern_line, expected_pattern):
    assert module.parse_pattern(pattern_line) == expected_pattern


def test_parse_pattern_with_invalid_pattern_line_errors():
    with pytest.raises(ValueError):
        module.parse_pattern('/foo')


def test_collect_patterns_converts_source_directories():
    assert module.collect_patterns({'source_directories': ['/foo', '/bar']}) == (
        Pattern('/foo', source=Pattern_source.CONFIG),
        Pattern('/bar', source=Pattern_source.CONFIG),
    )


def test_collect_patterns_parses_config_patterns():
    flexmock(module).should_receive('parse_pattern').with_args('R /foo').and_return(Pattern('/foo'))
    flexmock(module).should_receive('parse_pattern').with_args('# comment').never()
    flexmock(module).should_receive('parse_pattern').with_args('').never()
    flexmock(module).should_receive('parse_pattern').with_args('   ').never()
    flexmock(module).should_receive('parse_pattern').with_args('R /bar').and_return(Pattern('/bar'))

    assert module.collect_patterns({'patterns': ['R /foo', '# comment', '', '   ', 'R /bar']}) == (
        Pattern('/foo'),
        Pattern('/bar'),
    )


def test_collect_patterns_converts_exclude_patterns():
    assert module.collect_patterns({'exclude_patterns': ['/foo', '/bar', 'sh:**/baz']}) == (
        Pattern(
            '/foo',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
            source=Pattern_source.CONFIG,
        ),
        Pattern(
            '/bar',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
            source=Pattern_source.CONFIG,
        ),
        Pattern(
            '**/baz',
            Pattern_type.NO_RECURSE,
            Pattern_style.SHELL,
            source=Pattern_source.CONFIG,
        ),
    )


def test_collect_patterns_reads_config_patterns_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt', encoding='utf-8').and_return(
        io.StringIO('R /foo')
    )
    builtins.should_receive('open').with_args('file2.txt', encoding='utf-8').and_return(
        io.StringIO('R /bar\n# comment\n\n   \nR /baz'),
    )
    flexmock(module).should_receive('parse_pattern').with_args('R /foo').and_return(Pattern('/foo'))
    flexmock(module).should_receive('parse_pattern').with_args('# comment').never()
    flexmock(module).should_receive('parse_pattern').with_args('').never()
    flexmock(module).should_receive('parse_pattern').with_args('   ').never()
    flexmock(module).should_receive('parse_pattern').with_args('R /bar').and_return(Pattern('/bar'))
    flexmock(module).should_receive('parse_pattern').with_args('R /baz').and_return(Pattern('/baz'))

    assert module.collect_patterns({'patterns_from': ['file1.txt', 'file2.txt']}) == (
        Pattern('/foo'),
        Pattern('/bar'),
        Pattern('/baz'),
    )


def test_collect_patterns_errors_on_missing_config_patterns_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt', encoding='utf-8').and_raise(
        FileNotFoundError
    )
    flexmock(module).should_receive('parse_pattern').never()

    with pytest.raises(ValueError):
        module.collect_patterns({'patterns_from': ['file1.txt', 'file2.txt']})


def test_collect_patterns_reads_config_exclude_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt', encoding='utf-8').and_return(
        io.StringIO('/foo')
    )
    builtins.should_receive('open').with_args('file2.txt', encoding='utf-8').and_return(
        io.StringIO('/bar\n# comment\n\n   \n/baz'),
    )
    flexmock(module).should_receive('parse_pattern').with_args(
        '! /foo',
        default_style=Pattern_style.FNMATCH,
    ).and_return(Pattern('/foo', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH))
    flexmock(module).should_receive('parse_pattern').with_args(
        '! /bar',
        default_style=Pattern_style.FNMATCH,
    ).and_return(Pattern('/bar', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH))
    flexmock(module).should_receive('parse_pattern').with_args('# comment').never()
    flexmock(module).should_receive('parse_pattern').with_args('').never()
    flexmock(module).should_receive('parse_pattern').with_args('   ').never()
    flexmock(module).should_receive('parse_pattern').with_args(
        '! /baz',
        default_style=Pattern_style.FNMATCH,
    ).and_return(Pattern('/baz', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH))

    assert module.collect_patterns({'exclude_from': ['file1.txt', 'file2.txt']}) == (
        Pattern('/foo', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH),
        Pattern('/bar', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH),
        Pattern('/baz', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH),
    )


def test_collect_patterns_errors_on_missing_config_exclude_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt', encoding='utf-8').and_raise(OSError)
    flexmock(module).should_receive('parse_pattern').never()

    with pytest.raises(ValueError):
        module.collect_patterns({'exclude_from': ['file1.txt', 'file2.txt']})


def test_expand_directory_with_basic_path_passes_it_through():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo')
    flexmock(module.glob).should_receive('glob').and_return([])

    paths = module.expand_directory('foo', None)

    assert paths == ['foo']


def test_expand_directory_with_glob_expands():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo*')
    flexmock(module.glob).should_receive('glob').and_return(['foo', 'food'])

    paths = module.expand_directory('foo*', None)

    assert paths == ['foo', 'food']


def test_expand_directory_strips_off_working_directory():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo').and_return([]).once()

    paths = module.expand_directory('foo', working_directory='/working/dir')

    assert paths == ['foo']


def test_expand_directory_globs_working_directory_and_strips_it_off():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo*')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo*').and_return(
        ['/working/dir/foo', '/working/dir/food'],
    ).once()

    paths = module.expand_directory('foo*', working_directory='/working/dir')

    assert paths == ['foo', 'food']


def test_expand_directory_with_slashdot_hack_globs_working_directory_and_strips_it_off():
    flexmock(module.os.path).should_receive('expanduser').and_return('./foo*')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/./foo*').and_return(
        ['/working/dir/./foo', '/working/dir/./food'],
    ).once()

    paths = module.expand_directory('./foo*', working_directory='/working/dir')

    assert paths == ['./foo', './food']


def test_expand_directory_with_working_directory_matching_start_of_directory_does_not_strip_it_off():
    flexmock(module.os.path).should_receive('expanduser').and_return('/working/dir/foo')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo').and_return(
        ['/working/dir/foo'],
    ).once()

    paths = module.expand_directory('/working/dir/foo', working_directory='/working/dir')

    assert paths == ['/working/dir/foo']


def test_expand_patterns_flattens_expanded_directories():
    flexmock(module).should_receive('expand_directory').with_args('~/foo', None).and_return(
        ['/root/foo'],
    )
    flexmock(module).should_receive('expand_directory').with_args('bar*', None).and_return(
        ['bar', 'barf'],
    )

    paths = module.expand_patterns((Pattern('~/foo'), Pattern('bar*')))

    assert paths == (Pattern('/root/foo'), Pattern('bar'), Pattern('barf'))


def test_expand_patterns_with_working_directory_passes_it_through():
    flexmock(module).should_receive('expand_directory').with_args('foo', '/working/dir').and_return(
        ['/working/dir/foo'],
    )

    patterns = module.expand_patterns((Pattern('foo'),), working_directory='/working/dir')

    assert patterns == (Pattern('/working/dir/foo'),)


def test_expand_patterns_does_not_expand_skip_paths():
    flexmock(module).should_receive('expand_directory').with_args('/foo', None).and_return(['/foo'])
    flexmock(module).should_receive('expand_directory').with_args('/bar*', None).never()

    patterns = module.expand_patterns((Pattern('/foo'), Pattern('/bar*')), skip_paths=('/bar*',))

    assert patterns == (Pattern('/foo'), Pattern('/bar*'))


def test_expand_patterns_considers_none_as_no_patterns():
    assert module.expand_patterns(None) == ()


def test_expand_patterns_expands_tildes_and_globs_in_root_patterns():
    flexmock(module.os.path).should_receive('expanduser').never()
    flexmock(module).should_receive('expand_directory').and_return(
        ['/root/foo/one', '/root/foo/two'],
    )

    paths = module.expand_patterns((Pattern('~/foo/*'),))

    assert paths == (Pattern('/root/foo/one'), Pattern('/root/foo/two'))


def test_expand_patterns_expands_only_tildes_in_non_root_patterns():
    flexmock(module).should_receive('expand_directory').never()
    flexmock(module.os.path).should_receive('expanduser').and_return('/root/bar/*')

    paths = module.expand_patterns((Pattern('~/bar/*', Pattern_type.INCLUDE),))

    assert paths == (Pattern('/root/bar/*', Pattern_type.INCLUDE),)


def test_get_existent_path_or_parent_passes_through_existent_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)

    assert module.get_existent_path_or_parent('/foo/bar/baz') == '/foo/bar/baz'


def test_get_existent_path_or_parent_with_non_existent_path_returns_none():
    flexmock(module.os.path).should_receive('exists').and_return(False)

    assert module.get_existent_path_or_parent('/foo/bar/baz') is None


def test_get_existent_path_or_parent_with_non_existent_path_returns_existent_parent():
    flexmock(module.os.path).should_receive('exists').with_args('/foo/bar/baz*').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/foo/bar').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/foo').never()
    flexmock(module.os.path).should_receive('exists').with_args('/').never()

    assert module.get_existent_path_or_parent('/foo/bar/baz*') == '/foo/bar'


def test_get_existent_path_or_parent_with_non_existent_path_returns_existent_grandparent():
    flexmock(module.os.path).should_receive('exists').with_args('/foo/bar/baz*').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/foo/bar').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/').never()

    assert module.get_existent_path_or_parent('/foo/bar/baz*') == '/foo'


def test_get_existent_path_or_parent_with_end_to_end_test_prefix_returns_none():
    flexmock(module.os.path).should_receive('exists').never()

    assert module.get_existent_path_or_parent('/e2e/foo/bar/baz') is None


def test_device_map_patterns_gives_device_id_per_path():
    flexmock(module).should_receive('get_existent_path_or_parent').replace_with(lambda path: path)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').and_return(flexmock(st_dev=66))

    device_map = module.device_map_patterns(
        (
            Pattern('/foo'),
            Pattern('^/bar', type=Pattern_type.INCLUDE, style=Pattern_style.REGULAR_EXPRESSION),
        ),
    )

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern(
            '^/bar',
            type=Pattern_type.INCLUDE,
            style=Pattern_style.REGULAR_EXPRESSION,
            device=66,
        ),
    )


def test_device_map_patterns_with_missing_path_does_not_error():
    flexmock(module).should_receive('get_existent_path_or_parent').with_args('/foo').and_return(
        '/foo',
    )
    flexmock(module).should_receive('get_existent_path_or_parent').with_args('/bar').and_return(
        None,
    )
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').never()

    device_map = module.device_map_patterns((Pattern('/foo'), Pattern('/bar')))

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('/bar'),
    )


def test_device_map_patterns_uses_working_directory_to_construct_path():
    flexmock(module).should_receive('get_existent_path_or_parent').replace_with(lambda path: path)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/working/dir/bar').and_return(
        flexmock(st_dev=66),
    )

    device_map = module.device_map_patterns(
        (Pattern('/foo'), Pattern('bar')),
        working_directory='/working/dir',
    )

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('bar', device=66),
    )


def test_device_map_patterns_with_existing_device_id_does_not_overwrite_it():
    flexmock(module).should_receive('get_existent_path_or_parent').replace_with(lambda path: path)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').and_return(flexmock(st_dev=100))

    device_map = module.device_map_patterns((Pattern('/foo'), Pattern('/bar', device=66)))

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('/bar', device=66),
    )


@pytest.mark.parametrize(
    'patterns,borgmatic_runtime_directory,expected_patterns,one_file_system',
    (
        (
            (Pattern('/', device=1), Pattern('/root', device=1)),
            '/root',
            (Pattern('/', device=1),),
            False,
        ),
        # No deduplication is expected when borgmatic runtime directory is None.
        (
            (Pattern('/', device=1), Pattern('/root', device=1)),
            None,
            (Pattern('/', device=1), Pattern('/root', device=1)),
            False,
        ),
        (
            (Pattern('/', device=1), Pattern('/root/', device=1)),
            '/root',
            (Pattern('/', device=1),),
            False,
        ),
        (
            (Pattern('/', device=1), Pattern('/root', device=2)),
            '/root',
            (Pattern('/', device=1),),
            False,
        ),
        (
            (Pattern('/', device=1), Pattern('/root', device=2)),
            None,
            (Pattern('/', device=1), Pattern('/root', device=2)),
            False,
        ),
        (
            (Pattern('/root', device=1), Pattern('/', device=1)),
            '/root',
            (Pattern('/', device=1),),
            False,
        ),
        (
            (Pattern('/root', device=1), Pattern('/', device=1)),
            None,
            (Pattern('/root', device=1), Pattern('/', device=1)),
            False,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            '/root/foo',
            (Pattern('/root', device=1),),
            False,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            None,
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            False,
        ),
        # No deduplication is expected when the runtime directory doesn't match the patterns.
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            '/other',
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            False,
        ),
        (
            (Pattern('/root/', device=1), Pattern('/root/foo', device=1)),
            '/root/foo',
            (Pattern('/root/', device=1),),
            False,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo/', device=1)),
            '/root/foo',
            (Pattern('/root', device=1),),
            False,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=2)),
            '/root/foo',
            (Pattern('/root', device=1),),
            False,
        ),
        (
            (Pattern('/root/foo', device=1), Pattern('/root', device=1)),
            '/root/foo',
            (Pattern('/root', device=1),),
            False,
        ),
        (
            (Pattern('/root', device=None), Pattern('/root/foo', device=None)),
            '/root/foo',
            (Pattern('/root'), Pattern('/root/foo')),
            False,
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/etc', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            '/root/foo/bar',
            (Pattern('/root', device=1), Pattern('/etc', device=1)),
            False,
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            '/root/foo/bar',
            (Pattern('/root', device=1),),
            False,
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            None,
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            False,
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            '/other',
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            False,
        ),
        (
            (Pattern('/dup', device=1), Pattern('/dup', device=1)),
            '/dup',
            (Pattern('/dup', device=1),),
            False,
        ),
        (
            (Pattern('/foo', device=1), Pattern('/bar', device=1)),
            '/bar',
            (Pattern('/foo', device=1), Pattern('/bar', device=1)),
            False,
        ),
        (
            (Pattern('/foo', device=1), Pattern('/bar', device=2)),
            '/bar',
            (Pattern('/foo', device=1), Pattern('/bar', device=2)),
            False,
        ),
        ((Pattern('/root/foo', device=1),), '/root/foo', (Pattern('/root/foo', device=1),), False),
        (
            (Pattern('/', device=1), Pattern('/root', Pattern_type.INCLUDE, device=1)),
            '/root',
            (Pattern('/', device=1), Pattern('/root', Pattern_type.INCLUDE, device=1)),
            False,
        ),
        (
            (Pattern('/root', Pattern_type.INCLUDE, device=1), Pattern('/', device=1)),
            '/root',
            (Pattern('/root', Pattern_type.INCLUDE, device=1), Pattern('/', device=1)),
            False,
        ),
        (
            (Pattern('/', device=1), Pattern('/root', device=1)),
            '/root',
            (Pattern('/', device=1),),
            True,
        ),
        (
            (Pattern('/', device=1), Pattern('/root/', device=1)),
            '/root',
            (Pattern('/', device=1),),
            True,
        ),
        (
            (Pattern('/', device=1), Pattern('/root', device=2)),
            '/root',
            (Pattern('/', device=1), Pattern('/root', device=2)),
            True,
        ),
        (
            (Pattern('/root', device=1), Pattern('/', device=1)),
            '/root',
            (Pattern('/', device=1),),
            True,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            '/root/foo',
            (Pattern('/root', device=1),),
            True,
        ),
        (
            (Pattern('/root/', device=1), Pattern('/root/foo', device=1)),
            '/root/foo',
            (Pattern('/root/', device=1),),
            True,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo/', device=1)),
            '/root/foo',
            (Pattern('/root', device=1),),
            True,
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=2)),
            '/root/foo',
            (Pattern('/root', device=1), Pattern('/root/foo', device=2)),
            True,
        ),
        (
            (Pattern('/root/foo', device=1), Pattern('/root', device=1)),
            '/root/foo',
            (Pattern('/root', device=1),),
            True,
        ),
        (
            (Pattern('/root', device=None), Pattern('/root/foo', device=None)),
            '/root/foo',
            (Pattern('/root'), Pattern('/root/foo')),
            True,
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/etc', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            '/root/foo/bar',
            (Pattern('/root', device=1), Pattern('/etc', device=1)),
            True,
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            '/root/foo/bar',
            (Pattern('/root', device=1),),
            True,
        ),
        (
            (Pattern('/dup', device=1), Pattern('/dup', device=1)),
            '/dup',
            (Pattern('/dup', device=1),),
            True,
        ),
        (
            (Pattern('/foo', device=1), Pattern('/bar', device=1)),
            '/bar',
            (Pattern('/foo', device=1), Pattern('/bar', device=1)),
            True,
        ),
        (
            (Pattern('/foo', device=1), Pattern('/bar', device=2)),
            '/bar',
            (Pattern('/foo', device=1), Pattern('/bar', device=2)),
            True,
        ),
        ((Pattern('/root/foo', device=1),), '/root/foo', (Pattern('/root/foo', device=1),), True),
        (
            (Pattern('/', device=1), Pattern('/root', Pattern_type.INCLUDE, device=1)),
            '/root',
            (Pattern('/', device=1), Pattern('/root', Pattern_type.INCLUDE, device=1)),
            True,
        ),
        (
            (Pattern('/root', Pattern_type.INCLUDE, device=1), Pattern('/', device=1)),
            '/root',
            (Pattern('/root', Pattern_type.INCLUDE, device=1), Pattern('/', device=1)),
            True,
        ),
    ),
)
def test_deduplicate_runtime_directory_patterns_omits_child_paths_based_on_device_and_one_file_system(
    patterns,
    borgmatic_runtime_directory,
    expected_patterns,
    one_file_system,
):
    assert (
        module.deduplicate_runtime_directory_patterns(
            patterns, {'one_file_system': one_file_system}, borgmatic_runtime_directory
        )
        == expected_patterns
    )


def test_process_patterns_includes_patterns():
    flexmock(module).should_receive('deduplicate_runtime_directory_patterns').and_return(
        (Pattern('foo'), Pattern('bar')),
    )
    flexmock(module).should_receive('device_map_patterns').and_return({})
    flexmock(module).should_receive('expand_patterns').with_args(
        (Pattern('foo'), Pattern('bar')),
        working_directory='/working',
        skip_paths=set(),
    ).and_return(()).once()

    assert module.process_patterns(
        (Pattern('foo'), Pattern('bar')),
        config={},
        working_directory='/working',
    ) == [Pattern('foo'), Pattern('bar')]


def test_process_patterns_skips_expand_for_requested_paths():
    skip_paths = {flexmock()}
    flexmock(module).should_receive('deduplicate_runtime_directory_patterns').and_return(
        (Pattern('foo'), Pattern('bar')),
    )
    flexmock(module).should_receive('device_map_patterns').and_return({})
    flexmock(module).should_receive('expand_patterns').with_args(
        (Pattern('foo'), Pattern('bar')),
        working_directory='/working',
        skip_paths=skip_paths,
    ).and_return(()).once()

    assert module.process_patterns(
        (Pattern('foo'), Pattern('bar')),
        config={},
        working_directory='/working',
        skip_expand_paths=skip_paths,
    ) == [Pattern('foo'), Pattern('bar')]
