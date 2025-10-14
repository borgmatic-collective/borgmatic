---
title: How to backup to a removable drive or an intermittent server
eleventyNavigation:
  key: 💾 Backup to a removable drive/server
  parent: How-to guides
  order: 11
---
A common situation is backing up to a repository that's only sometimes online.
For instance, you might send most of your backups to the cloud, but
occasionally you want to plug in an external hard drive or backup to your
buddy's sometimes-online server for that extra level of redundancy.

But if you run borgmatic and your hard drive isn't plugged in, or your buddy's
server is offline, then you'll get an annoying error message and the overall
borgmatic run will fail (even if individual repositories still complete).

Another variant is when the source machine is only sometimes available for
backups, e.g. a laptop where you want to skip backups when the battery falls
below a certain level.

So what if you want borgmatic to swallow the error of a missing drive
or an offline server or a low battery—and exit gracefully? That's where the
concept of "soft failure" come in.


<a id="caveats-and-details"></a>


## Soft failure command hooks

This feature leverages [borgmatic command
hooks](https://torsion.org/borgmatic/how-to/add-preparation-and-cleanup-steps-to-backups/),
so familiarize yourself with them first. The idea is that you write a simple
test in the form of a borgmatic command hook to see if backups should proceed or
not.

The way the test works is that if any of your hook commands return a special
exit status of 75, that indicates to borgmatic that it's a temporary failure
and borgmatic should skip all subsequent actions for the current repository.

If you return any status besides 75, then it's a standard success or error.
(Zero is success; anything else other than 75 is an error).

So for instance, if you have an external drive that's only sometimes mounted,
declare its repository in its own [separate configuration
file](https://torsion.org/borgmatic/how-to/make-per-application-backups/),
say at `/etc/borgmatic.d/removable.yaml`:

```yaml
source_directories:
    - /home

repositories:
    - path: /mnt/removable/backup.borg
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `location:` section of your configuration.

<span class="minilink minilink-addedin">Prior to version 1.7.10</span> Omit
the `path:` portion of the `repositories` list.

Then, make a command hook in that same configuration file that uses the external
`findmnt` utility to see whether the drive is mounted before proceeding.

```yaml
commands:
    - before: repository
      run:
          - findmnt /mnt/removable > /dev/null || exit 75
```

<span class="minilink minilink-addedin">Prior to version 2.0.0</span> Use the
deprecated `before_actions` hook instead:

```yaml
before_actions:
    - findmnt /mnt/removable > /dev/null || exit 75
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put this
option in the `hooks:` section of your configuration.

<span class="minilink minilink-addedin">Prior to version 1.7.0</span> Use
`before_create` or similar instead of `before_actions`, which was introduced in
borgmatic 1.7.0.

What this does is check if the `findmnt` command errors when probing for a
particular mount point. If it does error, then it returns exit code 75 to
borgmatic. borgmatic logs the soft failure, skips all further actions for the
current repository, and proceeds onward to any other repositories and/or
configuration files you may have.

You can imagine a similar check for the sometimes-online server case:

```yaml
source_directories:
    - /home

repositories:
    - path: ssh://me@buddys-server.org/./backup.borg

commands:
    - before: repository
      run:
          - ping -q -c 1 buddys-server.org > /dev/null || exit 75
```

Or to only run backups if the battery level is high enough:

```yaml
commands:
    - before: repository
      run:
          - is_battery_percent_at_least.sh 25
```

Writing the battery script is left as an exercise to the reader.

See the [soft failure
documentation](https://torsion.org/borgmatic/reference/configuration/command-hooks/#soft-failure)
for additional details.
