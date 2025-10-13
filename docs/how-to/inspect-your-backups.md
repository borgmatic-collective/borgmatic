---
title: How to inspect your backups
eleventyNavigation:
  key: 🔎 Inspect your backups
  parent: How-to guides
  order: 5
---
By default, borgmatic runs proceed silently except in the case of warnings or
errors. But if you'd like to to get additional information about the progress of
the backup as it proceeds, see the [logging
documentation](https://torsion.org/borgmatic/reference/command-line/logging/)
for details.


## Backup summary

If you're less concerned with progress during a backup, and you only want to see
the summary of archive statistics at the end, use the stats option when
performing a backup:

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

<span class="minilink minilink-addedin">New in version 1.9.0</span> There are
also `repo-list` and `repo-info` actions for displaying repository information
with Borg 2.x:

```bash
borgmatic repo-list
borgmatic repo-info
```

See the [borgmatic command-line
reference](https://torsion.org/borgmatic/reference/command-line/) for
more information.


### Searching for a file

<span class="minilink minilink-addedin">New in version 1.6.3</span> Let's say
you've accidentally deleted a file and want to find the backup archive(s)
containing it. `borgmatic list` provides a `--find` flag for exactly this
purpose. For instance, if you're looking for a `foo.txt`:

```bash
borgmatic list --find foo.txt
```

This lists your archives and indicate those with files matching `*foo.txt*`
anywhere in the archive. The `--find` parameter can alternatively be a [Borg
pattern](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-patterns).

To limit the archives searched, use the standard `list` parameters for
filtering archives such as `--last`, `--archive`, `--match-archives`, etc. For
example, to search only the last five archives:

```bash
borgmatic list --find foo.txt --last 5
```

## Listing database dumps

If you've enabled borgmatic's [database
hooks](https://torsion.org/borgmatic/how-to/backup-your-databases/), you
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
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.

<span class="minilink minilink-addedin">Prior to borgmatic version
1.9.0</span>Database dump files were instead stored at `~/.borgmatic` within
the backup archive (where `~` was expanded to the home directory of the user
who performed the backup). This applied with all versions of Borg.


<a id="rate-limiting"></a>
<a id="logging-to-file"></a>


## Logging

By default, borgmatic only logs to the console. But to enable simultaneous
syslog or file logging, see the [logging
documentation](https://torsion.org/borgmatic/reference/command-line/logging/)
for details.
