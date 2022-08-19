import os
import subprocess
import tempfile


def test_generate_borgmatic_config_with_merging_succeeds():
    with tempfile.TemporaryDirectory() as temporary_directory:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        new_config_path = os.path.join(temporary_directory, 'new.yaml')

        subprocess.check_call(f'generate-borgmatic-config --destination {config_path}'.split(' '))
        subprocess.check_call(
            f'generate-borgmatic-config --source {config_path} --destination {new_config_path}'.split(
                ' '
            )
        )
