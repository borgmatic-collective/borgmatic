import json
import logging
import os
import shutil
from copy import copy
from functools import lru_cache
from pathlib import Path

from borgmatic.execute import execute_command_and_capture_output

logger = logging.getLogger(__name__)


def _call_snapper(*args) -> dict:
    return json.loads(execute_command_and_capture_output(['snapper', '--jsonout', *args]))


@lru_cache(maxsize=None)
def _available_configs() -> dict[Path, str]:
    '''
    Returns available snapper configs mapping subvolume paths to snapper config names
    '''
    configs = _call_snapper('list-configs')['configs']
    # using Path as a key makes it possible to ignore the trailing slash problem
    # i.e. Path('/test') == Path('/test/')
    return {Path(config['subvolume']): config['config'] for config in configs}


def prepare_source_directories(hook_config, _log_prefix, source_directories):
    '''
    Computes latest snapper snapshot for each configured path based on source_directories
    '''

    if hook_config == {}:
        return source_directories
    source_directories = set(map(Path, source_directories))

    if hook_config['include'] == 'all':
        snapper_dirs = copy(source_directories)
        include_all = True
    else:
        include_dirs = set(map(Path, hook_config['include']))
        snapper_dirs = source_directories.intersection(include_dirs)
        include_all = False

    if hook_config.get('exclude'):
        exclude_dirs = set(map(Path, hook_config['exclude']))
        snapper_dirs -= exclude_dirs

    processed_dirs = set()
    altered_dirs = set()

    for snapper_dir in snapper_dirs:
        if snapper_dir not in _available_configs():
            msg = (
                f'Source directory "{snapper_dir}" was configured to use its latest snapper snapshot for backup, '
                f'but a corresponding snapper config could not be found'
            )
            if include_all:
                logger.warning(msg)
                continue
            else:
                raise ValueError(msg)
        config = _available_configs()[snapper_dir]
        available_snapshots = _call_snapper('-c', config, 'list', '--disable-used-space')
        latest_snapshot_number = str(available_snapshots[config][-1]['number'])
        new_src_dir = snapper_dir / '.snapshots' / latest_snapshot_number / 'snapshot'

        if not new_src_dir.exists():
            msg = (
                f'Detected snapshot number {latest_snapshot_number} to be the latest for '
                f'source directory {snapper_dir}, but the deduced directory ({new_src_dir}) is not present. '
                f'Likely causes are .snapshots not being mounted properly or no snapshots have been taken yet'
            )
            raise ValueError(msg)
        processed_dirs.add(snapper_dir)
        altered_dirs.add(new_src_dir)
    return list(map(str, altered_dirs.union(source_directories - processed_dirs)))


def fix_extracted_dirs(hook_config, log_prefix, source_directories, destination_path):
    '''
    Renames extracted configured source_directories from snapper snapshot path back to their original pre-snapshot path
    Example: /some/path/.snapshots/3/snapshot to /some/path
    '''

    if not source_directories:
        logger.warning(
            f'{log_prefix}: No source_directories configured. Unable to rename snapshot directories. '
            f'Please restore source_directories config to be same, when creating the archive for best '
            f'results'
        )
        return
    source_directories = set(map(Path, source_directories))
    destination_path = Path(destination_path) if destination_path else Path(os.getcwd())

    if hook_config['include'] == 'all':
        snapper_dirs = copy(source_directories)
    else:
        include_dirs = set(map(Path, hook_config['include']))
        snapper_dirs = source_directories.intersection(include_dirs)

    if hook_config.get('exclude'):
        exclude_dirs = set(map(Path, hook_config['exclude']))
        snapper_dirs -= exclude_dirs

    for snapper_dir in snapper_dirs:
        # remove leading slash to allow joining with other paths

        if snapper_dir.is_absolute():
            snapper_dir = Path(str(snapper_dir)[1:])
        dest_snapper_dir = destination_path / snapper_dir
        snap_dir = dest_snapper_dir / '.snapshots'

        if not snap_dir.is_dir():
            continue
        snap_number_dir = next(snap_dir.iterdir())

        if not snap_number_dir.is_dir() or not snap_number_dir.name.isdigit():
            continue
        final_snap_dir = snap_number_dir / 'snapshot'

        if not final_snap_dir.is_dir():
            continue

        if len(os.listdir(dest_snapper_dir)) != 1:
            logger.warning(
                f'{log_prefix}: Refusing to overwrite non-empty directory "{dest_snapper_dir}". '
                f'Run "mv {final_snap_dir} {dest_snapper_dir}" if you want to force this'
            )
            continue

        logger.info(f'{log_prefix}: renaming {final_snap_dir} -> {dest_snapper_dir}')
        tmp_snapper_dir = f'{snapper_dir}_'
        final_snap_dir.rename(destination_path / tmp_snapper_dir)
        shutil.rmtree(destination_path / snapper_dir)
        (destination_path / tmp_snapper_dir).rename(dest_snapper_dir)
