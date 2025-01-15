import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest


def generate_configuration_with_source_directories(config_path, repository_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing, including updating the source directories, injecting the given repository
    path, and tacking on an encryption passphrase.
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
        + '\nencryption_passphrase: "test"'
        # Disable automatic storage of config files so we can test storage and extraction manually.
        + '\nbootstrap:\n  store_config_files: false'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def generate_configuration_with_patterns(config_path, repository_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing, including adding patterns, injecting the given repository path, and tacking
    on an encryption passphrase.
    '''
    subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
    config = (
        open(config_path)
        .read()
        .replace('ssh://user@backupserver/./sourcehostname.borg', repository_path)
        .replace('- path: /mnt/backup', '')
        .replace('label: local', '')
        .replace('source_directories:', '')
        .replace('- /home/user/path with spaces', '')
        .replace('- /home', '')
        .replace('- /etc', '')
        .replace('- /var/log/syslog*', '')
        + f'\npatterns: ["R {config_path}"]'
        + '\nencryption_passphrase: "test"'
        # Disable automatic storage of config files so we can test storage and extraction manually.
        + '\nbootstrap:\n  store_config_files: false'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


@pytest.mark.parametrize(
    'generate_configuration',
    (generate_configuration_with_source_directories, generate_configuration_with_patterns),
)
def test_borgmatic_command(generate_configuration):
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    extract_path = os.path.join(temporary_directory, 'extract')

    original_working_directory = os.getcwd()
    os.mkdir(extract_path)
    os.chdir(extract_path)

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path)

        subprocess.check_call(
            f'borgmatic -v 2 --config {config_path} repo-create --encryption repokey'.split(' ')
        )

        # Run borgmatic to generate a backup archive, and then list it to make sure it exists.
        subprocess.check_call(f'borgmatic --config {config_path}'.split(' '))
        output = subprocess.check_output(
            f'borgmatic --config {config_path} list --json'.split(' ')
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Extract the created archive into the current (temporary) directory, and confirm that the
        # extracted file looks right.
        output = subprocess.check_output(
            f'borgmatic --config {config_path} extract --archive {archive_name}'.split(' '),
        ).decode(sys.stdout.encoding)
        extracted_config_path = os.path.join(extract_path, config_path)
        assert open(extracted_config_path).read() == open(config_path).read()

        # Exercise the info action.
        output = subprocess.check_output(
            f'borgmatic --config {config_path} info --json'.split(' '),
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert 'repository' in parsed_output[0]
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
