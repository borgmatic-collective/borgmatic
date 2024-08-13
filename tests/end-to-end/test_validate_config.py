import os
import subprocess
import sys
import tempfile


def test_validate_config_command_with_valid_configuration_succeeds():
    with tempfile.TemporaryDirectory() as temporary_directory:
        config_path = os.path.join(temporary_directory, 'test.yaml')

        subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
        exit_code = subprocess.call(f'borgmatic config validate --config {config_path}'.split(' '))

        assert exit_code == 0


def test_validate_config_command_with_invalid_configuration_fails():
    with tempfile.TemporaryDirectory() as temporary_directory:
        config_path = os.path.join(temporary_directory, 'test.yaml')

        subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
        config = open(config_path).read().replace('keep_daily: 7', 'keep_daily: "7"')
        config_file = open(config_path, 'w')
        config_file.write(config)
        config_file.close()

        exit_code = subprocess.call(f'borgmatic config validate --config {config_path}'.split(' '))

        assert exit_code == 1


def test_validate_config_command_with_show_flag_displays_configuration():
    with tempfile.TemporaryDirectory() as temporary_directory:
        config_path = os.path.join(temporary_directory, 'test.yaml')

        subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
        output = subprocess.check_output(
            f'borgmatic config validate --config {config_path} --show'.split(' ')
        ).decode(sys.stdout.encoding)

        assert 'repositories:' in output
