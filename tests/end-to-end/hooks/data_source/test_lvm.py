import json
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
        .replace('- path: /e2e/mnt/backup', '')
        .replace('label: local', '')
        .replace('- /home/user/path with spaces', '')
        .replace('- /home', f'- {config_path}')
        .replace('- /etc', '- /e2e/mnt/lvolume/subdir')
        .replace('- /var/log/syslog*', '')
        + 'encryption_passphrase: "test"\n'
        + 'lvm:\n'
        + '    lsblk_command: python3 /app/tests/end-to-end/commands/fake_lsblk.py\n'
        + '    lvcreate_command: python3 /app/tests/end-to-end/commands/fake_lvcreate.py\n'
        + '    lvremove_command: python3 /app/tests/end-to-end/commands/fake_lvremove.py\n'
        + '    lvs_command: python3 /app/tests/end-to-end/commands/fake_lvs.py\n'
        + '    mount_command: python3 /app/tests/end-to-end/commands/fake_mount.py\n'
        + '    umount_command: python3 /app/tests/end-to-end/commands/fake_umount.py\n'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_lvm_create_and_list():
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path)

        subprocess.check_call(
            f'borgmatic -v 2 --config {config_path} repo-create --encryption repokey'.split(' '),
        )

        # Run a create action to exercise LVM snapshotting and backup.
        subprocess.check_call(f'borgmatic --config {config_path} create'.split(' '))

        # List the resulting archive and assert that the snapshotted files are there.
        output = subprocess.check_output(
            f'borgmatic --config {config_path} list --archive latest'.split(' '),
        ).decode(sys.stdout.encoding)

        assert 'e2e/mnt/lvolume/subdir/file.txt' in output

        # Assert that the snapshot has been deleted.
        assert not json.loads(
            subprocess.check_output(
                [
                    *'python3 /app/tests/end-to-end/commands/fake_lvs.py --report-format json --options lv_name,lv_path --select'.split(
                        ' ',
                    ),
                    'lv_attr =~ ^s',
                ],
            ),
        )['report'][0]['lv']
    finally:
        shutil.rmtree(temporary_directory)
