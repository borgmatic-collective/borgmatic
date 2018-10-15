---
title: borgmatic
permalink: borgmatic/index.html
---
## Overview

<img src="https://projects.torsion.org/witten/borgmatic/raw/branch/master/static/borgmatic.png" width="150px" style="float: right; padding-left: 1em;">

borgmatic is a simple Python wrapper script for the
[Borg](https://www.borgbackup.org/) backup software that initiates a backup,
prunes any old backups according to a retention policy, and validates backups
for consistency. The script supports specifying your settings in a declarative
configuration file rather than having to put them all on the command-line, and
handles common errors.

Here's an example config file:

```yaml
location:
    # List of source directories to backup. Globs are expanded.
    source_directories:
        - /home
        - /etc
        - /var/log/syslog*

    # Paths to local or remote repositories.
    repositories:
        - user@backupserver:sourcehostname.borg

    # Any paths matching these patterns are excluded from backups.
    exclude_patterns:
        - /home/*/.cache

retention:
    # Retention policy for how many backups to keep in each category.
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6

consistency:
    # List of consistency checks to run: "repository", "archives", or both.
    checks:
        - repository
        - archives
```

borgmatic is hosted at <https://torsion.org/borgmatic> with [source code
available](https://projects.torsion.org/witten/borgmatic). It's also mirrored
on [GitHub](https://github.com/witten/borgmatic) for convenience.

Want to see borgmatic in action? Check out the <a
href="https://asciinema.org/a/203761" target="_blank">screencast</a>.

<script src="https://asciinema.org/a/203761.js" id="asciicast-203761" async></script>


## Installation

To get up and running, first [install
Borg](https://borgbackup.readthedocs.io/en/latest/installation.html), at
least version 1.1. Then, follow the [Borg Quick
Start](https://borgbackup.readthedocs.org/en/latest/quickstart.html) to create
a repository on a local or remote host.

Note that if you plan to run borgmatic on a schedule with cron, and you
encrypt your Borg repository with a passphrase instead of a key file, you'll
either need to set the borgmatic `encryption_passphrase` configuration
variable or set the `BORG_PASSPHRASE` environment variable. See the
[repository encryption
section](https://borgbackup.readthedocs.io/en/latest/quickstart.html#repository-encryption)
of the Quick Start for more info.

Alternatively, the passphrase can be specified programatically by setting
either the borgmatic `encryption_passcommand` configuration variable or the
`BORG_PASSCOMMAND` environment variable. See the [Borg Security
FAQ](http://borgbackup.readthedocs.io/en/stable/faq.html#how-can-i-specify-the-encryption-passphrase-programmatically)
for more info.

If the repository is on a remote host, make sure that your local root user has
key-based ssh access to the desired user account on the remote host.

To install borgmatic, run the following command to download and install it:

```bash
sudo pip3 install --upgrade borgmatic
```

Note that your pip binary may have a different name than "pip3". Make sure
you're using Python 3, as borgmatic does not support Python 2.

### Other ways to install

 * [A borgmatic Docker image](https://hub.docker.com/r/b3vis/borgmatic/) based
   on Alpine Linux.
 * [Another borgmatic Docker image](https://hub.docker.com/r/coaxial/borgmatic/) based
   on Alpine Linux, updated automatically whenever the Alpine image updates.
 * [A borgmatic package for
   Fedora](https://bodhi.fedoraproject.org/updates/?search=borgmatic).
 * [A borgmatic package for Arch
   Linux](https://aur.archlinux.org/packages/borgmatic/).
 * [A borgmatic package for OpenBSD](http://ports.su/sysutils/borgmatic).
<br><br>

## Configuration

After you install borgmatic, generate a sample configuration file:

```bash
sudo generate-borgmatic-config
```

If that command is not found, then it may be installed in a location that's
not in your system `PATH`. Try looking in `/usr/local/bin/`.

This generates a sample configuration file at /etc/borgmatic/config.yaml (by
default). You should edit the file to suit your needs, as the values are just
representative. All fields are optional except where indicated, so feel free
to ignore anything you don't need.

You can also have a look at the [full configuration
schema](https://projects.torsion.org/witten/borgmatic/src/master/borgmatic/config/schema.yaml)
for the authoritative set of all configuration options. This is handy if
borgmatic has added new options since you originally created your
configuration file.


### Multiple configuration files

A more advanced usage is to create multiple separate configuration files and
place each one in an /etc/borgmatic.d directory. For instance:

```bash
sudo mkdir /etc/borgmatic.d
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app1.yaml
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app2.yaml
```

With this approach, you can have entirely different backup policies for
different applications on your system. For instance, you may want one backup
configuration for your database data directory, and a different configuration
for your user home directories.

When you set up multiple configuration files like this, borgmatic will run
each one in turn from a single borgmatic invocation. This includes, by
default, the traditional /etc/borgmatic/config.yaml as well.

And if you need even more customizability, you can specify alternate
configuration paths on the command-line with borgmatic's `--config` option.
See `borgmatic --help` for more information.


### Hooks

If you find yourself performing prepraration tasks before your backup runs, or
cleanup work afterwards, borgmatic hooks may be of interest. They're simply
shell commands that borgmatic executes for you at various points, and they're
configured in the `hooks` section of your configuration file.

For instance, you can specify `before_backup` hooks to dump a database to file
before backing it up, and specify `after_backup` hooks to delete the temporary
file afterwards.

borgmatic hooks run once per configuration file. `before_backup` hooks run
prior to backups of all repositories. `after_backup` hooks run afterwards, but
not if an error occurs in a previous hook or in the backups themselves. And
borgmatic runs `on_error` hooks if an error occurs.

An important security note about hooks: borgmatic executes all hook commands
with the user permissions of borgmatic itself. So to prevent potential shell
injection or privilege escalation, do not forget to set secure permissions
(`chmod 0700`) on borgmatic configuration files and scripts invoked by hooks.

See the sample generated configuration file mentioned above for specifics
about hook configuration syntax.


## Upgrading

In general, all you should need to do to upgrade borgmatic is run the
following:

```bash
sudo pip3 install --upgrade borgmatic
```

However, see below about special cases.


### Upgrading from borgmatic 1.0.x

borgmatic changed its configuration file format in version 1.1.0 from
INI-style to YAML. This better supports validation, and has a more natural way
to express lists of values. To upgrade your existing configuration, first
upgrade to the new version of borgmatic.

As of version 1.1.0, borgmatic no longer supports Python 2. If you were
already running borgmatic with Python 3, then you can simply upgrade borgmatic
in-place:

```bash
sudo pip3 install --upgrade borgmatic
```

But if you were running borgmatic with Python 2, uninstall and reinstall instead:

```bash
sudo pip uninstall borgmatic
sudo pip3 install borgmatic
```

The pip binary names for different versions of Python can differ, so the above
commands may need some tweaking to work on your machine.


Once borgmatic is upgraded, run:

```bash
sudo upgrade-borgmatic-config
```

That will generate a new YAML configuration file at /etc/borgmatic/config.yaml
(by default) using the values from both your existing configuration and
excludes files. The new version of borgmatic will consume the YAML
configuration file instead of the old one.


### Upgrading from atticmatic

You can ignore this section if you're not an atticmatic user (the former name
of borgmatic).

borgmatic only supports Borg now and no longer supports Attic. So if you're
an Attic user, consider switching to Borg. See the [Borg upgrade
command](https://borgbackup.readthedocs.io/en/stable/usage.html#borg-upgrade)
for more information. Then, follow the instructions above about setting up
your borgmatic configuration files.

If you were already using Borg with atticmatic, then you can easily upgrade
from atticmatic to borgmatic. Simply run the following commands:

```bash
sudo pip3 uninstall atticmatic
sudo pip3 install borgmatic
```

That's it! borgmatic will continue using your /etc/borgmatic configuration
files.


## Usage

You can run borgmatic and start a backup simply by invoking it without
arguments:

```bash
borgmatic
```

This will also prune any old backups as per the configured retention policy,
and check backups for consistency problems due to things like file damage.

If you'd like to see the available command-line arguments, view the help:

```bash
borgmatic --help
```

Note that borgmatic prunes archives *before* creating an archive, so as to
free up space for archiving. This means that when a borgmatic run finishes,
there may still be prune-able archives. Not to worry, as they will get cleaned
up at the start of the next run.

### Verbosity

By default, the backup will proceed silently except in the case of errors. But
if you'd like to to get additional information about the progress of the
backup as it proceeds, use the verbosity option:

```bash
borgmatic --verbosity 1
```

Or, for even more progress spew:

```bash
borgmatic --verbosity 2
```

### À la carte

If you want to run borgmatic with only pruning, creating, or checking enabled,
the following optional flags are available:

```bash
borgmatic --prune
borgmatic --create
borgmatic --check
```

You can run with only one of these flags provided, or you can mix and match
any number of them. This supports use cases like running consistency checks
from a different cron job with a different frequency, or running pruning with
a different verbosity level.

Additionally, borgmatic provides convenient flags for Borg's
[list](https://borgbackup.readthedocs.io/en/stable/usage/list.html) and
[info](https://borgbackup.readthedocs.io/en/stable/usage/info.html)
functionality:


```bash
borgmatic --list
borgmatic --info
```

You can include an optional `--json` flag with `--create`, `--list`, or
`--info` to get the output formatted as JSON.


## Autopilot

If you want to run borgmatic automatically, say once a day, the you can
configure a job runner to invoke it periodically.

### cron

If you're using cron, download the [sample cron
file](https://projects.torsion.org/witten/borgmatic/src/master/sample/cron/borgmatic).
Then, from the directory where you downloaded it:

```bash
sudo mv borgmatic /etc/cron.d/borgmatic
sudo chmod +x /etc/cron.d/borgmatic
```

You can modify the cron file if you'd like to run borgmatic more or less frequently.

### systemd

If you're using systemd instead of cron to run jobs, download the [sample
systemd service
file](https://projects.torsion.org/witten/borgmatic/src/master/sample/systemd/borgmatic.service)
and the [sample systemd timer
file](https://projects.torsion.org/witten/borgmatic/src/master/sample/systemd/borgmatic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv borgmatic.service borgmatic.timer /etc/systemd/system/
sudo systemctl enable borgmatic.timer
sudo systemctl start borgmatic.timer
```

Feel free to modify the timer file based on how frequently you'd like
borgmatic to run.


## Support and contributing

### Issues

You've got issues? Or an idea for a feature enhancement? We've got an [issue
tracker](https://projects.torsion.org/witten/borgmatic/issues). In order to
create a new issue or comment on an issue, you'll need to [login
first](https://projects.torsion.org/user/login). Note that you can login with
an existing GitHub account if you prefer.

Other questions or comments? Contact <mailto:witten@torsion.org>.


### Contributing

If you'd like to contribute to borgmatic development, please feel free to
submit a [Pull Request](https://projects.torsion.org/witten/borgmatic/pulls)
or open an [issue](https://projects.torsion.org/witten/borgmatic/issues) first
to discuss your idea. We also accept Pull Requests on GitHub, if that's more
your thing. In general, contributions are very welcome. We don't bite! 


### Code style

Start with [PEP 8](https://www.python.org/dev/peps/pep-0008/). But then, apply
the following deviations from it:

 * For strings, prefer single quotes over double quotes.
 * Limit all lines to a maximum of 100 characters.
 * Use trailing commas within multiline values or argument lists.
 * For multiline constructs, put opening and closing delimeters on lines
   separate from their contents.
 * Within multiline constructs, use standard four-space indentation. Don't align
   indentation with an opening delimeter.

borgmatic code uses the [Black](https://black.readthedocs.io/en/stable/) code
formatter and [Flake8](http://flake8.pycqa.org/en/latest/) code checker, so
certain code style requirements will be enforced when running automated tests.
See the Black and Flake8 documentation for more information.


### Development

To get set up to hack on borgmatic, first clone master via HTTPS or SSH:

```bash
git clone https://projects.torsion.org/witten/borgmatic.git
```

Or:

```bash
git clone ssh://git@projects.torsion.org:3022/witten/borgmatic.git
```

Then, install borgmatic
"[editable](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs)"
so that you can easily run borgmatic commands while you're hacking on them to
make sure your changes work.

```bash
cd borgmatic/
pip3 install --editable --user .
```

Note that this will typically install the borgmatic commands into
`~/.local/bin`, which may or may not be on your PATH. There are other ways to
install borgmatic editable as well, for instance into the system Python
install (so without `--user`, as root), or even into a
[virtualenv](https://virtualenv.pypa.io/en/stable/). How or where you install
borgmatic is up to you, but generally an editable install makes development
and testing easier.


### Running tests

Assuming you've cloned the borgmatic source code as described above, and
you're in the `borgmatic/` working copy, install tox, which is used for
setting up testing environments:

```bash
sudo pip3 install tox
```

Finally, to actually run tests, run:

```bash
cd borgmatic
tox
```

If when running tests, you get an error from the
[Black](https://black.readthedocs.io/en/stable/) code formatter about files
that would be reformatted, you can ask Black to format them for you via the
following:

```bash
tox -e black
```

### End-to-end tests

borgmatic additionally includes some end-to-end tests that integration test
with Borg for a few representative scenarios. These tests don't run by default
because they're relatively slow and depend on Borg. If you would like to run
them:

```bash
tox -e end-to-end
```

## Troubleshooting

### Broken pipe with remote repository

When running borgmatic on a large remote repository, you may receive errors
like the following, particularly while "borg check" is validating backups for
consistency:

```text
    Write failed: Broken pipe
    borg: Error: Connection closed by remote host
```

This error can be caused by an ssh timeout, which you can rectify by adding
the following to the `~/.ssh/config` file on the client:

```text
    Host *
        ServerAliveInterval 120
```

This should make the client keep the connection alive while validating
backups.


### libyaml compilation errors

borgmatic depends on a Python YAML library (ruamel.yaml) that will optionally
use a C YAML library (libyaml) if present. But if it's not installed, then
when installing or upgrading borgmatic, you may see errors about compiling the
YAML library. If so, not to worry. borgmatic should install and function
correctly even without the C YAML library. And borgmatic won't be any faster
with the C library present, so you don't need to go out of your way to install
it.
