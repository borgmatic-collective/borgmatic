import subprocess


def test_bash_completion_runs_without_error():
    subprocess.check_call('eval "$(borgmatic --bash-completion)"', shell=True)
