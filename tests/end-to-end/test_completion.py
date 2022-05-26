import subprocess


def test_bash_completion_runs_without_error():
    subprocess.check_call('borgmatic --bash-completion | bash', shell=True)
