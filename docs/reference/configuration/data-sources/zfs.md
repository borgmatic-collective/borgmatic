---
title: ZFS
eleventyNavigation:
  key: • ZFS
  parent: 🗄️ Data sources
---
<span class="minilink minilink-addedin">New in version 1.9.3</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports
taking snapshots with the [ZFS filesystem](https://openzfs.org/) and sending
those snapshots to Borg for backup.

The minimum configuration to enable ZFS support is:

```yaml
zfs:
```

## Dataset discovery

You have a couple of options for borgmatic to find and backup your ZFS datasets:

 * For any dataset you'd like backed up, add its mount point to borgmatic's
   `source_directories` option.
 * <span class="minilink minilink-addedin">New in version 1.9.6</span> Or
   include the mount point as a root pattern with borgmatic's `patterns` or
   `patterns_from` options.
 * Or set the borgmatic-specific user property
   `org.torsion.borgmatic:backup=auto` onto your dataset, e.g. by running `zfs
   set org.torsion.borgmatic:backup=auto datasetname`. Then borgmatic can find
   and backup these datasets.

If you have multiple borgmatic configuration files with ZFS enabled, and you'd
like particular datasets to be backed up only for particular configuration
files, use the `source_directories` option instead of the user property.

<span class="minilink minilink-addedin">New in version 1.9.11</span> borgmatic
won't snapshot datasets with the `canmount=off` property, which is often set on
datasets that only serve as a container for other datasets. Use `zfs get
canmount datasetname` to see the `canmount` value for a dataset.

During a backup, borgmatic automatically snapshots these discovered datasets,
temporarily mounts the snapshots within its [runtime
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/),
and includes the snapshotted files in the paths sent to Borg. borgmatic is also
responsible for cleaning up (destroying) these snapshots after a backup
completes.

Additionally, borgmatic rewrites the snapshot file paths so that they appear
at their original dataset locations in a Borg archive. For instance, if your
dataset is mounted at `/var/dataset`, then the snapshotted files will appear
in an archive at `/var/dataset` as well—even if borgmatic has to mount the
snapshot somewhere in `/run/user/1000/borgmatic/zfs_snapshots/` to perform the
backup.

If a dataset has a separate filesystem mounted somewhere within it, that
filesystem won't get included in the snapshot. For instance, if `/` is a ZFS
dataset but `/boot` is a separate filesystem, borgmatic won't include `/boot` as
part of the dataset snapshot. You can however add `/boot` to
`source_directories` if you'd like it included in your backup.

<span class="minilink minilink-addedin">New in version 1.9.4</span> borgmatic
is smart enough to look at the parent (and grandparent, etc.) directories of
each of your `source_directories` to discover any datasets. For instance,
let's say you add `/var/log` and `/var/lib` to your source directories, but
`/var` is a dataset. borgmatic will discover that and snapshot `/var`
accordingly. This also works even with nested datasets; borgmatic selects
the dataset that's the "closest" parent to your source directories.

<span class="minilink minilink-addedin">New in version 1.9.6</span> When using
[patterns](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns),
the initial portion of a pattern's path that you intend borgmatic to match
against a dataset can't have globs or other non-literal characters in it—or it
won't actually match. For instance, a mount point of `/var` would match a
pattern of `+ fm:/var/*/data`, but borgmatic isn't currently smart enough to
match `/var` to a pattern like `+ fm:/v*/lib/data`.

<span class="minilink minilink-addedin">With Borg version 1.2 and
earlier</span>Snapshotted files are instead stored at a path dependent on the
[runtime
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.


## Performance

<span class="minilink minilink-addedin">With Borg version 1.x</span> Because of
the way that ZFS snapshot paths can change from one borgmatic invocation to the
next, the [Borg file
cache](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#cache)
may not get cache hits on snapshotted files. This makes backing up ZFS snapshots
a little slower than non-snapshotted files that have consistent paths. You can
mitigate this by setting a fixed [runtime
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/))
(that's not located in `/tmp`). This allows borgmatic to use a consistent
snapshot path from one run to the next, thereby resulting in Borg files cache
hits.

<span class="minilink minilink-addedin">With Borg version 2.x</span> Snapshotted
files should get cache hits regardless of whether their paths change, because
Borg 2.x is smarter about how it looks up file paths in its cache—it constructs
the cache key with the path *as it's seen in the archive* (which is consistent
across runs) rather than the full absolute source path (which can change).


## Full configuration

```yaml
{% include borgmatic/zfs.yaml %}
```
