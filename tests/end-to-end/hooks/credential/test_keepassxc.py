import json
import os
import shutil
import subprocess
import sys
import tempfile


def generate_configuration(config_path, repository_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing, including updating the source directories, injecting the given repository
    path, and tacking on an encryption passphrase loaded from keepassxc-cli.
    '''
    subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
    config = (
        open(config_path)
        .read()
        .replace('ssh://user@backupserver/./sourcehostname.borg', repository_path)
        .replace('- path: /mnt/backup', '')
        .replace('label: local', '')
        .replace('- /home/user/path with spaces', '')
        .replace('- /home', f'- {config_path}')
        .replace('- /etc', '')
        .replace('- /var/log/syslog*', '')
        + '\nencryption_passphrase: "{credential keepassxc keys.kdbx mypassword}"'
        + '\nkeepassxc:\n    keepassxc_cli_command: python3 /app/tests/end-to-end/commands/fake_keepassxc_cli.py'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_keepassxc_password():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()
    os.chdir(temporary_directory)

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path)

        database_path = os.path.join(temporary_directory, 'keys.kdbx')
        with open(database_path, 'w') as database_file:
            database_file.write('fake KeePassXC database to pacify file existence check')

        subprocess.check_call(
            f'borgmatic -v 2 --config {config_path} repo-create --encryption repokey'.split(' '),
        )

        # Run borgmatic to generate a backup archive, and then list it to make sure it exists.
        subprocess.check_call(
            f'borgmatic --config {config_path}'.split(' '),
        )
        output = subprocess.check_output(
            f'borgmatic --config {config_path} list --json'.split(' '),
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
