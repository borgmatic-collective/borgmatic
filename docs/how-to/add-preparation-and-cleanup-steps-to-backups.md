---
title: How to add preparation and cleanup steps to backups
eleventyNavigation:
  key: 🧹 Add preparation and cleanup steps
  parent: How-to guides
  order: 9
---
## Preparation and cleanup hooks

If you find yourself performing preparation tasks before your backup runs, or
cleanup work afterwards, borgmatic hooks may be of interest. Hooks are shell
commands that borgmatic executes for you at various points as it runs, and
they're configured in the `hooks` section of your configuration file. But if
you're looking to backup a database, it's probably easier to use the [database
backup
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

<span class="minilink minilink-addedin">New in version 1.6.0</span> The
`before_backup` and `after_backup` hooks each run once per repository in a
configuration file. `before_backup` hooks runs right before the `create`
action for a particular repository, and `after_backup` hooks run afterwards,
but not if an error occurs in a previous hook or in the backups themselves.
(Prior to borgmatic 1.6.0, these hooks instead ran once per configuration file
rather than once per repository.)

There are additional hooks that run before/after other actions as well. For
instance, `before_prune` runs before a `prune` action for a repository, while
`after_prune` runs after it.

<span class="minilink minilink-addedin">New in version 1.7.0</span> The
`before_actions` and `after_actions` hooks run before/after all the actions
(like `create`, `prune`, etc.) for each repository. These hooks are a good
place to run per-repository steps like mounting/unmounting a remote
filesystem.


## Variable interpolation

The before and after action hooks support interpolating particular runtime
variables into the hook command. Here's an example that assumes you provide a
separate shell script:

```yaml
hooks:
    after_prune:
        - record-prune.sh "{configuration_filename}" "{repository}"
```

In this example, when the hook is triggered, borgmatic interpolates runtime
values into the hook command: the borgmatic configuration filename and the
paths of the current Borg repository. Here's the full set of supported
variables you can use here:

 * `configuration_filename`: borgmatic configuration filename in which the
   hook was defined
 * `repository`: path of the current repository as configured in the current
   borgmatic configuration file

Note that you can also interpolate in [arbitrary environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).


## Global hooks

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

## Error hooks

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
