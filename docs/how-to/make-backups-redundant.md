---
title: How to make backups redundant
eleventyNavigation:
  key: ☁️  Make backups redundant
  parent: How-to guides
  order: 3
---
If you really care about your data, you probably want more than one backup of
it. borgmatic supports this in its configuration by specifying multiple backup
repositories. Here's an example:

```yaml
# List of source directories to backup.
source_directories:
    - /home
    - /etc

# Paths of local or remote repositories to backup to.
repositories:
    - path: ssh://k8pDxu32@k8pDxu32.repo.borgbase.com/./repo
    - path: /var/lib/backups/local.borg
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `location:` section of your configuration.

<span class="minilink minilink-addedin">Prior to version 1.7.10</span> Omit
the `path:` portion of the `repositories` list.

When you run borgmatic with this configuration, it invokes Borg once for each
configured repository in sequence. (So, not in parallel.) That means—in each
repository—borgmatic creates a single new backup archive containing all of
your source directories.

Here's a way of visualizing what borgmatic does with the above configuration:

1. Backup `/home` and `/etc` to `k8pDxu32@k8pDxu32.repo.borgbase.com:repo`
2. Backup `/home` and `/etc` to `/var/lib/backups/local.borg`

This gives you redundancy of your data across repositories and even
potentially across providers.

See [Borg repository URLs
documentation](https://borgbackup.readthedocs.io/en/stable/usage/general.html#repository-urls)
for more information on how to specify local and remote repository paths.

### Different options per repository

What if you want borgmatic to backup to multiple repositories—while also
setting different options for each one? In that case, you'll need to use
[a separate borgmatic configuration file for each
repository](https://torsion.org/borgmatic/how-to/make-per-application-backups/)
instead of the multiple repositories in one configuration file as described
above. That's because all of the repositories in a particular configuration
file get the same options applied.
