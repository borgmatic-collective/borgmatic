---
title: How to inspect your backups
---
## Backup progress

By default, borgmatic runs proceed silently except in the case of errors. But
if you'd like to to get additional information about the progress of the
backup as it proceeds, use the verbosity option:

```bash
borgmatic --verbosity 1
```

This lists the files that borgmatic is archiving, which are those that are new
or changed since the last backup.

Or, for even more progress and debug spew:

```bash
borgmatic --verbosity 2
```

## Existing backups

Borgmatic provides convenient flags for Borg's
[list](https://borgbackup.readthedocs.io/en/stable/usage/list.html) and
[info](https://borgbackup.readthedocs.io/en/stable/usage/info.html)
functionality:


```bash
borgmatic --list
borgmatic --info
```

## Logging

By default, borgmatic logs to a local syslog-compatible daemon if one is
present. You can customize the log level used for syslog logging with the
`--syslog-verbosity` flag, and this is independent from the console logging
`--verbosity` flag described above. For instance, to disable syslog logging
except for errors:

```bash
borgmatic --syslog-verbosity 0
```

Or to increase syslog logging to include debug spew:

```bash
borgmatic --syslog-verbosity 2
```

## Scripting borgmatic

To consume the output of borgmatic in other software, you can include an
optional `--json` flag with `--create`, `--list`, or `--info` to get the
output formatted as JSON.

Note that when you specify the `--json` flag, Borg's other non-JSON output is
suppressed so as not to interfere with the captured JSON. Also note that JSON
output only shows up at the console, and not in syslog.


## Related documentation

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups.md)
 * [Develop on borgmatic](https://torsion.org/borgmatic/docs/how-to/develop-on-borgmatic.md)
