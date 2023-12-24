---
title: How to extract a backup
eleventyNavigation:
  key: 📤 Extract a backup
  parent: How-to guides
  order: 7
---
## Extract

When the worst happens—or you want to test your backups—the first step is
to figure out which archive to extract. A good way to do that is to use the
`rlist` action:

```bash
borgmatic rlist
```

(No borgmatic `rlist` action? Try `list` instead or upgrade borgmatic!)

That should yield output looking something like:

```text
host-2023-01-01T04:05:06.070809      Tue, 2023-01-01 04:05:06 [...]
host-2023-01-02T04:06:07.080910      Wed, 2023-01-02 04:06:07 [...]
```

Assuming that you want to extract the archive with the most up-to-date files
and therefore the latest timestamp, run a command like:

```bash
borgmatic extract --archive host-2023-01-02T04:06:07.080910
```

(No borgmatic `extract` action? Upgrade borgmatic!)

Or simplify this to:

```bash
borgmatic extract --archive latest
```

The `--archive` value is the name of the archive to extract. This extracts the
entire contents of the archive to the current directory, so make sure you're
in the right place before running the command—or see below about the
`--destination` flag.

## Repository selection

If you have a single repository in your borgmatic configuration file(s), no
problem: the `extract` action figures out which repository to use.

But if you have multiple repositories configured, then you'll need to specify
the repository to use via the `--repository` flag. This can be done either
with the repository's path or its label as configured in your borgmatic configuration file.

```bash
borgmatic extract --repository repo.borg --archive host-2023-...
```

## Extract particular files

Sometimes, you want to extract a single deleted file, rather than extracting
everything from an archive. To do that, tack on one or more `--path` values.
For instance:

```bash
borgmatic extract --archive latest --path path/1 --path path/2
```

Note that the specified restore paths should not have a leading slash. Like a
whole-archive extract, this also extracts into the current directory by
default. So for example, if you happen to be in the directory `/var` and you
run the `extract` command above, borgmatic will extract `/var/path/1` and
`/var/path/2`.


### Searching for files

If you're not sure which archive contains the files you're looking for, you
can [search across
archives](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/#searching-for-a-file).


## Extract to a particular destination

By default, borgmatic extracts files into the current directory. To instead
extract files to a particular destination directory, use the `--destination`
flag:

```bash
borgmatic extract --archive latest --destination /tmp
```

When using the `--destination` flag, be careful not to overwrite your system's
files with extracted files unless that is your intent.


## Database restoration

The `borgmatic extract` command only extracts files. To restore a database,
please see the [documentation on database backups and
restores](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/).
borgmatic does not perform database restoration as part of `borgmatic extract`
so that you can extract files from your archive without impacting your live
databases.


## Mount a filesystem

If instead of extracting files, you'd like to explore the files from an
archive as a [FUSE](https://en.wikipedia.org/wiki/Filesystem_in_Userspace)
filesystem, you can use the `borgmatic mount` action. Here's an example:

```bash
borgmatic mount --archive latest --mount-point /mnt
```

This mounts the entire archive on the given mount point `/mnt`, so that you
can look in there for your files.

Omit the `--archive` flag to mount all archives (lazy-loaded):

```bash
borgmatic mount --mount-point /mnt
```

Or use the "latest" value for the archive to mount the latest archive:

```bash
borgmatic mount --archive latest --mount-point /mnt
```

If you'd like to restrict the mounted filesystem to only particular paths from
your archive, use the `--path` flag, similar to the `extract` action above.
For instance:

```bash
borgmatic mount --archive latest --mount-point /mnt --path var/lib
```

When you're all done exploring your files, unmount your mount point. No
`--archive` flag is needed:

```bash
borgmatic umount --mount-point /mnt
```

## Extract the configuration files used to create an archive

<span class="minilink minilink-addedin">New in version 1.7.15</span> borgmatic
automatically stores all the configuration files used to create an archive
inside the archive itself. They are stored in the archive using their full
paths from the machine being backed up. This is useful in cases where you've
lost a configuration file or you want to see what configurations were used to
create a particular archive.

To extract the configuration files from an archive, use the `config bootstrap`
action. For example:

```bash 
borgmatic config bootstrap --repository repo.borg --destination /tmp
```

This extracts the configuration file from the latest archive in the repository
`repo.borg` to `/tmp/etc/borgmatic/config.yaml`, assuming that the only
configuration file used to create this archive was located at
`/etc/borgmatic/config.yaml` when the archive was created.

Note that to run the `config bootstrap` action, you don't need to have a
borgmatic configuration file. You only need to specify the repository to use
via the `--repository` flag; borgmatic will figure out the rest.

If a destination directory is not specified, the configuration files will be
extracted to their original locations, silently *overwriting* any configuration
files that may already exist. For example, if a configuration file was located
at `/etc/borgmatic/config.yaml` when the archive was created, it will be
extracted to `/etc/borgmatic/config.yaml` too.

If you want to extract the configuration file from a specific archive, use the
`--archive` flag:

```bash
borgmatic config bootstrap --repository repo.borg --archive host-2023-01-02T04:06:07.080910 --destination /tmp
```

See the output of `config bootstrap --help` for additional flags you may need
for bootstrapping.

<span class="minilink minilink-addedin">New in version 1.8.1</span> Set the
`store_config_files` option to `false` to disable the automatic backup of
borgmatic configuration files, for instance if they contain sensitive
information you don't want to store even inside your encrypted backups. If you
do this though, the `config bootstrap` action will no longer work.
