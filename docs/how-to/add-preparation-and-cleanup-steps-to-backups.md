---
title: How to add preparation and cleanup steps to backups
eleventyNavigation:
  key: Add preparation and cleanup steps
  parent: How-to guides
  order: 8
---
## Preparation and cleanup hooks

If you find yourself performing prepraration tasks before your backup runs, or
cleanup work afterwards, borgmatic hooks may be of interest. Hooks are shell
commands that borgmatic executes for you at various points, and they're
configured in the `hooks` section of your configuration file. But if you're
looking to backup a database, it's probably easier to use the [database backup
feature](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/)
instead.

You can specify `before_backup` hooks to perform preparation steps before
running backups, and specify `after_backup` hooks to perform cleanup steps
afterwards. Here's an example:

```yaml
hooks:
    before_backup:
        - mount /some/filesystem
    after_backup:
        - umount /some/filesystem
```

The `before_backup` and `after_backup` hooks each run once per configuration
file. `before_backup` hooks run prior to backups of all repositories in a
configuration file, right before the `create` action. `after_backup` hooks run
afterwards, but not if an error occurs in a previous hook or in the backups
themselves.

There are additional hooks for the `prune` and `check` actions as well.
`before_prune` and `after_prune` run if there are any `prune` actions, while
`before_check` and `after_check` run if there are any `check` actions.

You can also use `before_everything` and `after_everything` hooks to perform
global setup or cleanup:

```yaml
hooks:
    before_everything:
        - set-up-stuff-globally
    after_everything:
        - clean-up-stuff-globally
```

`before_everything` hooks collected from all borgmatic configuration files run
once before all configuration files (prior to all actions), but only if there
is a `create` action. An error encountered during a `before_everything` hook
causes borgmatic to exit without creating backups.

`after_everything` hooks run once after all configuration files and actions,
but only if there is a `create` action. It runs even if an error occurs during
a backup or a backup hook, but not if an error occurs during a
`before_everything` hook.

borgmatic also runs `on_error` hooks if an error occurs, either when creating
a backup or running a backup hook. See the [monitoring and alerting
documentation](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/)
for more information.

## Hook output

Any output produced by your hooks shows up both at the console and in syslog
(when run in a non-interactive console). For more information, read about <a
href="https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/">inspecting
your backups</a>.

## Security

An important security note about hooks: borgmatic executes all hook commands
with the user permissions of borgmatic itself. So to prevent potential shell
injection or privilege escalation, do not forget to set secure permissions
on borgmatic configuration files (`chmod 0600`) and scripts (`chmod 0700`)
invoked by hooks.
