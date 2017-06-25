title: borgmatic

<img src="static/borgmatic.svg" alt="borgmatic logo" style="width: 8em; float: right; padding-left: 1em;" />

## Overview

borgmatic (formerly atticmatic) is a simple Python wrapper script for the
[Borg](https://borgbackup.readthedocs.org/en/stable/) backup software that
initiates a backup, prunes any old backups according to a retention policy,
and validates backups for consistency. The script supports specifying your
settings in a declarative configuration file rather than having to put them
all on the command-line, and handles common errors.

Here's an example config file:

```INI
[location]
# Space-separated list of source directories to backup.
# Globs are expanded.
# Spaces in names can be escaped with a backslash.
source_directories: /home /etc /var/log/syslog* /dir\ with\ spaces

# Path to local or remote backup repository.
repository: user@backupserver:sourcehostname.borg

[retention]
# Retention policy for how many backups to keep in each category.
keep_daily: 7
keep_weekly: 4
keep_monthly: 6

[consistency]
# Consistency checks to run, or "disabled" to prevent checks.
checks: repository archives
```

Additionally, exclude patterns can be specified in a separate excludes config
file, one pattern per line.

borgmatic is hosted at <https://torsion.org/borgmatic> with [source code
available](https://torsion.org/hg/borgmatic). It's also mirrored on
[GitHub](https://github.com/witten/borgmatic) and
[BitBucket](https://bitbucket.org/dhelfman/borgmatic) for convenience.


## Setup

To get up and running, follow the [Borg Quick
Start](https://borgbackup.readthedocs.org/en/latest/quickstart.html) to create
a repository on a local or remote host. Note that if you plan to run
borgmatic on a schedule with cron, and you encrypt your Borg repository with
a passphrase instead of a key file, you'll need to set the borgmatic
`encryption_passphrase` configuration variable. See the repository encryption
section of the Quick Start for more info.

If the repository is on a remote host, make sure that your local root user has
key-based ssh access to the desired user account on the remote host.

To install borgmatic, run the following command to download and install it:

    sudo pip install --upgrade borgmatic

Then, download a [sample config
file](https://torsion.org/hg/borgmatic/raw-file/tip/sample/config) and a
[sample excludes
file](https://torsion.org/hg/borgmatic/raw-file/tip/sample/excludes). From the
directory where you downloaded them:

    sudo mkdir /etc/borgmatic/
    sudo mv config excludes /etc/borgmatic/

Lastly, modify the /etc files with your desired configuration.


## Upgrading from atticmatic

You can ignore this section if you're not an atticmatic user (the former name
of borgmatic).

borgmatic only supports Borg now and no longer supports Attic. So if you're
an Attic user, consider switching to Borg. See the [Borg upgrade
command](https://borgbackup.readthedocs.io/en/stable/usage.html#borg-upgrade)
for more information. Then, follow the instructions above about setting up
your borgmatic configuration files.

If you were already using Borg with atticmatic, then you can easily upgrade
from atticmatic to borgmatic. Simply run the following commands:

    sudo pip uninstall atticmatic
    sudo pip install borgmatic

That's it! borgmatic will continue using your /etc/borgmatic configuration
files.

## Usage

You can run borgmatic and start a backup simply by invoking it without
arguments:

    borgmatic

This will also prune any old backups as per the configured retention policy,
and check backups for consistency problems due to things like file damage.

By default, the backup will proceed silently except in the case of errors. But
if you'd like to to get additional information about the progress of the
backup as it proceeds, use the verbosity option:

    borgmatic --verbosity 1

Or, for even more progress spew:

    borgmatic --verbosity 2

If you'd like to see the available command-line arguments, view the help:

    borgmatic --help


## Autopilot

If you want to run borgmatic automatically, say once a day, the you can
configure a job runner to invoke it periodically.

### cron

If you're using cron, download the [sample cron
file](https://torsion.org/hg/borgmatic/raw-file/tip/sample/cron/borgmatic).
Then, from the directory where you downloaded it:

    sudo mv borgmatic /etc/cron.d/borgmatic

You can modify the cron file if you'd like to run borgmatic more or less frequently.

### systemd

If you're using systemd instead of cron to run jobs, download the [sample
systemd service
file](https://torsion.org/hg/borgmatic/raw-file/tip/sample/systemd/borgmatic.service)
and the [sample systemd timer
file](https://torsion.org/hg/borgmatic/raw-file/tip/sample/systemd/borgmatic.timer).
Then, from the directory where you downloaded them:

    sudo mv borgmatic.service borgmatic.timer /etc/systemd/system/
    sudo systemctl enable borgmatic.timer
    sudo systemctl start borgmatic.timer

Feel free to modify the timer file based on how frequently you'd like
borgmatic to run.


## Running tests

First install tox, which is used for setting up testing environments:

    pip install tox

Then, to actually run tests, run:

    tox


## Troubleshooting

### Broken pipe with remote repository

When running borgmatic on a large remote repository, you may receive errors
like the following, particularly while "borg check" is validating backups for
consistency:

    Write failed: Broken pipe
    borg: Error: Connection closed by remote host

This error can be caused by an ssh timeout, which you can rectify by adding
the following to the ~/.ssh/config file on the client:

    Host *
        ServerAliveInterval 120

This should make the client keep the connection alive while validating
backups.


## Issues and feedback

Got an issue or an idea for a feature enhancement? Check out the [borgmatic
issue tracker](https://tree.taiga.io/project/witten-borgmatic/issues?page=1&status=399951,399952,399955). In
order to create a new issue or comment on an issue, you'll need to [login
first](https://tree.taiga.io/login).

Other questions or comments? Contact <mailto:witten@torsion.org>.
