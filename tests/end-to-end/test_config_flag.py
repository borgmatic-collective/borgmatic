import os
import shlex
import shutil
import subprocess
import tempfile


def generate_configuration(config_path):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing (including injecting the given repository path and tacking on an encryption
    passphrase). But don't actually set the repository path, as that's done on the command-line
    below.
    '''
    subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
    config = (
        open(config_path)
        .read()
        .replace('- ssh://user@backupserver/./{fqdn}', '')  # noqa: FS003
        .replace('- /var/local/backups/local.borg', '')
        .replace('- /home/user/path with spaces', '')
        .replace('- /home', f'- {config_path}')
        .replace('- /etc', '')
        .replace('- /var/log/syslog*', '')
        + 'encryption_passphrase: "test"'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_config_flags_do_not_error():
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path)

        subprocess.check_call(
            shlex.split(
                f'borgmatic -v 2 --config {config_path} --repositories "[{{path: {repository_path}, label: repo}}]" repo-create --encryption repokey'
            )
        )

        subprocess.check_call(
            shlex.split(
                f'borgmatic create --config {config_path} --repositories[0].path "{repository_path}"'
            )
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
