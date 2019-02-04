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


## How-to guides

 * [Set up backups with borgmatic](docs/how-to/set-up-backups.md) \<-- *Start here!*
 * [Make per-application backups](docs/how-to/make-per-application-backups.md)
 * [Deal with very large backups](docs/how-to/deal-with-very-large-backups.md)
 * [Inspect your backups](docs/how-to/inspect-your-backups.md)
 * [Run preparation steps before backups](docs/how-to/run-preparation-steps-before-backups.md)
 * [Upgrade borgmatic](docs/how-to/upgrade.md)
 * [Develop on borgmatic](docs/how-to/develop-on-borgmatic.md)


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

Also, please check out the [borgmatic development
how-to](docs/how-to/develop-on-borgmatic.md) for info on cloning source code,
running tests, etc.


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
