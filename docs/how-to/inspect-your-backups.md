---
title: How to inspect your backups
eleventyNavigation:
  key: 🔎 Inspect your backups
  parent: How-to guides
  order: 5
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

## Backup summary

If you're less concerned with progress during a backup, and you only want to
see the summary of archive statistics at the end, you can use the stats
option when performing a backup:

```bash
borgmatic --stats
```

## Existing backups

borgmatic provides convenient actions for Borg's
[`list`](https://borgbackup.readthedocs.io/en/stable/usage/list.html) and
[`info`](https://borgbackup.readthedocs.io/en/stable/usage/info.html)
functionality:

```bash
borgmatic list
borgmatic info
```

You can change the output format of `borgmatic list` by specifying your own
with `--format`. Refer to the [borg list --format
documentation](https://borgbackup.readthedocs.io/en/stable/usage/list.html#the-format-specifier-syntax)
for available values.

*(No borgmatic `list` or `info` actions? Upgrade borgmatic!)*

<span class="minilink minilink-addedin">New in borgmatic version 1.7.0</span>
There are also `rlist` and `rinfo` actions for displaying repository
information with Borg 2.x:

```bash
borgmatic rlist
borgmatic rinfo
```

See the [borgmatic command-line
reference](https://torsion.org/borgmatic/docs/reference/command-line/) for
more information.


### Searching for a file

<span class="minilink minilink-addedin">New in version 1.6.3</span> Let's say
you've accidentally deleted a file and want to find the backup archive(s)
containing it. `borgmatic list` provides a `--find` flag for exactly this
purpose. For instance, if you're looking for a `foo.txt`:

```bash
borgmatic list --find foo.txt
```

This will list your archives and indicate those with files matching
`*foo.txt*` anywhere in the archive. The `--find` parameter can alternatively
be a [Borg
pattern](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-patterns).

To limit the archives searched, use the standard `list` parameters for
filtering archives such as `--last`, `--archive`, `--match-archives`, etc. For
example, to search only the last five archives:

```bash
borgmatic list --find foo.txt --last 5
```


## Logging

By default, borgmatic logs to a local syslog-compatible daemon if one is
present and borgmatic is running in a non-interactive console. Where those
logs show up depends on your particular system. If you're using systemd, try
running `journalctl -xe`. Otherwise, try viewing `/var/log/syslog` or
similiar.

You can customize the log level used for syslog logging with the
`--syslog-verbosity` flag, and this is independent from the console logging
`--verbosity` flag described above. For instance, to get additional
information about the progress of the backup as it proceeds:

```bash
borgmatic --syslog-verbosity 1
```

Or to increase syslog logging to include debug spew:

```bash
borgmatic --syslog-verbosity 2
```

### Rate limiting

If you are using rsyslog or systemd's journal, be aware that by default they
both throttle the rate at which logging occurs. So you may need to change
either [the global rate
limit](https://www.rootusers.com/how-to-change-log-rate-limiting-in-linux/) or
[the per-service rate
limit](https://www.freedesktop.org/software/systemd/man/journald.conf.html#RateLimitIntervalSec=)
if you're finding that borgmatic logs are missing.

Note that the [sample borgmatic systemd service
file](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#systemd)
already has this rate limit disabled for systemd's journal.


### Logging to file

If you don't want to use syslog, and you'd rather borgmatic log to a plain
file, use the `--log-file` flag:

```bash
borgmatic --log-file /path/to/file.log
```

Note that if you use the `--log-file` flag, you are responsible for rotating
the log file so it doesn't grow too large, for example with
[logrotate](https://wiki.archlinux.org/index.php/Logrotate). Also, there is a
`--log-file-verbosity` flag to customize the log file's log level.
