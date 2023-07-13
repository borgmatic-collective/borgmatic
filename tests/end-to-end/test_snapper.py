import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

import pytest

BTRFS_IMG_FILE = Path('/tmp/btrfs.img')
BTRFS_IMG_SIZE = 256 * 1024 * 1024  # 256 MB
BTRFS_MOUNT_POINT = Path('/mnt/btrfs')

SNAPPER_CONFIG = f'''
# subvolume to snapshot
SUBVOLUME="{BTRFS_MOUNT_POINT}"

# filesystem type
FSTYPE="btrfs"


# btrfs qgroup for space aware cleanup algorithms
QGROUP=""


# fraction or absolute size of the filesystems space the snapshots may use
SPACE_LIMIT="0.5"

# fraction or absolute size of the filesystems space that should be free
FREE_LIMIT="0.2"


# users and groups allowed to work with config
ALLOW_USERS=""
ALLOW_GROUPS="users"

# sync users and groups from ALLOW_USERS and ALLOW_GROUPS to .snapshots
# directory
SYNC_ACL="no"


# start comparing pre- and post-snapshot in background after creating
# post-snapshot
BACKGROUND_COMPARISON="yes"


# run daily number cleanup
NUMBER_CLEANUP="no"

# limit for number cleanup
NUMBER_MIN_AGE="1800"
NUMBER_LIMIT="50"
NUMBER_LIMIT_IMPORTANT="10"


# create hourly snapshots
TIMELINE_CREATE="no"

# cleanup hourly snapshots after some time
TIMELINE_CLEANUP="no"

# limits for timeline cleanup
TIMELINE_MIN_AGE="1800"
TIMELINE_LIMIT_HOURLY="10"
TIMELINE_LIMIT_DAILY="10"
TIMELINE_LIMIT_WEEKLY="0"
TIMELINE_LIMIT_MONTHLY="10"
TIMELINE_LIMIT_YEARLY="10"


# cleanup empty pre-post-pairs
EMPTY_PRE_POST_CLEANUP="yes"

# limits for empty pre-post-pair cleanup
EMPTY_PRE_POST_MIN_AGE="1800"
'''


@pytest.fixture
def mounted_btrfs():
    with BTRFS_IMG_FILE.open('wb') as f:
        f.seek(BTRFS_IMG_SIZE - 1)
        f.write(b'\0')
    subprocess.check_output(['mkfs.btrfs', str(BTRFS_IMG_FILE)])
    BTRFS_MOUNT_POINT.mkdir()
    subprocess.check_output(
        ['mount', '-t', 'btrfs', '-o', 'loop', str(BTRFS_IMG_FILE), str(BTRFS_MOUNT_POINT)]
    )
    subprocess.check_output(['btrfs', 'subvolume', 'create', f'{BTRFS_MOUNT_POINT / ".snapshots"}'])
    yield BTRFS_MOUNT_POINT
    subprocess.check_output(['umount', str(BTRFS_MOUNT_POINT)])
    BTRFS_MOUNT_POINT.rmdir()
    BTRFS_IMG_FILE.unlink()


@pytest.fixture
def snapper_env():
    config = Path('/etc/snapper/configs/test')
    with config.open('w') as f:
        f.write(SNAPPER_CONFIG)
    meta_config = Path('/etc/snapper/snapper')
    with meta_config.open('w') as f:
        f.write('SNAPPER_CONFIGS="test"')
    dbus_run_dir = Path('/var/run/dbus')
    dbus_run_dir.mkdir()
    original_working_directory = os.getcwd()
    # dbus needs a writeable working dir
    os.chdir("/tmp")
    subprocess.check_call(['dbus-daemon', '--system', '--fork', '--nosyslog'])
    os.chdir(original_working_directory)
    snapperd_proc = subprocess.Popen(['snapperd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    yield
    snapperd_proc.terminate()
    snapperd_proc.wait()
    with open('/run/dbus/dbus.pid', 'r') as f:
        dbus_pid = int(f.read().encode('utf-8').strip())
    os.kill(dbus_pid, signal.SIGTERM)
    shutil.rmtree(dbus_run_dir)
    with meta_config.open('w') as f:
        f.write('SNAPPER_CONFIGS=""')
    config.unlink()


def write_borgmatic_configuration(
    source_directory,
    repository_path,
    config_path,
):
    config = f'''
location:
    source_directories:
        - {source_directory}
    repositories:
        - path: {repository_path}
          label: repo

hooks:
    snapper:
      include: all
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config)


def test_snapper_snapshot_backup_create_and_restore(mounted_btrfs, snapper_env):
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_directory = Path(temporary_directory)
        source_directory = mounted_btrfs
        repository = temporary_directory / 'repo'
        repository.mkdir(parents=True)
        config_path = temporary_directory / 'config.yml'

        test_directory = Path('foo') / 'bar'
        (source_directory / test_directory).mkdir(parents=True)

        test_file = test_directory / 'stuff.txt'
        with (source_directory / test_file).open('w') as f:
            f.write('stuff')

        subprocess.check_call(['snapper', '-c', 'test', 'create'])

        write_borgmatic_configuration(source_directory, repository, config_path)
        subprocess.check_call(
            ['borgmatic', '--config', str(config_path), 'init', '--encryption', 'none']
        )

        subprocess.check_call(['borgmatic', '-c', str(config_path), 'create'])

        extract_dir = temporary_directory / 'extract'
        extract_dir.mkdir()

        extract_command_base = [
            'borgmatic',
            '--config',
            str(config_path),
            'extract',
            '--archive',
            'latest',
            '--repository',
            'repo',
            '--destination',
        ]
        extract_command = extract_command_base + [str(extract_dir)]
        subprocess.check_call(extract_command)

        snapper_path = Path('.snapshots') / '1' / 'snapshot'
        test_path = extract_dir / 'mnt' / 'btrfs' / snapper_path / test_file
        assert test_path.exists()
        with test_path.open() as f:
            assert 'stuff' == f.read()

        extract_dir = temporary_directory / 'extract2'
        extract_dir.mkdir()

        extract_command = extract_command_base + [str(extract_dir), '--rename-snapshots']
        subprocess.check_call(extract_command)

        test_path = extract_dir / 'mnt' / 'btrfs' / test_file
        assert test_path.exists()
        with test_path.open() as f:
            assert 'stuff' == f.read()
