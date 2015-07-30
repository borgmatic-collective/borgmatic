import subprocess


def test_setup_version_matches_news_version():
    setup_version = subprocess.check_output(('python', 'setup.py', '--version')).decode('ascii')
    news_version = open('NEWS').readline()

    assert setup_version == news_version
