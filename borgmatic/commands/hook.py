import subprocess


def execute_hook(commands):
    if commands:
        for cmd in commands:
            subprocess.check_call(cmd, shell=True)
