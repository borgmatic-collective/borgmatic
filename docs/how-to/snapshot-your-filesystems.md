---
title: How to snapshot your filesystems
eleventyNavigation:
  key: 📸 Snapshot your filesystems
  parent: How-to guides
  order: 9
---
## Filesystem hooks

Many filesystems support taking snapshots—point-in-time, read-only "copies" of
your data, ideal for backing up files that may be changing during the backup.
These snapshots initially don't use any additional storage space and can be made
almost instantly.


### ZFS

<span class="minilink minilink-addedin">New in version 1.9.3</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports
taking and backing up snapshots with the ZFS filesystem. First, you need one
or more mounted ZFS datasets. Then, enable ZFS within borgmatic by adding the
following line to your configuration file:

```yaml
zfs:
```

No other options are necessary to enable ZFS support, but if desired you can
override some of the commands used by the ZFS hook. For instance:

```yaml
zfs:
    zfs_command: /usr/local/bin/zfs
    mount_command: /usr/local/bin/mount
    umount_command: /usr/local/bin/umount
```

As long as the ZFS hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.


#### Dataset discovery

You have a couple of options for borgmatic to find and backup your ZFS datasets:

 * For any dataset you'd like backed up, add its mount point to borgmatic's
   `source_directories`.
 * Or set the borgmatic-specific user property
   `org.torsion.borgmatic:backup=auto` onto your dataset, e.g. by running `zfs
   set org.torsion.borgmatic:backup=auto datasetname`. Then borgmatic can find
   and backup these datasets.

If you have multiple borgmatic configuration files with ZFS enabled, and you'd
like particular datasets to be backed up only for particular configuration
files, use the `source_directories` option.

During a backup, borgmatic automatically snapshots these discovered datasets,
temporary mounts the snapshots within its [runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory),
and includes the snapshotted files in the backup. Additionally, borgmatic
rewrites the paths so that they appear at their original dataset locations in a
Borg archive. For instance, if your dataset is mounted at `/mnt/dataset`, then
the snapshotted files will appear in an archive at `/mnt/dataset` as well.

<span class="minilink minilink-addedin">With Borg version 1.2 and
earlier</span>Snapshotted files are stored at a path dependent on the [runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.


#### Extract a dataset

Given that filesystem snapshots are stored in a Borg archive as normal files,
you can use the standard
[extract action](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) to
extract them.
