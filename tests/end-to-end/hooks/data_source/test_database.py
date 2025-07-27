import json
import os
import shutil
import subprocess
import sys
import tempfile

import pymongo
import pytest
import ruamel.yaml

from borgmatic.hooks.data_source import utils


def write_configuration(
    source_directory,
    config_path,
    repository_path,
    user_runtime_directory,
    postgresql_dump_format='custom',
    postgresql_all_dump_format=None,
    mariadb_mysql_all_dump_format=None,
    mongodb_dump_format='archive',
    use_containers=False,
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing. This includes injecting the given repository path, borgmatic source directory for
    storing database dumps, dump format (for PostgreSQL), and encryption passphrase.
    '''
    postgresql_all_format_option = (
        f'format: {postgresql_all_dump_format}' if postgresql_all_dump_format else ''
    )
    mariadb_mysql_dump_format_option = (
        f'format: {mariadb_mysql_all_dump_format}' if mariadb_mysql_all_dump_format else ''
    )

    hostname_option = 'container' if use_containers else 'hostname'

    config_yaml = f'''
source_directories:
    - {source_directory}
repositories:
    - path: {repository_path}
user_runtime_directory: {user_runtime_directory}

encryption_passphrase: "test"

postgresql_databases:
    - name: test
      {hostname_option}: postgresql
      username: postgres
      password: test
      format: {postgresql_dump_format}
    - name: all
      {postgresql_all_format_option}
      {hostname_option}: postgresql
      username: postgres
      password: test
mariadb_databases:
    - name: test
      {hostname_option}: mariadb
      username: root
      password: test
    - name: all
      {mariadb_mysql_dump_format_option}
      {hostname_option}: mariadb
      username: root
      password: test
mysql_databases:
    - name: test
      {hostname_option}: not-actually-mysql
      username: root
      password: test
    - name: all
      {mariadb_mysql_dump_format_option}
      {hostname_option}: not-actually-mysql
      username: root
      password: test
mongodb_databases:
    - name: test
      {hostname_option}: mongodb
      username: root
      password: test
      authentication_database: admin
      format: {mongodb_dump_format}
    - name: all
      {hostname_option}: mongodb
      username: root
      password: test
sqlite_databases:
    - name: sqlite_test
      path: /tmp/sqlite_test.db
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config_yaml)

    return ruamel.yaml.YAML(typ='safe').load(config_yaml)


@pytest.mark.parametrize(
    'postgresql_all_dump_format,mariadb_mysql_all_dump_format',
    (
        (None, None),
        ('custom', 'sql'),
    ),
)
def write_custom_restore_configuration(
    source_directory,
    config_path,
    repository_path,
    user_runtime_directory,
    postgresql_dump_format='custom',
    postgresql_all_dump_format=None,
    mariadb_mysql_all_dump_format=None,
    mongodb_dump_format='archive',
    use_containers=False,
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing with custom restore options. This includes a custom restore_hostname, restore_port,
    restore_username, restore_password and restore_path.
    '''

    hostname_option = 'container' if use_containers else 'hostname'

    config_yaml = f'''
source_directories:
    - {source_directory}
repositories:
    - path: {repository_path}
user_runtime_directory: {user_runtime_directory}

encryption_passphrase: "test"

postgresql_databases:
    - name: test
      {hostname_option}: postgresql
      username: postgres
      password: test
      format: {postgresql_dump_format}
      restore_{hostname_option}: postgresql2
      restore_port: 5433
      restore_password: test2
mariadb_databases:
    - name: test
      {hostname_option}: mariadb
      username: root
      password: test
      restore_{hostname_option}: mariadb2
      restore_port: 3307
      restore_username: root
      restore_password: test2
mysql_databases:
    - name: test
      {hostname_option}: not-actually-mysql
      username: root
      password: test
      restore_{hostname_option}: not-actually-mysql2
      restore_port: 3307
      restore_username: root
      restore_password: test2
mongodb_databases:
    - name: test
      {hostname_option}: mongodb
      username: root
      password: test
      authentication_database: admin
      format: {mongodb_dump_format}
      restore_{hostname_option}: mongodb2
      restore_port: 27018
      restore_username: root2
      restore_password: test2
sqlite_databases:
    - name: sqlite_test
      path: /tmp/sqlite_test.db
      restore_path: /tmp/sqlite_test2.db
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config_yaml)

    return ruamel.yaml.YAML(typ='safe').load(config_yaml)


def write_simple_custom_restore_configuration(
    source_directory,
    config_path,
    repository_path,
    user_runtime_directory,
    postgresql_dump_format='custom',
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing with custom restore options, but this time using CLI arguments. This includes a
    custom restore_hostname, restore_port, restore_username and restore_password as we only test
    these options for PostgreSQL.
    '''
    config_yaml = f'''
source_directories:
    - {source_directory}
repositories:
    - path: {repository_path}
user_runtime_directory: {user_runtime_directory}

encryption_passphrase: "test"

postgresql_databases:
    - name: test
      hostname: postgresql
      username: postgres
      password: test
      format: {postgresql_dump_format}
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config_yaml)

    return ruamel.yaml.YAML(typ='safe').load(config_yaml)


def get_connection_params(database, use_restore_options=False):
    hostname = utils.resolve_database_option('hostname', database, restore=use_restore_options)
    port = utils.resolve_database_option('port', database, restore=use_restore_options)
    username = utils.resolve_database_option('username', database, restore=use_restore_options)
    password = utils.resolve_database_option('password', database, restore=use_restore_options)

    return (hostname, port, username, password)


def run_postgresql_command(command, config, use_restore_options=False):
    (hostname, port, username, password) = get_connection_params(
        config['postgresql_databases'][0],
        use_restore_options,
    )

    subprocess.check_call(
        [
            '/usr/bin/psql',
            f'--host={hostname}',
            f'--port={port or 5432}',
            f"--username={username or 'root'}",
            f'--command={command}',
            'test',
        ],
        env={'PGPASSWORD': password},
    )


def run_mariadb_command(command, config, use_restore_options=False, binary_name='mariadb'):
    (hostname, port, username, password) = get_connection_params(
        config[f'{binary_name}_databases'][0],
        use_restore_options,
    )

    subprocess.check_call(
        [
            f'/usr/bin/{binary_name}',
            f'--host={hostname}',
            f'--port={port or 3306}',
            f'--user={username}',
            f'--execute={command}',
            'test',
        ],
        env={'MYSQL_PWD': password},
    )


def get_mongodb_database_client(config, use_restore_options=False):
    (hostname, port, username, password) = get_connection_params(
        config['mongodb_databases'][0],
        use_restore_options,
    )

    return pymongo.MongoClient(f'mongodb://{username}:{password}@{hostname}:{port or 27017}').test


def run_sqlite_command(command, config, use_restore_options=False):
    database = config['sqlite_databases'][0]
    path = (database.get('restore_path') if use_restore_options else None) or database.get('path')

    subprocess.check_call(
        [
            '/usr/bin/sqlite3',
            path,
            command,
            '.exit',
        ],
    )


DEFAULT_HOOK_NAMES = {'postgresql', 'mariadb', 'mysql', 'mongodb', 'sqlite'}


def create_test_tables(config, use_restore_options=False):
    '''
    Create test tables for borgmatic to dump and backup.
    '''
    command = 'create table test{id} (thing int); insert into test{id} values (1);'

    if 'postgresql_databases' in config:
        run_postgresql_command(command.format(id=1), config, use_restore_options)

    if 'mariadb_databases' in config:
        run_mariadb_command(command.format(id=2), config, use_restore_options)

    if 'mysql_databases' in config:
        run_mariadb_command(command.format(id=3), config, use_restore_options, binary_name='mysql')

    if 'mongodb_databases' in config:
        get_mongodb_database_client(config, use_restore_options)['test4'].insert_one({'thing': 1})

    if 'sqlite_databases' in config:
        run_sqlite_command(command.format(id=5), config, use_restore_options)


def drop_test_tables(config, use_restore_options=False):
    '''
    Drop the test tables in preparation for borgmatic restoring them.
    '''
    command = 'drop table if exists test{id};'

    if 'postgresql_databases' in config:
        run_postgresql_command(command.format(id=1), config, use_restore_options)

    if 'mariadb_databases' in config:
        run_mariadb_command(command.format(id=2), config, use_restore_options)

    if 'mysql_databases' in config:
        run_mariadb_command(command.format(id=3), config, use_restore_options, binary_name='mysql')

    if 'mongodb_databases' in config:
        get_mongodb_database_client(config, use_restore_options)['test4'].drop()

    if 'sqlite_databases' in config:
        run_sqlite_command(command.format(id=5), config, use_restore_options)


def select_test_tables(config, use_restore_options=False):
    '''
    Select the test tables to make sure they exist.

    Raise if the expected tables cannot be selected, for instance if a restore hasn't worked as
    expected.
    '''
    command = 'select count(*) from test{id};'

    if 'postgresql_databases' in config:
        run_postgresql_command(command.format(id=1), config, use_restore_options)

    if 'mariadb_databases' in config:
        run_mariadb_command(command.format(id=2), config, use_restore_options)

    if 'mysql_databases' in config:
        run_mariadb_command(command.format(id=3), config, use_restore_options, binary_name='mysql')

    if 'mongodb_databases' in config:
        assert (
            get_mongodb_database_client(config, use_restore_options)['test4'].count_documents(
                filter={},
            )
            > 0
        )

    if 'sqlite_databases' in config:
        run_sqlite_command(command.format(id=5), config, use_restore_options)


def test_database_dump_and_restore():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    # Write out a special file to ensure that it gets properly excluded and Borg doesn't hang on it.
    os.mkfifo(os.path.join(temporary_directory, 'special_file'))

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        config = write_configuration(
            temporary_directory,
            config_path,
            repository_path,
            temporary_directory,
        )
        create_test_tables(config)
        select_test_tables(config)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
        )

        # Run borgmatic to generate a backup archive including database dumps.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json'],
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the databases from the archive.
        drop_test_tables(config)
        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'restore', '--archive', archive_name],
        )

        # Ensure the test tables have actually been restored.
        select_test_tables(config)
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
        drop_test_tables(config)


def test_database_dump_and_restore_with_restore_cli_flags():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        config = write_simple_custom_restore_configuration(
            temporary_directory,
            config_path,
            repository_path,
            temporary_directory,
        )
        create_test_tables(config)
        select_test_tables(config)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json'],
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the database from the archive.
        drop_test_tables(config)
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
                '--password',
                'test2',
            ],
        )

        # Ensure the test tables have actually been restored. But first modify the config to contain
        # the altered restore values from the borgmatic command above. This ensures that the test
        # tables are selected from the correct database.
        database = config['postgresql_databases'][0]
        database['restore_hostname'] = 'postgresql2'
        database['restore_port'] = '5433'
        database['restore_password'] = 'test2'

        select_test_tables(config, use_restore_options=True)
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
        drop_test_tables(config)
        drop_test_tables(config, use_restore_options=True)


def test_database_dump_and_restore_with_restore_configuration_options():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        config = write_custom_restore_configuration(
            temporary_directory,
            config_path,
            repository_path,
            temporary_directory,
        )
        create_test_tables(config)
        select_test_tables(config)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json'],
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the database from the archive.
        drop_test_tables(config)
        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'restore', '--archive', archive_name],
        )

        # Ensure the test tables have actually been restored.
        select_test_tables(config, use_restore_options=True)
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
        drop_test_tables(config)
        drop_test_tables(config, use_restore_options=True)


def test_database_dump_and_restore_with_directory_format():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        config = write_configuration(
            temporary_directory,
            config_path,
            repository_path,
            temporary_directory,
            postgresql_dump_format='directory',
            mongodb_dump_format='directory',
        )
        create_test_tables(config)
        select_test_tables(config)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
        )

        # Run borgmatic to generate a backup archive including a database dump.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Restore the database from the archive.
        drop_test_tables(config)
        subprocess.check_call(
            ['borgmatic', '--config', config_path, 'restore', '--archive', 'latest'],
        )

        # Ensure the test tables have actually been restored.
        select_test_tables(config)
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
        drop_test_tables(config)


def test_database_dump_with_error_causes_borgmatic_to_exit():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        write_configuration(temporary_directory, config_path, repository_path, temporary_directory)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
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
                    "hooks.postgresql_databases=[{'name': 'nope'}]",
                ],
            )
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)


def test_database_dump_and_restore_containers():
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')

    original_working_directory = os.getcwd()
    original_path = os.environ.get('PATH', '')

    os.environ['PATH'] = f'/app/tests/end-to-end/commands:{original_path}'

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        config = write_configuration(
            temporary_directory,
            config_path,
            repository_path,
            temporary_directory,
            use_containers=True,
        )
        create_test_tables(config)
        select_test_tables(config)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
        )

        # Run borgmatic to generate a backup archive including database dumps.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json'],
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the databases from the archive.
        drop_test_tables(config)
        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'restore', '--archive', archive_name],
        )

        # Ensure the test tables have actually been restored.
        select_test_tables(config)
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
        drop_test_tables(config)
        os.environ['PATH'] = original_path
