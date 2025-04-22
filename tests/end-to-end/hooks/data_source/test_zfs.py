import os
import shutil
import subprocess
import sys
import tempfile


def generate_configuration(config_path, repository_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing (including injecting the given repository path and tacking on an encryption
    passphrase).
    '''
    subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
    config = (
        open(config_path)
        .read()
        .replace('ssh://user@backupserver/./sourcehostname.borg', repository_path)
        .replace('- path: /mnt/backup', '')
        .replace('label: local', '')
        .replace('- /home', f'- {config_path}')
        .replace('- /etc', '- /e2e/pool/dataset/subdir')
        .replace('- /var/log/syslog*', '')
        + 'encryption_passphrase: "test"\n'
        + 'zfs:\n'
        + '    zfs_command: python3 /app/tests/end-to-end/commands/fake_zfs.py\n'
        + '    mount_command: python3 /app/tests/end-to-end/commands/fake_mount.py\n'
        + '    umount_command: python3 /app/tests/end-to-end/commands/fake_umount.py'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_zfs_create_and_list():
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path)

        subprocess.check_call(
            f'borgmatic -v 2 --config {config_path} repo-create --encryption repokey'.split(' ')
        )

        # Run a create action to exercise ZFS snapshotting and backup.
        subprocess.check_call(f'borgmatic -v 2 --config {config_path} create'.split(' '))

        # List the resulting archive and assert that the snapshotted files are there.
        output = subprocess.check_output(
            f'borgmatic --config {config_path} list --archive latest'.split(' ')
        ).decode(sys.stdout.encoding)

        assert 'e2e/pool/dataset/subdir/file.txt' in output

        # Assert that the snapshot has been deleted.
        assert not subprocess.check_output(
            'python3 /app/tests/end-to-end/commands/fake_zfs.py list -H -t snapshot'.split(' ')
        )
    finally:
        shutil.rmtree(temporary_directory)
