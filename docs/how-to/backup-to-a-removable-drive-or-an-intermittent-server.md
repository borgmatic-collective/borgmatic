---
title: How to backup to a removable drive or an intermittent server
eleventyNavigation:
  key: 💾 Backup to a removable drive/server
  parent: How-to guides
  order: 11
---
## Occasional backups

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


## Soft failure command hooks

This feature leverages [borgmatic command
hooks](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/),
so familiarize yourself with them first. The idea is that you write a simple
test in the form of a borgmatic command hook to see if backups should proceed or
not.

The way the test works is that if any of your hook commands return a special
exit status of 75, that indicates to borgmatic that it's a temporary failure,
and borgmatic should skip all subsequent actions for the current repository.

If you return any status besides 75, then it's a standard success or error.
(Zero is success; anything else other than 75 is an error).

So for instance, if you have an external drive that's only sometimes mounted,
declare its repository in its own [separate configuration
file](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/),
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


## Caveats and details

There are some caveats you should be aware of with this feature.

 * You'll generally want to put a soft failure command in a `before` command
   hook, so as to gate whether the backup action occurs. While a soft failure is
   also supported in an `after` command hook, returning a soft failure there
   won't prevent any actions from occurring, because they've already occurred!
   Similarly, you can return a soft failure from an `error` command hook, but at
   that point it's too late to prevent the error.
 * Returning a soft failure does prevent further commands in the same hook from
   executing. So, like a standard error, it is an "early out." Unlike a standard
   error, borgmatic does not display it in angry red text or consider it a
   failure.
 * <span class="minilink minilink-addedin">New in version 1.9.0</span> Soft
   failures in `action` or `before_*` command hooks only skip the current
   repository rather than all repositories in a configuration file.
 * If you're writing a soft failure script that you want to vary based on the
   current repository, for instance so you can have multiple repositories in a
   single configuration file, have a look at [command hook variable
   interpolation](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/#variable-interpolation).
   And there's always still the option of putting anything that you don't want
   soft-failed (like always-online cloud backups) in separate configuration
   files from your soft-failing repositories.
 * The soft failure doesn't have to test anything related to a repository. You
   can even perform a test that individual source directories are mounted and
   available. Use your imagination!
 * Soft failures are not currently implemented for `everything`,
   `before_everything`, or `after_everything` command hooks.
