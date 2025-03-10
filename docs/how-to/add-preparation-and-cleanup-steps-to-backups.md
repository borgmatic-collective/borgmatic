---
title: How to add preparation and cleanup steps to backups
eleventyNavigation:
  key: 🧹 Add preparation and cleanup steps
  parent: How-to guides
  order: 10
---
## Preparation and cleanup hooks

If you find yourself performing preparation tasks before your backup runs or
doing cleanup work afterwards, borgmatic command hooks may be of interest. These
are custom shell commands you can configure borgmatic to execute at various
points as it runs.

(But if you're looking to backup a database, it's probably easier to use the
[database backup
feature](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/)
instead.)

<span class="minilink minilink-addedin">New in version 1.9.14</span> Command
hooks are now configured via a list of `commands:` in your borgmatic
configuration file. For example:

```yaml
commands:
    - before: action
      when: [create]
      run:
          - echo "Before create!"
    - after: action
      when:
          - create
          - prune
      run:
          - echo "After create and/or prune!"
```

If a `run:` command contains a special YAML character such as a colon, you may
need to quote the entire string (or use a [multiline
string](https://yaml-multiline.info/)) to avoid an error:

```yaml
commands:
    - before: action
      when: [create]
      run:
          - "echo Backup: start"
```

Each command in the `commands:` list has the following options:

 * `before` or `after`: Name for the point in borgmatic's execution that the commands should be run before or after, one of:
    * `action` runs before each action for each repository. This replaces the deprecated `before_create`, `after_prune`, etc.
    * `repository` runs before or after all actions for each repository. This replaces the deprecated `before_actions` and `after_actions`.
    * `configuration` runs before or after all actions and repositories in the current configuration file.
    * `everything` runs before or after all configuration files. This replaces the deprecated `before_everything` and `after_everything`.
    * `error` runs after an error occurs—and it's only available for `after`. This replaces the deprecated `on_error` hook.
 * `when`: Actions (`create`, `prune`, etc.) for which the commands will be run. Defaults to running for all actions.
 * `run`: List of one or more shell commands or scripts to run when this command hook is triggered.

There's also another command hook that works a little differently:

```yaml
commands:
    - before: dump_data_sources
      hooks: [postgresql]
      run:
          - echo "Right before the PostgreSQL database dump!"
```

This command hook has the following options:

 * `before` or `after`: `dump_data_sources`
 * `hooks`: Names of other hooks that this command hook applies to, e.g. `postgresql`, `mariadb`, `zfs`, `btrfs`, etc. Defaults to all hooks of the relevant type.
 * `run`: One or more shell commands or scripts to run when this command hook is triggered.


### Order of execution

Here's a way of visualizing how all of these command hooks slot into borgmatic's
execution.

Let's say you've got a borgmatic configuration file with a configured
repository. And suppose you configure several command hooks and then run
borgmatic for the `create` and `prune` actions. Here's the order of execution:

 * Run `before: everything` hooks (from all configuration files).
    * Run `before: configuration` hooks (from the first configuration file).
        * Run `before: repository` hooks (for the first repository).
            * Run `before: action` hooks for `create`.
                * Run `before: dump_data_sources` hooks (e.g. for the PostgreSQL hook).
                * Actually dump data sources (e.g. PostgreSQL databases).
                * Run `after: dump_data_sources` hooks (e.g. for the PostgreSQL hook).
            * Actually run the `create` action.
            * Run `after: action` hooks for `create`.
            * Run `before: action` hooks for `prune`.
            * Actually run the `prune` action.
            * Run `after: action` hooks for `prune`.
        * Run `after: repository` hooks (for the first repository).
    * Run `after: configuration` hooks (from the first configuration file).
 * Run `after: everything` hooks (from all configuration files).

This same order of execution extends to multiple repositories and/or
configuration files.


### Deprecated command hooks

<span class="minilink minilink-addedin">Prior to version 1.9.14</span> The
command hooks worked a little differently. In these older versions of borgmatic,
you can specify `before_backup` hooks to perform preparation steps before
running backups and specify `after_backup` hooks to perform cleanup steps
afterwards. Here's an example:

```yaml
before_backup:
    - mount /some/filesystem
after_backup:
    - umount /some/filesystem
```

If your command contains a special YAML character such as a colon, you may
need to quote the entire string (or use a [multiline
string](https://yaml-multiline.info/)) to avoid an error:

```yaml
before_backup:
    - "echo Backup: start"
```

There are additional hooks that run before/after other actions as well. For
instance, `before_prune` runs before a `prune` action for a repository, while
`after_prune` runs after it.

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `hooks:` section of your configuration.

<span class="minilink minilink-addedin">New in version 1.7.0</span> The
`before_actions` and `after_actions` hooks run before/after all the actions
(like `create`, `prune`, etc.) for each repository. These hooks are a good
place to run per-repository steps like mounting/unmounting a remote
filesystem.

<span class="minilink minilink-addedin">New in version 1.6.0</span> The
`before_backup` and `after_backup` hooks each run once per repository in a
configuration file. `before_backup` hooks runs right before the `create`
action for a particular repository, and `after_backup` hooks run afterwards,
but not if an error occurs in a previous hook or in the backups themselves.
(Prior to borgmatic 1.6.0, these hooks instead ran once per configuration file
rather than once per repository.)


## Variable interpolation

The command action hooks support interpolating particular runtime variables into
the commands that are run. Here's an example that assumes you provide a separate
shell script:

```yaml
commands:
    - after: action
      when: [prune]
      run:
          - record-prune.sh "{configuration_filename}" "{repository}"
```

In this example, when the hook is triggered, borgmatic interpolates runtime
values into the hook command: the borgmatic configuration filename and the
paths of the current Borg repository. Here's the full set of supported
variables you can use here:

 * `configuration_filename`: borgmatic configuration filename in which the
   hook was defined
 * `log_file`
   <span class="minilink minilink-addedin">New in version 1.7.12</span>:
   path of the borgmatic log file, only set when the `--log-file` flag is used
 * `repository`: path of the current repository as configured in the current
   borgmatic configuration file
 * `repository_label` <span class="minilink minilink-addedin">New in version
   1.8.12</span>: label of the current repository as configured in the current
   borgmatic configuration file

Not all command hooks support all variables. For instance, the `everything` and
`configuration` hooks don't support repository variables because those hooks
don't run in the context of a single repository.

Note that you can also interpolate in [arbitrary environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).


## Global hooks

You can also use `before_everything` and `after_everything` hooks to perform
global setup or cleanup:

```yaml
before_everything:
    - set-up-stuff-globally
after_everything:
    - clean-up-stuff-globally
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `hooks:` section of your configuration.

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
(when enabled). For more information, read about <a
href="https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/">inspecting
your backups</a>.


## Security

An important security note about hooks: borgmatic executes all hook commands
with the user permissions of borgmatic itself. So to prevent potential shell
injection or privilege escalation, do not forget to set secure permissions
on borgmatic configuration files (`chmod 0600`) and scripts (`chmod 0700`)
invoked by hooks.
