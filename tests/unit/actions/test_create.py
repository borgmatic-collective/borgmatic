import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.actions import create as module
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
                '/foo*', Pattern_type.INCLUDE, Pattern_style.SHELL, source=Pattern_source.CONFIG
            ),
        ),
    ),
)
def test_parse_pattern_transforms_pattern_line_to_instance(pattern_line, expected_pattern):
    module.parse_pattern(pattern_line) == expected_pattern


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
            '/foo', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH, source=Pattern_source.CONFIG
        ),
        Pattern(
            '/bar', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH, source=Pattern_source.CONFIG
        ),
        Pattern(
            '**/baz', Pattern_type.NO_RECURSE, Pattern_style.SHELL, source=Pattern_source.CONFIG
        ),
    )


def test_collect_patterns_reads_config_patterns_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt').and_return(io.StringIO('R /foo'))
    builtins.should_receive('open').with_args('file2.txt').and_return(
        io.StringIO('R /bar\n# comment\n\n   \nR /baz')
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
    builtins.should_receive('open').with_args('file1.txt').and_raise(FileNotFoundError)
    flexmock(module).should_receive('parse_pattern').never()

    with pytest.raises(ValueError):
        module.collect_patterns({'patterns_from': ['file1.txt', 'file2.txt']})


def test_collect_patterns_reads_config_exclude_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt').and_return(io.StringIO('/foo'))
    builtins.should_receive('open').with_args('file2.txt').and_return(
        io.StringIO('/bar\n# comment\n\n   \n/baz')
    )
    flexmock(module).should_receive('parse_pattern').with_args(
        '! /foo', default_style=Pattern_style.FNMATCH
    ).and_return(Pattern('/foo', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH))
    flexmock(module).should_receive('parse_pattern').with_args(
        '! /bar', default_style=Pattern_style.FNMATCH
    ).and_return(Pattern('/bar', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH))
    flexmock(module).should_receive('parse_pattern').with_args('# comment').never()
    flexmock(module).should_receive('parse_pattern').with_args('').never()
    flexmock(module).should_receive('parse_pattern').with_args('   ').never()
    flexmock(module).should_receive('parse_pattern').with_args(
        '! /baz', default_style=Pattern_style.FNMATCH
    ).and_return(Pattern('/baz', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH))

    assert module.collect_patterns({'exclude_from': ['file1.txt', 'file2.txt']}) == (
        Pattern('/foo', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH),
        Pattern('/bar', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH),
        Pattern('/baz', Pattern_type.NO_RECURSE, Pattern_style.FNMATCH),
    )


def test_collect_patterns_errors_on_missing_config_exclude_from_file():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('file1.txt').and_raise(OSError)
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
        ['/working/dir/foo', '/working/dir/food']
    ).once()

    paths = module.expand_directory('foo*', working_directory='/working/dir')

    assert paths == ['foo', 'food']


def test_expand_directory_with_slashdot_hack_globs_working_directory_and_strips_it_off():
    flexmock(module.os.path).should_receive('expanduser').and_return('./foo*')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/./foo*').and_return(
        ['/working/dir/./foo', '/working/dir/./food']
    ).once()

    paths = module.expand_directory('./foo*', working_directory='/working/dir')

    assert paths == ['./foo', './food']


def test_expand_directory_with_working_directory_matching_start_of_directory_does_not_strip_it_off():
    flexmock(module.os.path).should_receive('expanduser').and_return('/working/dir/foo')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo').and_return(
        ['/working/dir/foo']
    ).once()

    paths = module.expand_directory('/working/dir/foo', working_directory='/working/dir')

    assert paths == ['/working/dir/foo']


def test_expand_patterns_flattens_expanded_directories():
    flexmock(module).should_receive('expand_directory').with_args('~/foo', None).and_return(
        ['/root/foo']
    )
    flexmock(module).should_receive('expand_directory').with_args('bar*', None).and_return(
        ['bar', 'barf']
    )

    paths = module.expand_patterns((Pattern('~/foo'), Pattern('bar*')))

    assert paths == (Pattern('/root/foo'), Pattern('bar'), Pattern('barf'))


def test_expand_patterns_with_working_directory_passes_it_through():
    flexmock(module).should_receive('expand_directory').with_args('foo', '/working/dir').and_return(
        ['/working/dir/foo']
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


def test_expand_patterns_only_considers_root_patterns():
    flexmock(module).should_receive('expand_directory').with_args('~/foo', None).and_return(
        ['/root/foo']
    )
    flexmock(module).should_receive('expand_directory').with_args('bar*', None).never()

    paths = module.expand_patterns((Pattern('~/foo'), Pattern('bar*', Pattern_type.INCLUDE)))

    assert paths == (Pattern('/root/foo'), Pattern('bar*', Pattern_type.INCLUDE))


def test_device_map_patterns_gives_device_id_per_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').and_return(flexmock(st_dev=66))

    device_map = module.device_map_patterns((Pattern('/foo'), Pattern('/bar')))

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('/bar', device=66),
    )


def test_device_map_patterns_only_considers_root_patterns():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar*').never()

    device_map = module.device_map_patterns(
        (Pattern('/foo'), Pattern('/bar*', Pattern_type.INCLUDE))
    )

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('/bar*', Pattern_type.INCLUDE),
    )


def test_device_map_patterns_with_missing_path_does_not_error():
    flexmock(module.os.path).should_receive('exists').and_return(True).and_return(False)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').never()

    device_map = module.device_map_patterns((Pattern('/foo'), Pattern('/bar')))

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('/bar'),
    )


def test_device_map_patterns_uses_working_directory_to_construct_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/working/dir/bar').and_return(
        flexmock(st_dev=66)
    )

    device_map = module.device_map_patterns(
        (Pattern('/foo'), Pattern('bar')), working_directory='/working/dir'
    )

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('bar', device=66),
    )


def test_device_map_patterns_with_existing_device_id_does_not_overwrite_it():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').and_return(flexmock(st_dev=100))

    device_map = module.device_map_patterns((Pattern('/foo'), Pattern('/bar', device=66)))

    assert device_map == (
        Pattern('/foo', device=55),
        Pattern('/bar', device=66),
    )


@pytest.mark.parametrize(
    'patterns,expected_patterns',
    (
        ((Pattern('/', device=1), Pattern('/root', device=1)), (Pattern('/', device=1),)),
        ((Pattern('/', device=1), Pattern('/root/', device=1)), (Pattern('/', device=1),)),
        (
            (Pattern('/', device=1), Pattern('/root', device=2)),
            (Pattern('/', device=1), Pattern('/root', device=2)),
        ),
        ((Pattern('/root', device=1), Pattern('/', device=1)), (Pattern('/', device=1),)),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=1)),
            (Pattern('/root', device=1),),
        ),
        (
            (Pattern('/root/', device=1), Pattern('/root/foo', device=1)),
            (Pattern('/root/', device=1),),
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo/', device=1)),
            (Pattern('/root', device=1),),
        ),
        (
            (Pattern('/root', device=1), Pattern('/root/foo', device=2)),
            (Pattern('/root', device=1), Pattern('/root/foo', device=2)),
        ),
        (
            (Pattern('/root/foo', device=1), Pattern('/root', device=1)),
            (Pattern('/root', device=1),),
        ),
        (
            (Pattern('/root', device=None), Pattern('/root/foo', device=None)),
            (Pattern('/root'), Pattern('/root/foo')),
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/etc', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            (Pattern('/root', device=1), Pattern('/etc', device=1)),
        ),
        (
            (
                Pattern('/root', device=1),
                Pattern('/root/foo', device=1),
                Pattern('/root/foo/bar', device=1),
            ),
            (Pattern('/root', device=1),),
        ),
        ((Pattern('/dup', device=1), Pattern('/dup', device=1)), (Pattern('/dup', device=1),)),
        (
            (Pattern('/foo', device=1), Pattern('/bar', device=1)),
            (Pattern('/foo', device=1), Pattern('/bar', device=1)),
        ),
        (
            (Pattern('/foo', device=1), Pattern('/bar', device=2)),
            (Pattern('/foo', device=1), Pattern('/bar', device=2)),
        ),
        ((Pattern('/root/foo', device=1),), (Pattern('/root/foo', device=1),)),
        (
            (Pattern('/', device=1), Pattern('/root', Pattern_type.INCLUDE, device=1)),
            (Pattern('/', device=1), Pattern('/root', Pattern_type.INCLUDE, device=1)),
        ),
        (
            (Pattern('/root', Pattern_type.INCLUDE, device=1), Pattern('/', device=1)),
            (Pattern('/root', Pattern_type.INCLUDE, device=1), Pattern('/', device=1)),
        ),
    ),
)
def test_deduplicate_patterns_omits_child_paths_on_the_same_filesystem(patterns, expected_patterns):
    assert module.deduplicate_patterns(patterns) == expected_patterns


def test_process_patterns_includes_patterns():
    flexmock(module).should_receive('deduplicate_patterns').and_return(
        (Pattern('foo'), Pattern('bar'))
    )
    flexmock(module).should_receive('device_map_patterns').and_return({})
    flexmock(module).should_receive('expand_patterns').with_args(
        (Pattern('foo'), Pattern('bar')),
        working_directory='/working',
        skip_paths=set(),
    ).and_return(()).once()

    assert module.process_patterns(
        (Pattern('foo'), Pattern('bar')),
        working_directory='/working',
    ) == [Pattern('foo'), Pattern('bar')]


def test_process_patterns_skips_expand_for_requested_paths():
    skip_paths = {flexmock()}
    flexmock(module).should_receive('deduplicate_patterns').and_return(
        (Pattern('foo'), Pattern('bar'))
    )
    flexmock(module).should_receive('device_map_patterns').and_return({})
    flexmock(module).should_receive('expand_patterns').with_args(
        (Pattern('foo'), Pattern('bar')),
        working_directory='/working',
        skip_paths=skip_paths,
    ).and_return(()).once()

    assert module.process_patterns(
        (Pattern('foo'), Pattern('bar')),
        working_directory='/working',
        skip_expand_paths=skip_paths,
    ) == [Pattern('foo'), Pattern('bar')]


def test_run_create_executes_and_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('collect_patterns').and_return(())
    flexmock(module).should_receive('process_patterns').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_runs_with_selected_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('collect_patterns').and_return(())
    flexmock(module).should_receive('process_patterns').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(False)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').never()
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').never()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository='repo',
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_produces_json():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once().and_return(
        flexmock()
    )
    parsed_json = flexmock()
    flexmock(module.borgmatic.actions.json).should_receive('parse_json').and_return(parsed_json)
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('collect_patterns').and_return(())
    flexmock(module).should_receive('process_patterns').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=True,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    assert list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    ) == [parsed_json]
