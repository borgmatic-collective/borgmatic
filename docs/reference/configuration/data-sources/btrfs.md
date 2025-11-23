---
title: Btrfs
eleventyNavigation:
  key: Btrfs
  parent: 🗄️ Data sources
---
<span class="minilink minilink-addedin">New in version 1.9.4</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports taking
snapshots with the [Btrfs filesystem](https://btrfs.readthedocs.io/) and sending
those snapshots to Borg for backup.

The minimum configuration to enable Btrfs support is:

```yaml
btrfs:
```

## Subvolume discovery

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


## Performance

<span class="minilink minilink-addedin">New in borgmatic version 2.0.12, with Borg version
1.x</span> borgmatic uses consistent snapshot paths between invocations, so
backups will be cached correctly. No configuration is necessary.

<span class="minilink minilink-addedin">Prior to borgmatic version 2.0.12, with
Borg version 1.x</span> Because of the way that Btrfs snapshot paths change from
one borgmatic invocation to the next, the [Borg file
cache](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#cache)
will never get cache hits on snapshotted files. This makes backing up Btrfs
snapshots a little slower than non-snapshotted files that have consistent paths.
**It is also not possible to mitigate cache misses**, as the Btrfs hook uses
snapshot paths which change between borgmatic invocations, and the snapshots
are located outside the [runtime
directory](https://torsion.org/borgmatic/reference/configuration/runtime-directory/),
contrary to
[ZFS](https://torsion.org/borgmatic/reference/configuration/data-sources/zfs/#performance)
and
[LVM](https://torsion.org/borgmatic/reference/configuration/data-sources/lvm/#performance).

<span class="minilink minilink-addedin">With Borg version 2.x</span> Even
snapshotted files should get cache hits, because Borg 2.x is smarter about how
it looks up file paths in its cache—it constructs the cache key with the path
*as it's seen in the archive* (which is consistent across runs) rather than the
full absolute source path (which changes).


## Full configuration

```yaml
{% include borgmatic/btrfs.yaml %}
```
