title: Atticmatic
date:
save_as: atticmatic/index.html

## Overview

atticmatic is a simple Python wrapper script for the [Attic backup
software](https://attic-backup.org/) that initiates a backup and prunes any
old backups according to a retention policy. The script supports specifying
your settings in a declarative configuration file rather than having to put
them all on the command-line, and handles common errors.

Here's an example config file:

    [location]
    # Space-separated list of source directories to backup.
    source_directories: /home /etc

    # Path to local or remote Attic repository.
    repository: user@backupserver:sourcehostname.attic

    [retention]
    # Retention policy for how many backups to keep in each category.
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6

Additionally, exclude patterns can be specified in a separate excludes config
file, one pattern per line.

atticmatic is hosted at <https://torsion.org/atticmatic> with [source code
available](https://torsion.org/hg/atticmatic). It's also mirrored on
[GitHub](https://github.com/witten/atticmatic) and
[BitBucket](https://bitbucket.org/dhelfman/atticmatic) for convenience.


## Setup

To get up and running with Attic, follow the [Attic Quick
Start](https://attic-backup.org/quickstart.html) guide to create an Attic
repository on a local or remote host.

If the repository is on a remote host, make sure that your local root user has
key-based ssh access to the desired user account on the remote host.

To install atticmatic, run the following command to download and install it:

    sudo pip install hg+https://torsion.org/hg/atticmatic

Then copy the following configuration files:

    sudo cp sample/atticmatic.cron /etc/cron.d/atticmatic
    sudo mkdir /etc/atticmatic/
    sudo cp sample/config sample/excludes /etc/atticmatic/

Lastly, modify those files with your desired configuration.


## Usage

You can run atticmatic and start a backup simply by invoking it without
arguments:

    atticmatic

This will also prune any old backups as per the configured retention policy.
By default, the backup will proceed silently except in the case of errors. But
if you'd like to to get additional information about the progress of the
backup as it proceeds, use the verbose option instead:

    atticmattic --verbose

If you'd like to see the available command-line arguments, view the help:

    atticmattic --help


## Running tests

To install test-specific dependencies, first run:

    sudo python setup.py test

To actually run tests, run:

    nosetests --detailed-errors


## Feedback

Questions? Comments? Got a patch? Contact <mailto:witten@torsion.org>.
