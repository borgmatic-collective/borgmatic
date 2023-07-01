import json
import re

import pytest
from flexmock import flexmock

from borgmatic.hooks import snapper as module


@pytest.fixture(scope='function', autouse=True)
def setup():
    module._available_configs.cache_clear()


@pytest.mark.parametrize('src_dirs_before', ([], ['/foo'], ['/foo', '/bar', '/baz']))
def test_unaltered_if_not_configured(src_dirs_before):
    log_prefix = ''
    src_dirs_after = module.prepare_source_directories({}, log_prefix, src_dirs_before)
    assert src_dirs_before == src_dirs_after


def test_use_snapshots_include_all():
    log_prefix = ''

    flexmock(module).should_receive('execute_command_and_capture_output').once().with_args(
        ['snapper', '--jsonout', 'list-configs']
    ).and_return(
        json.dumps(
            {
                'configs': [
                    {
                        'config': 'foo',
                        'subvolume': '/foo',
                    },
                ],
            }
        )
    )
    flexmock(module).should_receive('execute_command_and_capture_output').once().with_args(
        ['snapper', '--jsonout', '-c', 'foo', 'list', '--disable-used-space']
    ).and_return(
        json.dumps(
            {
                'foo': [
                    {
                        'subvolume': '/foo',
                        'number': 17,
                        'default': False,
                        'active': False,
                        'type': 'single',
                        'pre-number': None,
                        'date': '2023-03-02 21:31:44',
                        'user': 'root',
                        'cleanup': '',
                        'description': 'current',
                        'userdata': None,
                    },
                ]
            }
        )
    )
    flexmock(module.Path).should_receive('exists').once().and_return(True)

    src_dirs_before = ['/foo']
    src_dirs_after = module.prepare_source_directories(
        {'include': 'all'}, log_prefix, src_dirs_before
    )
    assert src_dirs_after == ['/foo/.snapshots/17/snapshot']


@pytest.mark.parametrize(
    'config,src_dirs_in,expected',
    (
        (
            {'include': 'all'},
            ['/foo', '/bar', '/baz'],
            [
                '/foo/.snapshots/17/snapshot',
                '/bar/.snapshots/1337/snapshot',
                '/baz/.snapshots/13337/snapshot',
            ],
        ),
        (
            {'include': ['/bar', '/foo']},
            ['/foo', '/bar', '/baz'],
            ['/foo/.snapshots/17/snapshot', '/bar/.snapshots/1337/snapshot', '/baz'],
        ),
        (
            {'include': 'all', 'exclude': ['/baz']},
            ['/foo', '/bar', '/baz'],
            ['/foo/.snapshots/17/snapshot', '/bar/.snapshots/1337/snapshot', '/baz'],
        ),
        (
            {'include': 'all', 'exclude': ['/baz']},
            ['/foo', '/bar', '/baz'],
            ['/foo/.snapshots/17/snapshot', '/bar/.snapshots/1337/snapshot', '/baz'],
        ),
        (
            {'include': ['/foo', '/bar', '/baz'], 'exclude': ['/baz']},
            ['/foo', '/bar', '/baz'],
            ['/foo/.snapshots/17/snapshot', '/bar/.snapshots/1337/snapshot', '/baz'],
        ),
        (
            {'include': ['/foo', '/foo', '/foo'], 'exclude': ['/baz']},
            ['/foo', '/bar', '/baz'],
            ['/foo/.snapshots/17/snapshot', '/bar', '/baz'],
        ),
        (
            {'include': 'all', 'exclude': ['/foo', '/bar', '/baz']},
            ['/foo', '/bar', '/baz'],
            ['/foo', '/bar', '/baz'],
        ),
        (
            {'include': 'all'},
            ['/foo', '/bar', '/baz', '/quaz'],
            [
                '/foo/.snapshots/17/snapshot',
                '/bar/.snapshots/1337/snapshot',
                '/baz/.snapshots/13337/snapshot',
                '/quaz',
            ],
        ),
    ),
)
def test_use_snapshots_include_exclude(config, src_dirs_in, expected):
    log_prefix = ''

    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ['snapper', '--jsonout', 'list-configs']
    ).and_return(
        json.dumps(
            {
                'configs': [
                    {
                        'config': 'foo',
                        'subvolume': '/foo',
                    },
                    {
                        'config': 'bar',
                        'subvolume': '/bar',
                    },
                    {
                        'config': 'baz',
                        'subvolume': '/baz',
                    },
                ],
            }
        )
    )
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ['snapper', '--jsonout', '-c', 'foo', 'list', '--disable-used-space']
    ).and_return(
        json.dumps(
            {
                'foo': [
                    {
                        'number': 17,
                    },
                ]
            }
        )
    )
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ['snapper', '--jsonout', '-c', 'bar', 'list', '--disable-used-space']
    ).and_return(
        json.dumps(
            {
                'bar': [
                    {
                        'number': 1337,
                    },
                ]
            }
        )
    )
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ['snapper', '--jsonout', '-c', 'baz', 'list', '--disable-used-space']
    ).and_return(
        json.dumps(
            {
                'baz': [
                    {
                        'number': 13337,
                    },
                ]
            }
        )
    )
    flexmock(module.Path).should_receive('exists').and_return(True)

    src_dirs_after = module.prepare_source_directories(config, log_prefix, src_dirs_in)
    assert set(src_dirs_after) == set(expected)


def test_no_config():
    log_prefix = ''

    flexmock(module).should_receive('execute_command_and_capture_output').once().with_args(
        ['snapper', '--jsonout', 'list-configs']
    ).and_return(
        json.dumps(
            {
                'configs': [
                    {
                        'config': 'bar',
                        'subvolume': '/bar',
                    },
                ],
            }
        )
    )

    src_dirs_before = ['/foo']
    with pytest.raises(ValueError) as e_info:
        module.prepare_source_directories({'include': ['/foo']}, log_prefix, src_dirs_before)
    assert 'could not be found' in str(e_info)


def test_snapshot_not_present():
    log_prefix = ''

    flexmock(module).should_receive('execute_command_and_capture_output').once().with_args(
        ['snapper', '--jsonout', 'list-configs']
    ).and_return(
        json.dumps(
            {
                'configs': [
                    {
                        'config': 'foo',
                        'subvolume': '/foo',
                    },
                ],
            }
        )
    )
    flexmock(module).should_receive('execute_command_and_capture_output').once().with_args(
        ['snapper', '--jsonout', '-c', 'foo', 'list', '--disable-used-space']
    ).and_return(
        json.dumps(
            {
                'foo': [
                    {
                        'subvolume': '/foo',
                        'number': 17,
                        'default': False,
                        'active': False,
                        'type': 'single',
                        'pre-number': None,
                        'date': '2023-03-02 21:31:44',
                        'user': 'root',
                        'cleanup': '',
                        'description': 'current',
                        'userdata': None,
                    },
                ]
            }
        )
    )
    flexmock(module.Path).should_receive('exists').once().and_return(False)

    src_dirs_before = ['/foo']
    with pytest.raises(ValueError) as e_info:
        module.prepare_source_directories({'include': 'all'}, log_prefix, src_dirs_before)

    assert re.match(r'.*deduced directory .* is not present.*', str(e_info))
