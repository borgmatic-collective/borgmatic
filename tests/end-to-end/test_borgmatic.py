import json
import os
import subprocess
import sys


def generate_configuration():
    subprocess.check_call('generate-borgmatic-config --destination test.yaml'.split(' '))
    config = (
        open('test.yaml')
        .read()
        .replace('user@backupserver:sourcehostname.borg', 'test.borg')
        .replace('- /etc', '- /app')
        .replace('- /var/log/syslog*', '')
    )
    config_file = open('test.yaml', 'w')
    config_file.write(config)
    config_file.close()


def test_borgmatic_command():
    # Create a Borg repository.
    subprocess.check_call(
        'borg init --encryption repokey test.borg'.split(' '),
        env={'BORG_PASSPHRASE': '', **os.environ},
    )

    # Generate borgmatic configuration, and update the defaults so as to work for this test.
    generate_configuration()

    # Run borgmatic to generate a backup archive, and then list it to make sure it exists.
    subprocess.check_call('borgmatic --config test.yaml'.split(' '))
    output = subprocess.check_output(
        'borgmatic --config test.yaml --list --json'.split(' '), encoding=sys.stdout.encoding
    )
    parsed_output = json.loads(output)

    assert len(parsed_output) == 1
    assert len(parsed_output[0]['archives']) == 1
