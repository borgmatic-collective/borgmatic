---
title: LVM
eleventyNavigation:
  key: LVM
  parent: 🗄️ Data sources
---
<span class="minilink minilink-addedin">New in version 1.9.4</span> borgmatic
supports taking snapshots with [LVM](https://sourceware.org/lvm2/) (Linux
Logical Volume Manager) and sending those snapshots to Borg for backup. LVM
isn't itself a filesystem, but it can take snapshots at the layer right below
your filesystem.

The minimum configuration to enable LVM support is:

```yaml
lvm:
```

## Snapshot size

The `snapshot_size` option is the size to allocate for each snapshot taken,
including the units to use for that size:

```yaml
lvm:
    snapshot_size: 5GB
```

While borgmatic's snapshots themselves are read-only and don't change during
backups, the logical volume being snapshotted *can* change—therefore requiring
additional snapshot storage since LVM snapshots are copy-on-write. And if the
configured snapshot size is too small (and LVM isn't configured to grow
snapshots automatically), then the snapshots will fail to allocate enough space,
resulting in a broken backup.

If not specified, the `snapshot_size` option defaults to `10%ORIGIN`, which
means 10% of the size of the logical volume being snapshotted. See the
[`lvcreate --size` and `--extents`
documentation](https://www.man7.org/linux/man-pages/man8/lvcreate.8.html) for
more information about possible values here. (Under the hood, borgmatic uses
`lvcreate --extents` if the `snapshot_size` is a percentage value, and `lvcreate
--size` otherwise.)


## Logical volume discovery

For any logical volume you'd like backed up, add its mount point to
borgmatic's `source_directories` option.

<span class="minilink minilink-addedin">New in version 1.9.6</span> Or include
the mount point as a root pattern with borgmatic's `patterns` or `patterns_from`
options.

During a backup, borgmatic automatically snapshots these discovered logical volumes
(non-recursively), temporarily mounts the snapshots within its [runtime
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/), and
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
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/)
in use at the time the archive was created, as Borg 1.2 and earlier do not
support path rewriting.


## Performance

<span class="minilink minilink-addedin">With Borg version 1.x</span> Because of
the way that LVM snapshot paths can change from one borgmatic invocation to the
next, the [Borg file
cache](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#cache)
may not get cache hits on snapshotted files. This makes backing up LVM snapshots
a little slower than non-snapshotted files that have consistent paths. You can
mitigate this by setting a fixed [runtime
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/)
(that's not located in `/tmp`). This allows borgmatic to use a consistent
snapshot path from one run to the next, thereby resulting in Borg files cache
hits.

<span class="minilink minilink-addedin">With Borg version 2.x</span> Snapshotted
files should get cache hits regardless of whether their paths change, because
Borg 2.x is smarter about how it looks up file paths in its cache—it constructs
the cache key with the path *as it's seen in the archive* (which is consistent
across runs) rather than the full absolute source path (which can change).


## systemd settings

If you're using [systemd to run
borgmatic](https://torsion.org/borgmatic/how-to/set-up-backups/#systemd), you
may need to disable particular security settings like `ProtectKernelModules`,
`CapabilityBoundingSet`, and/or `PrivateDevices` to allow the LVM feature to
work. See the comments in the sample systemd service file for details.


## Full configuration

```yaml
{% include borgmatic/lvm.yaml %}
```
