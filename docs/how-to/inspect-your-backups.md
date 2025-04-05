---
title: How to inspect your backups
eleventyNavigation:
  key: 🔎 Inspect your backups
  parent: How-to guides
  order: 5
---
## Backup progress

By default, borgmatic runs proceed silently except in the case of warnings or
errors. But if you'd like to to get additional information about the progress of
the backup as it proceeds, use the verbosity option:

```bash
borgmatic --verbosity 1
```

This lists the files that borgmatic is archiving, which are those that are new
or changed since the last backup.

Or, for even more progress and debug spew:

```bash
borgmatic --verbosity 2
```

The full set of verbosity levels are:

 * `-2`: disable output entirely <span class="minilink minilink-addedin">New in borgmatic 1.7.14</span>
 * `-1`: only show errors
 * `0`: default output
 * `1`: some additional output (informational level)
 * `2`: lots of additional output (debug level)

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
verbosity in your borgmatic configuration via the `verbosity` option.


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

(No borgmatic `list` or `info` actions? Upgrade borgmatic!)

<span class="minilink minilink-addedin">New in version 1.9.0</span> There are
also `repo-list` and `repo-info` actions for displaying repository information
with Borg 2.x:

```bash
borgmatic repo-list
borgmatic repo-info
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

## Listing database dumps

If you have enabled borgmatic's [database
hooks](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/), you
can list backed up database dumps via borgmatic. For example:

```bash 
borgmatic list --archive latest --find *borgmatic/*_databases
```

This gives you a listing of all database dump files contained in the latest
archive, complete with file sizes.

<span class="minilink minilink-addedin">New in borgmatic version
1.9.0</span>Database dump files are stored at `/borgmatic` within a backup
archive, regardless of the user who performs the backup. (Note that Borg
doesn't store the leading `/`.)

<span class="minilink minilink-addedin">With Borg version 1.2 and
earlier</span>Database dump files are stored at a path dependent on the [runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.

<span class="minilink minilink-addedin">Prior to borgmatic version
1.9.0</span>Database dump files were instead stored at `~/.borgmatic` within
the backup archive (where `~` was expanded to the home directory of the user
who performed the backup). This applied with all versions of Borg.


## Logging

By default, borgmatic logs to the console. You can enable simultaneous syslog
logging and customize its log level with the `--syslog-verbosity` flag, which
is independent from the console logging `--verbosity` flag described above.
For instance, to enable syslog logging, run:

```bash
borgmatic --syslog-verbosity 1
```

To increase syslog logging further to include debugging information, run:

```bash
borgmatic --syslog-verbosity 2
```

See above for further details about the verbosity levels.

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
syslog verbosity in your borgmatic configuration via the `syslog_verbosity`
option.

Where these logs show up depends on your particular system. If you're using
systemd, try running `journalctl -xe`. Otherwise, try viewing
`/var/log/syslog` or similar.

<span class="minilink minilink-addedin">Prior to version 1.8.3</span>borgmatic
logged to syslog by default whenever run at a non-interactive console.

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
[logrotate](https://wiki.archlinux.org/index.php/Logrotate).

You can use the `--log-file-verbosity` flag to customize the log file's log level:

```bash
borgmatic --log-file /path/to/file.log --log-file-verbosity 2
```

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the log
file verbosity in your borgmatic configuration via the `log_file_verbosity`
option.

<span class="minilink minilink-addedin">New in version 1.7.11</span> Use the
`--log-file-format` flag to override the default log message format. This
format string can contain a series of named placeholders wrapped in curly
brackets. For instance, the default log format is: `[{asctime}] {levelname}:
{message}`. This means each log message is recorded as the log time (in square
brackets), a logging level name, a colon, and the actual log message.

So if you only want each log message to get logged *without* a timestamp or a
logging level name:

```bash
borgmatic --log-file /path/to/file.log --log-file-format "{message}"
```

Here is a list of available placeholders:

 * `{asctime}`: time the log message was created
 * `{levelname}`: level of the log message (`INFO`, `DEBUG`, etc.)
 * `{lineno}`: line number in the source file where the log message originated
 * `{message}`: actual log message
 * `{pathname}`: path of the source file where the log message originated

See the [Python logging
documentation](https://docs.python.org/3/library/logging.html#logrecord-attributes)
for additional placeholders.

Note that this `--log-file-format` flag only applies to the specified
`--log-file` and not to syslog or other logging.

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
defaults for these flags in your borgmatic configuration via the `log_file` and
`log_file_format` options.
