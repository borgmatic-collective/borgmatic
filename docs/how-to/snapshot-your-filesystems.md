---
title: 📸 How to snapshot your filesystems
eleventyNavigation:
  key: 📸 Snapshot your filesystems
  parent: How-to guides
  order: 9
---
Many filesystems support taking snapshots—point-in-time, read-only "copies" of
your data, ideal for backing up files that may change during the backup. These
snapshots initially don't use any additional storage space and can be made
almost instantly.

To help automate backup of these filesystems, borgmatic can use them to take
snapshots.


<a id="dataset-discovery"></a>
<a id="zfs-performance"></a>


### ZFS

<span class="minilink minilink-addedin">New in version 1.9.3</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports
taking snapshots with the [ZFS filesystem](https://openzfs.org/) and sending
those snapshots to Borg for backup.

To use this feature, add one or more ZFS dataset paths to your
`source_directories`. Then, enable borgmatic's ZFS snapshotting of those
datasets by adding the following line to your configuration file:

```yaml
zfs:
```

No other options are necessary to enable ZFS support. But if you're using
systemd to run borgmatic, you'll likely need to modify the [sample systemd
service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
to work with ZFS. See the comments in that file for details.

As long as the ZFS hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.

For additional details about ZFS support, see [borgmatic's ZFS
documentation](https://torsion.org/borgmatic/reference/configuration/data-sources/zfs/).


#### Extract a dataset

Filesystem snapshots are stored in a Borg archive as normal files, so
you can use the standard
[extract action](https://torsion.org/borgmatic/how-to/extract-a-backup/) to
extract them.


<a id="subvolume-discovery"></a>
<a id="btrfs-performance"></a>


### Btrfs

<span class="minilink minilink-addedin">New in version 1.9.4</span> <span
class="minilink minilink-addedin">Beta feature</span> borgmatic supports taking
snapshots with the [Btrfs filesystem](https://btrfs.readthedocs.io/) and sending
those snapshots to Borg for backup.

To use this feature, add one or more subvolume paths to your
`source_directories`. Then, enable Btrfs within borgmatic by adding the
following line to your configuration file:

```yaml
btrfs:
```

No other options are necessary to enable Btrfs support. But if you're using
systemd to run borgmatic, you may need to modify the [sample systemd service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
to work with Btrfs. See the comments in that file for details.

As long as the Btrfs hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.

For additional details about Btrfs support, see [borgmatic's Btrfs
documentation](https://torsion.org/borgmatic/reference/configuration/data-sources/btrfs/).


#### Extract a subvolume

Subvolume snapshots are stored in a Borg archive as normal files, so you can use
the standard [extract
action](https://torsion.org/borgmatic/how-to/extract-a-backup/) to extract
them.


<a id="snapshot-size"></a>
<a id="logical-volume-discovery"></a>
<a id="lvm-performance"></a>


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

To use the LVM snapshot feature, add one or more mounted LVM logical volumes to
your `source_directories`. Then, enable LVM within borgmatic by adding the
following line to your configuration file:

```yaml
lvm:
```

No other options are necessary to enable LVM support. But if you're using
systemd to run borgmatic, you may need to modify the [sample systemd service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
to work with LVM. See the comments in that file for details.

As long as the LVM hook is in beta, it may be subject to breaking changes
and/or may not work well for your use cases. But feel free to use it in
production if you're okay with these caveats, and please [provide any
feedback](https://torsion.org/borgmatic/#issues) you have on this feature.

For additional details about LVM support, see [borgmatic's LVM
documentation](https://torsion.org/borgmatic/reference/configuration/data-sources/lvm/).


#### Extract a logical volume

Logical volume snapshots are stored in a Borg archive as normal files, so
you can use the standard
[extract action](https://torsion.org/borgmatic/how-to/extract-a-backup/) to
extract them.
