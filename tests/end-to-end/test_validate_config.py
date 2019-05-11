import os
import subprocess
import tempfile


def test_validate_config_command_with_valid_configuration_succeeds():
    with tempfile.TemporaryDirectory() as temporary_directory:
        config_path = os.path.join(temporary_directory, 'test.yaml')

        subprocess.check_call(
            'generate-borgmatic-config --destination {}'.format(config_path).split(' ')
        )
        exit_code = subprocess.call(
            'validate-borgmatic-config --config {}'.format(config_path).split(' ')
        )

        assert exit_code == 0


def test_validate_config_command_with_invalid_configuration_fails():
    with tempfile.TemporaryDirectory() as temporary_directory:
        config_path = os.path.join(temporary_directory, 'test.yaml')

        subprocess.check_call(
            'generate-borgmatic-config --destination {}'.format(config_path).split(' ')
        )
        config = open(config_path).read().replace('keep_daily: 7', 'keep_daily: "7"')
        config_file = open(config_path, 'w')
        config_file.write(config)
        config_file.close()

        exit_code = subprocess.call(
            'validate-borgmatic-config --config {}'.format(config_path).split(' ')
        )

        assert exit_code == 1
