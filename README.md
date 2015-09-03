title: Atticmatic

## Overview

atticmatic is a simple Python wrapper script for the
[Attic](https://attic-backup.org/) and
[Borg](https://borgbackup.github.io/borgbackup/) backup software that
initiates a backup, prunes any old backups according to a retention policy,
and validates backups for consistency. The script supports specifying your
settings in a declarative configuration file rather than having to put them
all on the command-line, and handles common errors.

Here's an example config file:

    [location]
    # Space-separated list of source directories to backup.
    source_directories: /home /etc

    # Path to local or remote backup repository.
    repository: user@backupserver:sourcehostname.attic

    [retention]
    # Retention policy for how many backups to keep in each category.
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6

    [consistency]
    # Consistency checks to run, or "disabled" to prevent checks.
    checks: repository archives

Additionally, exclude patterns can be specified in a separate excludes config
file, one pattern per line.

atticmatic is hosted at <https://torsion.org/atticmatic> with [source code
available](https://torsion.org/hg/atticmatic). It's also mirrored on
[GitHub](https://github.com/witten/atticmatic) and
[BitBucket](https://bitbucket.org/dhelfman/atticmatic) for convenience.


## Setup

To get up and running, follow the [Attic Quick
Start](https://attic-backup.org/quickstart.html) or the [Borg Quick
Start](https://borgbackup.github.io/borgbackup/quickstart.html) to create a
repository on a local or remote host. Note that if you plan to run atticmatic
on a schedule with cron, and you encrypt your attic repository with a
passphrase instead of a key file, you'll need to set the atticmatic
`encryption_passphrase` configuration variable. See the repository encryption
section of the Quick Start for more info.

If the repository is on a remote host, make sure that your local root user has
key-based ssh access to the desired user account on the remote host.

To install atticmatic, run the following command to download and install it:

    sudo pip install --upgrade atticmatic

If you are using Attic, copy the following configuration files:

    sudo cp sample/atticmatic.cron /etc/cron.d/atticmatic
    sudo mkdir /etc/atticmatic/
    sudo cp sample/config sample/excludes /etc/atticmatic/

If you are using Borg, copy the files like this instead:

    sudo cp sample/borgmatic.cron /etc/cron.d/borgmatic
    sudo mkdir /etc/borgmatic/
    sudo cp sample/config sample/excludes /etc/borgmatic/

Lastly, modify the /etc files with your desired configuration.


## Usage

You can run atticmatic and start a backup simply by invoking it without
arguments:

    atticmatic

Or, if you're using Borg, use this command instead to make use of the Borg
backend:

    borgmatic

This will also prune any old backups as per the configured retention policy,
and check backups for consistency problems due to things like file damage.

By default, the backup will proceed silently except in the case of errors. But
if you'd like to to get additional information about the progress of the
backup as it proceeds, use the verbosity option:

    atticmattic --verbosity 1

Or, for even more progress spew:

    atticmattic --verbosity 2

If you'd like to see the available command-line arguments, view the help:

    atticmattic --help


## Running tests

First install tox, which is used for setting up testing environments:

    pip install tox

Then, to actually run tests, run:

    tox


## Troubleshooting

### Broken pipe with remote repository

When running atticmatic on a large remote repository, you may receive errors
like the following, particularly while "attic check" is valiating backups for
consistency:

    Write failed: Broken pipe
    attic: Error: Connection closed by remote host

This error can be caused by an ssh timeout, which you can rectify by adding
the following to the ~/.ssh/config file on the client:

    Host *
        ServerAliveInterval 120

This should make the client keep the connection alive while validating
backups.


## Issues and feedback

Got an issue or an idea for a feature enhancement? Check out the [atticmatic
issue tracker](https://tree.taiga.io/project/witten-atticmatic/issues). In
order to create a new issue or comment on an issue, you'll need to [login
first](https://tree.taiga.io/login).

Other questions or comments? Contact <mailto:witten@torsion.org>.
