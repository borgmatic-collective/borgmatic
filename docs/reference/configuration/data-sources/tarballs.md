---
title: Tarballs
eleventyNavigation:
  key: Tarballs
  parent: 🗄️ Data sources
---

If you backup [tarballs](https://en.wikipedia.org/wiki/Tar_(computing)) as part
of your source directories, Borg can't effectively deduplicate their contents
because of the way that a tarball's files are packed together (and often
compressed). This isn't a big deal for small tarballs, but it can really hurt
for large ones like virtual machine exports.

<span class="minilink minilink-addedin">New in version 2.1.11</span> <span
class="minilink minilink-addedin">beta feature</span> borgmatic supports
configuring tarballs as data sources for backups, unpacking their contained
files directly into a Borg archive so that deduplication works properly.

To take advantage of this feature, use the `tarballs:` hook. For example:

```yaml
tarballs:
    - name: virtual-machine
      path: /var/lib/vz/dump/vzdump-vm.tar
```

And to restore such a tarball to its original path:

```bash
borgmatic restore --archive latest --data-source virtual-machine
```

During backup, borgmatic streams each tarball to Borg, unpacking its files
directly into the created Borg archive. Under the hood, this doesn't use Borg's
native `import-tar`, because that's limited to a single tarball per archive (and
no additional source directories).

Upon
[restore](https://torsion.org/borgmatic/reference/command-line/actions/restore/),
borgmatic exports the tarball from the archive, rewriting it on the fly to
inject its original file permissions, ownership, symlinks, etc. The resulting
tarball ends up at its original `path` (or `restore_path`).

Both `create` and `restore` operate without using any temporary files for
tarball data.


## Limitmations

 * Within an archive, tarball contents are not stored at their original path.
   Instead, they are stored within `borgmatic/tarballs/` so that the `restore`
   action can find them.
 * Due to the way that borgmatic streams tarballs to Borg via named pipes,
   per-file information (permissions, ownership, symlink targets, etc.) and
   stored separately in a per-tarball manifest file. This is consumed by the
   `restore` action.
 * During restore, borgmatic attempts to match the compression (if any) of the
   original tarball based on its file extension. If it can't determine the
   compression method, it errors.
 * If a tarball that you've configured under `tarballs:` also appears in your
   source directories, it will get backed up twice—once tarred and once
   untarred. You can of course add an exclude if you'd like a tarball to only
   get backed up once.
 * When this hook is enabled, borgmatic instructs Borg to consume special files
   (via `--read-special`) to support tarball streaming—regardless of the value
   of your `read_special` configuration option.


## Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/tarballs.yaml %}
```
