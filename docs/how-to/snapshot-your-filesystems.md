---
title: How to snapshot your filesystems
eleventyNavigation:
  key: 📸 Snapshot your filesystems
  parent: How-to guides
  order: 9
---
## Filesystem hooks

Many filesystems support taking snapshots—point-in-time, read-only "copies" of
your data, ideal for backing up files that may change during the backup. These
snapshots initially don't use any additional storage space and can be made
almost instantly.

To help automate backup of these filesystems, borgmatic can use them to take
snapshots.


### ZFS

<span class="minilink minilink-addedin">New in version 1.9.3</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports
taking snapshots with the [ZFS filesystem](https://openzfs.org/) and sending
those snapshots to Borg for backup.

To use this feature, first you need one or more mounted ZFS datasets. Then,
enable ZFS within borgmatic by adding the following line to your configuration
file:

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

If you're using systemd to run borgmatic, you will likely need to modify the [sample systemd service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
to work with ZFS. See the comments in that file for details.

As long as the ZFS hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.


#### Dataset discovery

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
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory),
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
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.


#### Extract a dataset

Filesystem snapshots are stored in a Borg archive as normal files, so
you can use the standard
[extract action](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) to
extract them.


#### ZFS performance

<span class="minilink minilink-addedin">With Borg version 1.x</span> Because of
the way that ZFS snapshot paths can change from one borgmatic invocation to the
next, the [Borg file
cache](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#cache)
may not get cache hits on snapshotted files. This makes backing up ZFS snapshots
a little slower than non-snapshotted files that have consistent paths. You can
mitigate this by setting a fixed [runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory)
(that's not located in `/tmp`). This allows borgmatic to use a consistent
snapshot path from one run to the next, thereby resulting in Borg files cache
hits.

<span class="minilink minilink-addedin">With Borg version 2.x</span> Snapshotted
files should get cache hits regardless of whether their paths change, because
Borg 2.x is smarter about how it looks up file paths in its cache—it constructs
the cache key with the path *as it's seen in the archive* (which is consistent
across runs) rather than the full absolute source path (which can change).


### Btrfs

<span class="minilink minilink-addedin">New in version 1.9.4</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports taking
snapshots with the [Btrfs filesystem](https://btrfs.readthedocs.io/) and sending
those snapshots to Borg for backup.

To use this feature, first you need one or more Btrfs subvolumes. Then, enable
Btrfs within borgmatic by adding the following line to your configuration file:

```yaml
btrfs:
```

No other options are necessary to enable Btrfs support, but if desired you can
override the `btrfs` command used by the Btrfs hook. For instance:

```yaml
btrfs:
    btrfs_command: /usr/local/bin/btrfs
```

If you're using systemd to run borgmatic, you may need to modify the [sample systemd service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
to work with Btrfs. See the comments in that file for details.

As long as the Btrfs hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.


#### Subvolume discovery

For any read-write subvolume you'd like backed up, add its subvolume path to
borgmatic's `source_directories` option. borgmatic does not currently support
snapshotting read-only subvolumes.

<span class="minilink minilink-addedin">New in version 2.0.7</span> The path can
be either the path of the subvolume itself or the mount point where the
subvolume is mounted. Prior to version 2.0.7, the subvolume path could not be
used if the subvolume was mounted elsewhere; only the mount point could be used.

<span class="minilink minilink-addedin">New in version 1.9.6</span> Instead of
using `source_directories`, you can include the subvolume path as a root pattern
with borgmatic's `patterns` or `patterns_from` options.

During a backup, borgmatic snapshots these subvolumes and includes the
snapshotted files in the paths sent to Borg. borgmatic is also responsible for
cleaning up (deleting) these snapshots after a backup completes.

borgmatic is smart enough to look at the parent (and grandparent, etc.)
directories of each of your `source_directories` to discover any subvolumes. For
instance, let's say you add `/var/log` and `/var/lib` to your source
directories, but `/var` is a subvolume path. borgmatic will discover that and
snapshot `/var` accordingly. This also works even with nested subvolumes;
borgmatic selects the subvolume that's the "closest" parent to your source
directories.

If a subvolume has a separate filesystem mounted somewhere within it, that
filesystem won't get included in the snapshot. For instance, if `/` is a Btrfs
subvolume but `/boot` is a separate filesystem, borgmatic won't include `/boot`
as part of the subvolume snapshot. You can however add `/boot` to
`source_directories` if you'd like it included in your backup.

<span class="minilink minilink-addedin">New in version 1.9.6</span> When using
[patterns](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns),
the initial portion of a pattern's path that you intend borgmatic to match
against a subvolume path can't have globs or other non-literal characters in
it—or it won't actually match. For instance, a subvolume path of `/var` would
match a pattern of `+ fm:/var/*/data`, but borgmatic isn't currently smart
enough to match `/var` to a pattern like `+ fm:/v*/lib/data`.

Additionally, borgmatic rewrites the snapshot file paths so that they appear at
their original subvolume locations in a Borg archive. For instance, if your
subvolume path is `/var/subvolume`, then the snapshotted files will appear in an
archive at `/var/subvolume` as well—even if borgmatic has to mount the snapshot
somewhere in `/var/subvolume/.borgmatic-snapshot-1234/` to perform the backup.

<span class="minilink minilink-addedin">With Borg version 1.2 and
earlier</span>Snapshotted files are instead stored at a path dependent on the
temporary snapshot directory in use at the time the archive was created, as Borg
1.2 and earlier do not support path rewriting.


#### Extract a subvolume

Subvolume snapshots are stored in a Borg archive as normal files, so you can use
the standard [extract
action](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) to extract
them.


#### Btrfs performance

<span class="minilink minilink-addedin">With Borg version 1.x</span> Because of
the way that Btrfs snapshot paths change from one borgmatic invocation to the
next, the [Borg file
cache](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#cache)
will never get cache hits on snapshotted files. This makes backing up Btrfs
snapshots a little slower than non-snapshotted files that have consistent paths.

<span class="minilink minilink-addedin">With Borg version 2.x</span> Even
snapshotted files should get cache hits, because Borg 2.x is smarter about how
it looks up file paths in its cache—it constructs the cache key with the path
*as it's seen in the archive* (which is consistent across runs) rather than the
full absolute source path (which changes).


### LVM

<span class="minilink minilink-addedin">New in version 1.9.4</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports
taking snapshots with [LVM](https://sourceware.org/lvm2/) (Linux Logical
Volume Manager) and sending those snapshots to Borg for backup. LVM isn't
itself a filesystem, but it can take snapshots at the layer right below your
filesystem.

Note that, due to Borg being a file-level backup, this feature is really only
suitable for filesystems, not whole disk or raw images containing multiple
filesystems (for example, if you're using a LVM volume to run a Windows
KVM that contains an MBR, partitions, etc.).

In those cases, you can omit the `lvm:` option and use Borg's own support for
[image backup](https://borgbackup.readthedocs.io/en/stable/deployment/image-backup.html).

To use the LVM snapshot feature, first you need one or more mounted LVM logical
volumes. Then, enable LVM within borgmatic by adding the following line to your
configuration file:

```yaml
lvm:
```

No other options are necessary to enable LVM support, but if desired you can
override some of the options used by the LVM hook. For instance:

```yaml
lvm:
    snapshot_size: 5GB  # See below for details.
    lvcreate_command: /usr/local/bin/lvcreate
    lvremove_command: /usr/local/bin/lvremove
    lvs_command: /usr/local/bin/lvs
    lsbrk_command: /usr/local/bin/lsbrk
    mount_command: /usr/local/bin/mount
    umount_command: /usr/local/bin/umount
```

If you're using systemd to run borgmatic, you may need to modify the [sample systemd service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
to work with LVM. See the comments in that file for details.

As long as the LVM hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.


#### Snapshot size

The `snapshot_size` option is the size to allocate for each snapshot taken,
including the units to use for that size. While borgmatic's snapshots
themselves are read-only and don't change during backups, the logical volume
being snapshotted *can* change—therefore requiring additional snapshot storage
since LVM snapshots are copy-on-write. And if the configured snapshot size is
too small (and LVM isn't configured to grow snapshots automatically), then the
snapshots will fail to allocate enough space, resulting in a broken backup.

If not specified, the `snapshot_size` option defaults to `10%ORIGIN`, which
means 10% of the size of the logical volume being snapshotted. See the
[`lvcreate --size` and `--extents`
documentation](https://www.man7.org/linux/man-pages/man8/lvcreate.8.html) for
more information about possible values here. (Under the hood, borgmatic uses
`lvcreate --extents` if the `snapshot_size` is a percentage value, and `lvcreate
--size` otherwise.)


#### Logical volume discovery

For any logical volume you'd like backed up, add its mount point to
borgmatic's `source_directories` option.

<span class="minilink minilink-addedin">New in version 1.9.6</span> Or include
the mount point as a root pattern with borgmatic's `patterns` or `patterns_from`
options.

During a backup, borgmatic automatically snapshots these discovered logical volumes
(non-recursively), temporarily mounts the snapshots within its [runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory), and
includes the snapshotted files in the paths sent to Borg. borgmatic is also responsible for cleaning
up (deleting) these snapshots after a backup completes.

borgmatic is smart enough to look at the parent (and grandparent, etc.)
directories of each of your `source_directories` to discover any logical
volumes. For instance, let's say you add `/var/log` and `/var/lib` to your
source directories, but `/var` is a logical volume. borgmatic will discover
that and snapshot `/var` accordingly.

If a logical volume has a separate filesystem mounted somewhere within it, that
filesystem won't get included in the snapshot. For instance, if `/` is an LVM
logical volume but `/boot` is a separate filesystem, borgmatic won't include
`/boot` as part of the logical volume snapshot. You can however add `/boot` to
`source_directories` if you'd like it included in your backup.

<span class="minilink minilink-addedin">New in version 1.9.6</span> When using
[patterns](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns),
the initial portion of a pattern's path that you intend borgmatic to match
against a logical volume can't have globs or other non-literal characters in
it—or it won't actually match. For instance, a logical volume of `/var` would
match a pattern of `+ fm:/var/*/data`, but borgmatic isn't currently smart
enough to match `/var` to a pattern like `+ fm:/v*/lib/data`.

Additionally, borgmatic rewrites the snapshot file paths so that they appear
at their original logical volume locations in a Borg archive. For instance, if
your logical volume is mounted at `/var/lvolume`, then the snapshotted files
will appear in an archive at `/var/lvolume` as well—even if borgmatic has to
mount the snapshot somewhere in `/run/user/1000/borgmatic/lvm_snapshots/` to
perform the backup.

<span class="minilink minilink-addedin">With Borg version 1.2 and
earlier</span>Snapshotted files are instead stored at a path dependent on the
[runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.


#### Extract a logical volume

Logical volume snapshots are stored in a Borg archive as normal files, so
you can use the standard
[extract action](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) to
extract them.


#### LVM performance

<span class="minilink minilink-addedin">With Borg version 1.x</span> Because of
the way that LVM snapshot paths can change from one borgmatic invocation to the
next, the [Borg file
cache](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#cache)
may not get cache hits on snapshotted files. This makes backing up LVM snapshots
a little slower than non-snapshotted files that have consistent paths. You can
mitigate this by setting a fixed [runtime
directory](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/#runtime-directory)
(that's not located in `/tmp`). This allows borgmatic to use a consistent
snapshot path from one run to the next, thereby resulting in Borg files cache
hits.

<span class="minilink minilink-addedin">With Borg version 2.x</span> Snapshotted
files should get cache hits regardless of whether their paths change, because
Borg 2.x is smarter about how it looks up file paths in its cache—it constructs
the cache key with the path *as it's seen in the archive* (which is consistent
across runs) rather than the full absolute source path (which can change).
