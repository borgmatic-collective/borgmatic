import subprocess


def exec_cmd(config):
    if config and config.get('enable_hook', None) is True:
        for cmd in config.get('exec_hook'):
            subprocess.check_call(cmd, shell=True)
