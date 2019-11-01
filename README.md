---
title: borgmatic
permalink: index.html
---
<a href="https://build.torsion.org/witten/borgmatic" alt="build status">![Build Status](https://build.torsion.org/api/badges/witten/borgmatic/status.svg?ref=refs/heads/master)</a>

## Overview

<img src="https://projects.torsion.org/witten/borgmatic/raw/branch/master/static/borgmatic.png" alt="borgmatic logo" width="150px" style="float: right; padding-left: 1em;">

borgmatic is simple, configuration-driven backup software for servers and
workstations. Backup all of your machines from the command-line or scheduled
jobs. No GUI required. Built atop [Borg Backup](https://www.borgbackup.org/),
borgmatic initiates a backup, prunes any old backups according to a retention
policy, and validates backups for consistency. borgmatic supports specifying
your settings in a declarative configuration file, rather than having to put
them all on the command-line, and handles common errors.

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
    # List of consistency checks to run: "repository", "archives", etc.
    checks:
        - repository
        - archives

hooks:
    # Preparation scripts to run, databases to dump, and monitoring to perform.
    before_backup:
        - prepare-for-backup.sh
    postgresql_databases:
        - name: users
    healthchecks: https://hc-ping.com/be067061-cf96-4412-8eae-62b0c50d6a8c
```

borgmatic is hosted at <https://torsion.org/borgmatic> with [source code
available](https://projects.torsion.org/witten/borgmatic). It's also mirrored
on [GitHub](https://github.com/witten/borgmatic) for convenience.

Want to see borgmatic in action? Check out the <a
href="https://asciinema.org/a/203761" target="_blank">screencast</a>.

<script src="https://asciinema.org/a/203761.js" id="asciicast-203761" async></script>


## How-to guides

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups/) ⬅ *Start here!*
 * [Make per-application backups](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/)
 * [Deal with very large backups](https://torsion.org/borgmatic/docs/how-to/deal-with-very-large-backups/)
 * [Inspect your backups](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/)
 * [Monitor your backups](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/)
 * [Extract a backup](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/)
 * [Backup your databases](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/)
 * [Add preparation and cleanup steps to backups](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/)
 * [Upgrade borgmatic](https://torsion.org/borgmatic/docs/how-to/upgrade/)
 * [Develop on borgmatic](https://torsion.org/borgmatic/docs/how-to/develop-on-borgmatic/)


## Reference guides

 * [borgmatic configuration reference](https://torsion.org/borgmatic/docs/reference/configuration/)
 * [borgmatic command-line reference](https://torsion.org/borgmatic/docs/reference/command-line/)


## Hosting providers

Need somewhere to store your encrypted offsite backups? The following hosting
providers include specific support for Borg/borgmatic. Using these links and
services helps support borgmatic development and hosting. (These are referral
links, but without any tracking scripts or cookies.)

<ul>
 <li class="referral"><a href="https://www.rsync.net/cgi-bin/borg.cgi?campaign=borg&adgroup=borgmatic">rsync.net</a>: Cloud Storage provider with full support for borg and any other SSH/SFTP tool</li>
 <li class="referral"><a href="https://www.borgbase.com/?utm_source=borgmatic">BorgBase</a>: Borg hosting service with support for monitoring, 2FA, and append-only repos</li>
</ul>

## Support and contributing

### Issues

You've got issues? Or an idea for a feature enhancement? We've got an [issue
tracker](https://projects.torsion.org/witten/borgmatic/issues). In order to
create a new issue or comment on an issue, you'll need to [login
first](https://projects.torsion.org/user/login). Note that you can login with
an existing GitHub account if you prefer.

If you'd like to chat with borgmatic developers or users, head on over to the
`#borgmatic` IRC channel on Freenode, either via <a
href="https://webchat.freenode.net/?channels=borgmatic">web chat</a> or a
native <a href="irc://chat.freenode.net:6697">IRC client</a>.

Other questions or comments? Contact <mailto:witten@torsion.org>.


### Contributing

If you'd like to contribute to borgmatic development, please feel free to
submit a [Pull Request](https://projects.torsion.org/witten/borgmatic/pulls)
or open an [issue](https://projects.torsion.org/witten/borgmatic/issues) first
to discuss your idea. We also accept Pull Requests on GitHub, if that's more
your thing. In general, contributions are very welcome. We don't bite! 

Also, please check out the [borgmatic development
how-to](https://torsion.org/borgmatic/docs/how-to/develop-on-borgmatic/) for
info on cloning source code, running tests, etc.
