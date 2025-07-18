import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading

import pytest


def generate_configuration(config_path, repository_path, monitoring_hook_configuration):
    '''
    Generate borgmatic configuration into a file at the config path, and update the defaults so as
    to work for testing, including updating the source directories, injecting the given repository
    path, and tacking on an encryption passphrase.
    '''
    subprocess.check_call(f'borgmatic config generate --destination {config_path}'.split(' '))
    config = (
        open(config_path)
        .read()
        .replace('ssh://user@backupserver/./sourcehostname.borg', repository_path)
        .replace('- path: /mnt/backup', '')
        .replace('label: local', '')
        .replace('- /home/user/path with spaces', '')
        .replace('- /home', f'- {config_path}')
        .replace('- /etc', '')
        .replace('- /var/log/syslog*', '')
        + '\nencryption_passphrase: "test"'
        + f'\n{monitoring_hook_configuration}'
    )
    config_file = open(config_path, 'w')
    config_file.write(config)
    config_file.close()


class Web_server(http.server.BaseHTTPRequestHandler):
    def handle_method(self):
        self.send_response(http.HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'')

    def do_GET(self):
        self.handle_method()

    def do_POST(self):
        self.handle_method()


def serve_web_request(count):
    for _ in range(count):
        with http.server.HTTPServer(('localhost', 12345), Web_server) as server:
            server.handle_request()


class Background_web_server:
    def __init__(self, expected_request_count):
        self.expected_request_count = expected_request_count

    def __enter__(self):
        self.thread = threading.Thread(
            target=lambda: serve_web_request(count=self.expected_request_count),
        )
        self.thread.start()

    def __exit__(self, exception, value, traceback):
        self.thread.join()


START_AND_FINISH = 2
START_LOG_AND_FINISH = 3


@pytest.mark.parametrize(
    'monitoring_hook_configuration,expected_request_count',
    (
        (
            'cronhub:\n    ping_url: http://localhost:12345/start/1f5e3410-254c-11e8-b61d-55875966d031',
            START_AND_FINISH,
        ),
        (
            'cronitor:\n    ping_url: http://localhost:12345/d3x0c1',
            START_AND_FINISH,
        ),
        (
            'healthchecks:\n    ping_url: http://localhost:12345/addffa72-da17-40ae-be9c-ff591afb942a',
            START_LOG_AND_FINISH,
        ),
        (
            'loki:\n    url: http://localhost:12345/loki/api/v1/push\n    labels:\n        app: borgmatic',
            START_AND_FINISH,
        ),
        (
            'ntfy:\n    topic: my-unique-topic\n    server: http://localhost:12345\n    states: [start, finish]',
            START_AND_FINISH,
        ),
        (
            'sentry:\n    data_source_name_url: http://5f80ec@localhost:12345/203069\n    monitor_slug: mymonitor',
            START_AND_FINISH,
        ),
        (
            'uptime_kuma:\n    push_url: http://localhost:12345/api/push/abcd1234',
            START_AND_FINISH,
        ),
        (
            'zabbix:\n    itemid: 1\n    server: http://localhost:12345/zabbix/api_jsonrpc.php\n    api_key: mykey\n    states: [start, finish]',
            START_AND_FINISH,
        ),
    ),
)
def test_borgmatic_command(monitoring_hook_configuration, expected_request_count):
    # Create a Borg repository.
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    extract_path = os.path.join(temporary_directory, 'extract')

    original_working_directory = os.getcwd()
    os.mkdir(extract_path)
    os.chdir(extract_path)

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        generate_configuration(config_path, repository_path, monitoring_hook_configuration)

        subprocess.check_call(
            f'borgmatic -v 2 --config {config_path} repo-create --encryption repokey'.split(' '),
        )

        with Background_web_server(expected_request_count):
            # Run borgmatic to generate a backup archive, and then list it to make sure it exists.
            subprocess.check_call(f'borgmatic -v 2 --config {config_path}'.split(' '))
            output = subprocess.check_output(
                f'borgmatic --config {config_path} list --json'.split(' '),
            ).decode(sys.stdout.encoding)
            parsed_output = json.loads(output)

            assert len(parsed_output) == 1
            assert len(parsed_output[0]['archives']) == 1
    finally:
        os.chdir(original_working_directory)
        shutil.rmtree(temporary_directory)
