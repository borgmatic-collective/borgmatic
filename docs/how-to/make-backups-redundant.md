---
title: How to make backups redundant
---
## Multiple repositories

If you really care about your data, you probably want more than one backup of
it. borgmatic supports this in its configuration by specifying multiple backup
repositories. Here's an example:

```yaml
location:
    # List of source directories to backup.
    source_directories:
        - /home
        - /etc

    # Paths of local or remote repositories to backup to.
    repositories:
        - k8pDxu32@k8pDxu32.repo.borgbase.com:repo
        - 1234@usw-s001.rsync.net:backups.borg
        - /var/lib/backups/local.borg
```

When you run borgmatic with this configuration, it invokes Borg once for each
configured repository in sequence. (So, not in parallel.) That means—in each
repository—borgmatic creates a single new backup archive containing all of
your source directories.

Here's a way of visualizing what borgmatic does with the above configuration:

2. Backup `/home` and `/etc` to `k8pDxu32@k8pDxu32.repo.borgbase.com:repo`
1. Backup `/home` and `/etc` to `1234@usw-s001.rsync.net:backups.borg`
3. Backup `/home` and `/etc` to `/var/lib/backups/local.borg`

This gives you redundancy of your data across repositories and even
potentially across providers.

See [Borg repository URLs
documentation](https://borgbackup.readthedocs.io/en/stable/usage/general.html#repository-urls)
for more information on how to specify local and remote repository paths.


## Related documentation

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups/)
 * [Make per-application backups](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/)
 * [Backup to a removable drive or an intermittent server](https://torsion.org/borgmatic/docs/how-to/backup-to-a-removable-drive-or-an-intermittent-server/)
