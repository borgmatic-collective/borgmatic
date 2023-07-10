import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest


def write_configuration(
    source_directory,
    config_path,
    repository_path,
    borgmatic_source_directory,
    postgresql_dump_format='custom',
    mongodb_dump_format='archive',
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing. This includes injecting the given repository path, borgmatic source directory for
    storing database dumps, dump format (for PostgreSQL), and encryption passphrase.
    '''
    config = f'''
source_directories:
    - {source_directory}
repositories:
    - {repository_path}
borgmatic_source_directory: {borgmatic_source_directory}

encryption_passphrase: "test"

postgresql_databases:
    - name: test
      hostname: postgresql
      username: postgres
      password: test
      format: {postgresql_dump_format}
    - name: all
      hostname: postgresql
      username: postgres
      password: test
    - name: all
      format: custom
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
    - name: all
      format: sql
      hostname: mysql
      username: root
      password: test
mongodb_databases:
    - name: test
      hostname: mongodb
      username: root
      password: test
      authentication_database: admin
      format: {mongodb_dump_format}
    - name: all
      hostname: mongodb
      username: root
      password: test
sqlite_databases:
    - name: sqlite_test
      path: /tmp/sqlite_test.db
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config)


def write_custom_restore_configuration(
    source_directory,
    config_path,
    repository_path,
    borgmatic_source_directory,
    postgresql_dump_format='custom',
    mongodb_dump_format='archive',
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing with custom restore options. This includes a custom restore_hostname, restore_port,
    restore_username, restore_password and restore_path.
    '''
    config = f'''
source_directories:
    - {source_directory}
repositories:
    - {repository_path}
borgmatic_source_directory: {borgmatic_source_directory}

encryption_passphrase: "test"

postgresql_databases:
    - name: test
      hostname: postgresql
      username: postgres
      password: test
      format: {postgresql_dump_format}
      restore_hostname: postgresql2
      restore_port: 5433
      restore_username: postgres2
      restore_password: test2
mysql_databases:
    - name: test
      hostname: mysql
      username: root
      password: test
      restore_hostname: mysql2
      restore_port: 3307
      restore_username: root
      restore_password: test2
mongodb_databases:
    - name: test
      hostname: mongodb
      username: root
      password: test
      authentication_database: admin
      format: {mongodb_dump_format}
      restore_hostname: mongodb2
      restore_port: 27018
      restore_username: root2
      restore_password: test2
sqlite_databases:
    - name: sqlite_test
      path: /tmp/sqlite_test.db
      restore_path: /tmp/sqlite_test2.db
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config)


def write_simple_custom_restore_configuration(
    source_directory,
    config_path,
    repository_path,
    borgmatic_source_directory,
    postgresql_dump_format='custom',
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing with custom restore options, but this time using CLI arguments. This includes a
    custom restore_hostname, restore_port, restore_username and restore_password as we only test
    these options for PostgreSQL.
    '''
    config = f'''
source_directories:
    - {source_directory}
repositories:
    - {repository_path}
borgmatic_source_directory: {borgmatic_source_directory}

encryption_passphrase: "test"

postgresql_databases:
    - name: test
      hostname: postgresql
      username: postgres
      password: test
      format: {postgresql_dump_format}
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config)


def test_database_dump_and_restore():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    borgmatic_source_directory = os.path.join(temporary_directory, '.borgmatic')

    # Write out a special file to ensure that it gets properly excluded and Borg doesn't hang on it.
    os.mkfifo(os.path.join(temporary_directory, 'special_file'))

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_configuration(
            temporary_directory, config_path, repository_path, borgmatic_source_directory
        )

        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'rcreate', '--encryption', 'repokey']
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json']
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the database from the archive.
        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'restore', '--archive', archive_name]
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)


def test_database_dump_and_restore_with_restore_cli_arguments():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    borgmatic_source_directory = os.path.join(temporary_directory, '.borgmatic')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_simple_custom_restore_configuration(
            temporary_directory, config_path, repository_path, borgmatic_source_directory
        )

        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'rcreate', '--encryption', 'repokey']
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json']
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the database from the archive.
        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'restore',
                '--archive',
                archive_name,
                '--hostname',
                'postgresql2',
                '--port',
                '5433',
                '--username',
                'postgres2',
                '--password',
                'test2',
            ]
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)


def test_database_dump_and_restore_with_restore_configuration_options():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    borgmatic_source_directory = os.path.join(temporary_directory, '.borgmatic')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_custom_restore_configuration(
            temporary_directory, config_path, repository_path, borgmatic_source_directory
        )

        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'rcreate', '--encryption', 'repokey']
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json']
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the database from the archive.
        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'restore', '--archive', archive_name]
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)


def test_database_dump_and_restore_with_directory_format():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    borgmatic_source_directory = os.path.join(temporary_directory, '.borgmatic')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_configuration(
            temporary_directory,
            config_path,
            repository_path,
            borgmatic_source_directory,
            postgresql_dump_format='directory',
            mongodb_dump_format='directory',
        )

        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'rcreate', '--encryption', 'repokey']
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Restore the database from the archive.
        subprocess.check_call(
            ['borgmatic', '--config', config_path, 'restore', '--archive', 'latest']
        )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)


def test_database_dump_with_error_causes_borgmatic_to_exit():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    borgmatic_source_directory = os.path.join(temporary_directory, '.borgmatic')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_configuration(
            temporary_directory, config_path, repository_path, borgmatic_source_directory
        )

        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'rcreate', '--encryption', 'repokey']
        )

        # Run borgmatic with a config override such that the database dump fails.
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call(
                [
                    'borgmatic',
                    'create',
                    '--config',
                    config_path,
                    '-v',
                    '2',
                    '--override',
                    "hooks.postgresql_databases=[{'name': 'nope'}]",  # noqa: FS003
                ]
            )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
