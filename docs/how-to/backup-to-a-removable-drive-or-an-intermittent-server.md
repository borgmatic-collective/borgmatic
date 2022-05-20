---
title: How to backup to a removable drive or an intermittent server
eleventyNavigation:
  key: 💾 Backup to a removable drive/server
  parent: How-to guides
  order: 9
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
so first familiarize yourself with them. The idea is that you write a simple
test in the form of a borgmatic hook to see if backups should proceed or not.

The way the test works is that if any of your hook commands return a special
exit status of 75, that indicates to borgmatic that it's a temporary failure,
and borgmatic should skip all subsequent actions for that configuration file.
If you return any other status, then it's a standard success or error. (Zero is
success; anything else other than 75 is an error).

So for instance, if you have an external drive that's only sometimes mounted,
declare its repository in its own [separate configuration
file](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/),
say at `/etc/borgmatic.d/removable.yaml`:

```yaml
location:
    source_directories:
        - /home

    repositories:
        - /mnt/removable/backup.borg
```

Then, write a `before_backup` hook in that same configuration file that uses
the external `findmnt` utility to see whether the drive is mounted before
proceeding.

```yaml
hooks:
    before_backup:
      - findmnt /mnt/removable > /dev/null || exit 75
```

What this does is check if the `findmnt` command errors when probing for a
particular mount point. If it does error, then it returns exit code 75 to
borgmatic. borgmatic logs the soft failure, skips all further actions in that
configurable file, and proceeds onward to any other borgmatic configuration
files you may have.

You can imagine a similar check for the sometimes-online server case:

```yaml
location:
    source_directories:
        - /home

    repositories:
        - me@buddys-server.org:backup.borg

hooks:
    before_backup:
      - ping -q -c 1 buddys-server.org > /dev/null || exit 75
```

Or to only run backups if the battery level is high enough:

```yaml
hooks:
    before_backup:
      - is_battery_percent_at_least.sh 25
```

(Writing the battery script is left as an exercise to the reader.)


## Caveats and details

There are some caveats you should be aware of with this feature.

 * You'll generally want to put a soft failure command in the `before_backup`
   hook, so as to gate whether the backup action occurs. While a soft failure is
   also supported in the `after_backup` hook, returning a soft failure there
   won't prevent any actions from occuring, because they've already occurred!
   Similiarly, you can return a soft failure from an `on_error` hook, but at
   that point it's too late to prevent the error.
 * Returning a soft failure does prevent further commands in the same hook from
   executing. So, like a standard error, it is an "early out". Unlike a standard
   error, borgmatic does not display it in angry red text or consider it a
   failure.
 * The soft failure only applies to the scope of a single borgmatic
   configuration file. So put anything that you don't want soft-failed, like
   always-online cloud backups, in separate configuration files from your
   soft-failing repositories.
 * The soft failure doesn't have to apply to a repository. You can even perform
   a test to make sure that individual source directories are mounted and
   available. Use your imagination!
 * The soft failure feature also works for before/after hooks for other
   actions as well. But it is not implemented for `before_everything` or
   `after_everything`.
