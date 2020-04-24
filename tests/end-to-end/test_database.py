import json
import os
import shutil
import subprocess
import sys
import tempfile


def write_configuration(config_path, repository_path, borgmatic_source_directory):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing. This includes injecting the given repository path, borgmatic source directory for
    storing database dumps, and encryption passphrase.
    '''
    config = '''
location:
    source_directories:
        - {}
    repositories:
        - {}
    borgmatic_source_directory: {}

storage:
    encryption_passphrase: "test"

hooks:
    postgresql_databases:
        - name: test
          hostname: postgresql
          username: postgres
          password: test
        - name: all
          hostname: postgresql
          username: postgres
          password: test
    mysql_databases:
        - name: test
          hostname: mysql
          username: root
          password: test
        - name: all
          hostname: mysql
          username: root
          password: test
'''.format(
        config_path, repository_path, borgmatic_source_directory
    )

    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


def test_database_dump_and_restore():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    borgmatic_source_directory = os.path.join(temporary_directory, '.borgmatic')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_configuration(config_path, repository_path, borgmatic_source_directory)

        subprocess.check_call(
            'borgmatic -v 2 --config {} init --encryption repokey'.format(config_path).split(' ')
        )

        # Run borgmatic to generate a backup archive including a database dump
        subprocess.check_call('borgmatic create --config {} -v 2'.format(config_path).split(' '))

        # Get the created archive name.
        output = subprocess.check_output(
            'borgmatic --config {} list --json'.format(config_path).split(' ')
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the database from the archive.
        subprocess.check_call(
            'borgmatic --config {} restore --archive {}'.format(config_path, archive_name).split(
                ' '
            )
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
