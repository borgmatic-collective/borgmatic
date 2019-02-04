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

## Scripting borgmatic

To consume the output of borgmatic in other software, you can include an
optional `--json` flag with `--create`, `--list`, or `--info` to get the
output formatted as JSON.


## Related documentation

 * [Set up backups with borgmatic](../../docs/how-to/set-up-backups.md)
