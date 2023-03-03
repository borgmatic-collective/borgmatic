import json
import logging
from copy import copy
from functools import cache
from pathlib import Path

from borgmatic.execute import execute_command_and_capture_output

logger = logging.getLogger(__name__)


def _call_snapper(*args) -> dict:
    return json.loads(execute_command_and_capture_output(["snapper", "--jsonout", *args]))


@cache
def _available_configs() -> dict[Path, str]:
    configs = _call_snapper("list-configs")["configs"]
    # using Path as a key makes it possible to ignore the trailing slash problem
    # i.e. Path("/test") == Path("/test/")
    return {Path(c["subvolume"]): c["config"] for c in configs}


def prepare_source_directories(hook_config, log_prefix, src_dirs):
    '''
    Alter source directory list to use the latest snapper snapshot for each configured path
    '''
    if hook_config == {}:
        return src_dirs
    src_dirs = set(map(Path, src_dirs))
    if hook_config["include"] == "all":
        snapper_dirs = copy(src_dirs)
        fail = False
    else:
        include_dirs = set(map(Path, hook_config["include"]))
        snapper_dirs = src_dirs & include_dirs
        fail = True
    if hook_config.get("exclude"):
        exclude_dirs = set(map(Path, hook_config["exclude"]))
        snapper_dirs -= exclude_dirs

    processed_dirs = set()
    altered_dirs = set()
    for snapper_dir in snapper_dirs:
        msg = f'Source directory "{snapper_dir}" was configured to use its latest snapper snapshot for backup, '
        if snapper_dir not in _available_configs():
            msg += "but a corresponding snapper config could not be found"
            if fail:
                raise ValueError(msg)
            else:
                logger.warning(msg)
                continue
        config = _available_configs()[snapper_dir]
        available_snapshots = _call_snapper("-c", config, "list", "--disable-used-space")
        if not available_snapshots:
            msg += "but there aren't any snapshots available"
            if fail:
                raise ValueError(msg)
            else:
                logger.warning(msg)
                continue
        latest_snapshot_number = str(available_snapshots[config][-1]["number"])
        new_src_dir = snapper_dir / ".snapshots" / latest_snapshot_number / "snapshot"
        processed_dirs.add(snapper_dir)
        altered_dirs.add(new_src_dir)
    return list(map(str, altered_dirs | (src_dirs - processed_dirs)))
