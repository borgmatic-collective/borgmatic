---
title: 🪵 Logging
eleventyNavigation:
  key: 🪵 Logging
  parent: 💻 Command-line
---
By default, borgmatic runs proceed silently except in the case of warnings or
errors. But if you'd like to to get additional information about the progress of
the backup as it proceeds, use the verbosity option:

```bash
borgmatic --verbosity 1
```

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

Additionally, for the `create` action in particular, you can include the
`--list` flag to list the files that borgmatic is archiving—those files
that are new or changed since the last backup.


### JSON logging

<span class="minilink minilink-addedin">New in version 2.1.0</span>With the
`--log-json` flag, borgmatic logs both its own logs and Borg's output as JSON.
The `--log-json` flag applies to console output and any log file (see below).


## Logging to syslog

By default, borgmatic only logs its output to the console. You can enable
simultaneous syslog logging and customize its log level with the
`--syslog-verbosity` flag, which is independent from the console logging
`--verbosity` flag described above.  For instance, to enable syslog logging,
run:

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


### Systemd journal

<span class="minilink minilink-addedin">New in version 2.1.0</span>If the syslog
verbosity is set and systemd's journal is present, then borgmatic sends
structured logs to the journal instead of plain text. This allows you to query
logs by particular fields. For instance:

```bash
journalctl --catalog --pager-end SYSLOG_IDENTIFIER=borgmatic
```

Or to view just borgmatic warning and error logs:

```bash
journalctl --catalog --pager-end SYSLOG_IDENTIFIER=borgmatic --priority warning..alert
```

The fields borgmatic sends are:

 * `MESSAGE`: the log message
 * `PRIORITY`: the [numeric priority level](https://wiki.archlinux.org/title/Systemd/Journal#Priority_level) for the log entry
 * `SYSLOG_IDENTIFIER`: `borgmatic`
 * `SYSLOG_PID`: borgmatic's process ID

You can also output these structured logs as JSON:

```bash
journalctl --output=json SYSLOG_IDENTIFIER=borgmatic
```

Note that systemd's journal adds its own fields to the JSON on top of the fields
that borgmatic logs.


### Rate limiting

If you are using rsyslog or systemd's journal, be aware that by default they
both throttle the rate at which logging occurs. So you may need to change
either [the global rate
limit](https://www.rootusers.com/how-to-change-log-rate-limiting-in-linux/) or
[the per-service rate
limit](https://www.freedesktop.org/software/systemd/man/journald.conf.html#RateLimitIntervalSec=)
if you're finding that borgmatic logs are missing.

Note that the [sample borgmatic systemd service
file](https://torsion.org/borgmatic/how-to/set-up-backups/#systemd)
already has this rate limit disabled for systemd's journal.


## Logging to file

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
