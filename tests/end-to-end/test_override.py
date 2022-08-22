import os
import shutil
import subprocess
import tempfile


def generate_configuration(config_path, repository_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing (including injecting the given repository path and tacking on an encryption
    passphrase).
    '''
    subprocess.check_call(
        'generate-borgmatic-config --destination {}'.format(config_path).split(' ')
    )
    config = (
        open(config_path)
        .read()
        .replace('ssh://user@backupserver/./sourcehostname.borg', repository_path)
        .replace('- ssh://user@backupserver/./{fqdn}', '')
        .replace('- /var/local/backups/local.borg', '')
        .replace('- /home/user/path with spaces', '')
        .replace('- /home', '- {}'.format(config_path))
        .replace('- /etc', '')
        .replace('- /var/log/syslog*', '')
        + 'storage:\n    encryption_passphrase: "test"'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_override_get_normalized():
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path)

        subprocess.check_call(
            f'borgmatic -v 2 --config {config_path} init --encryption repokey'.split(' ')
        )

        # Run borgmatic with an override structured for an outdated config file format. If
        # normalization is working, it should get normalized and shouldn't error.
        subprocess.check_call(
            f'borgmatic create --config {config_path} --override hooks.healthchecks=http://localhost:8888/someuuid'.split(
                ' '
            )
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
