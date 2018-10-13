import json
import os
import shutil
import subprocess
import sys
import tempfile


def generate_configuration(config_path, repository_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing (including injecting the given repository path).
    '''
    subprocess.check_call(f'generate-borgmatic-config --destination {config_path}'.split(' '))
    config = (
        open(config_path)
        .read()
        .replace('user@backupserver:sourcehostname.borg', repository_path)
        .replace('- /home', f'- {config_path}')
        .replace('- /etc', '')
        .replace('- /var/log/syslog*', '')
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_borgmatic_command():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    try:
        subprocess.check_call(
            f'borg init --encryption repokey {repository_path}'.split(' '),
            env={'BORG_PASSPHRASE': '', **os.environ},
        )

        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path)

        # Run borgmatic to generate a backup archive, and then list it to make sure it exists.
        subprocess.check_call(f'borgmatic --config {config_path}'.split(' '))
        output = subprocess.check_output(
            f'borgmatic --config {config_path} --list --json'.split(' '),
            encoding=sys.stdout.encoding,
        )
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1

        # Also exercise the info flag.
        output = subprocess.check_output(
            f'borgmatic --config {config_path} --info --json'.split(' '),
            encoding=sys.stdout.encoding,
        )
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert 'repository' in parsed_output[0]
    finally:
        shutil.rmtree(temporary_directory)
