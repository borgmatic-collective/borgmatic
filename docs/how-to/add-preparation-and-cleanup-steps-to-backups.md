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

<span class="minilink minilink-addedin">New in version 2.0.0</span> Command
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
          - echo "After create or prune!"
    - after: error
      run:
          - echo "Something went wrong!"
```

If you're coming from an older version of borgmatic, there is tooling to help
you [upgrade your
configuration](https://torsion.org/borgmatic/docs/how-to/upgrade/#upgrading-your-configuration)
to this new command hook format.

Note that if a `run:` command contains a special YAML character such as a colon,
you may need to quote the entire string (or use a [multiline
string](https://yaml-multiline.info/)) to avoid an error:

```yaml
commands:
    - before: action
      when: [create]
      run:
          - "echo Backup: start"
```

By default, an `after` command hook runs even if an error occurs in the
corresponding `before` hook or between those two hooks. This allows you to
perform cleanup steps that correspond to `before` preparation commands—even when
something goes wrong. You may notice that this is a departure from the way that
the deprecated `after_*` hooks worked in borgmatic prior to version 2.0.0.

<span class="minilink minilink-addedin">New in version 2.0.3</span> You can
customize this behavior with the `states` option. For instance, here's an
example of an `after` hook that only triggers on success and not on error:

```yaml
commands:
    - after: action
      when: [create]
      states: [finish]
      run:
          - echo "After successful create!"
```

Each command in the `commands:` list has the following options:

 * `before` or `after`: Name for the point in borgmatic's execution that the commands should be run before or after, one of:
    * `action` runs before each action for each repository. This replaces the deprecated `before_create`, `after_prune`, etc.
    * `repository` runs before or after all actions for each repository. This replaces the deprecated `before_actions` and `after_actions`.
    * `configuration` runs before or after all actions and repositories in the current configuration file.
    * `everything` runs before or after all configuration files. Errors here do not trigger `error` hooks or the `fail` state in monitoring hooks. This replaces the deprecated `before_everything` and `after_everything`.
    * `error` runs after an error occurs—and it's only available for `after`. This replaces the deprecated `on_error` hook.
 * `when`: Only trigger the hook when borgmatic is run with particular actions (`create`, `prune`, etc.) listed here. Defaults to running for all actions.
 * `states`: <span class="minilink minilink-addedin">New in version 2.0.3</span> Only trigger the hook if borgmatic encounters one of the states (execution results) listed here. This state is evaluated only for the scope of the configured `action`, `repository`, etc., rather than for the entire borgmatic run. Only available for `after` hooks. Defaults to running the hook for all states. One or more of:
    * `finish`: No errors occurred.
    * `fail`: An error occurred.
 * `run`: List of one or more shell commands or scripts to run when this command hook is triggered.

When command hooks run, they respect the `working_directory` option if it is
configured, meaning that the hook commands are run in that directory.

<span class="minilink minilink-addedin">New in version 2.0.4</span>If the exact
same `everything` command hook is present in multiple configuration files,
borgmatic only runs it once.

borgmatic's `--repository` flag does not impact which command hooks get run. But
you can use the `--config` flag to limit the configuration files (and thus
command hooks) used.


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
            * Actually run the `create` action (e.g. `borg create`).
            * Run `after: action` hooks for `create`.
            * Run `before: action` hooks for `prune`.
            * Actually run the `prune` action (e.g. `borg prune`).
            * Run `after: action` hooks for `prune`.
        * Run `after: repository` hooks (for the first repository).
    * Run `after: configuration` hooks (from the first configuration file).
    * Run `after: error` hooks (if an error occurs).
 * Run `after: everything` hooks (from all configuration files).

This same order of execution extends to multiple repositories and/or
configuration files.

Based on the above, you can see the difference between, say, an `after: action`
hook with `states: [fail]` and an `after: error` hook. The `after: action hook`
runs immediately after the create action fails for a particular repository—so
before any subsequent actions for that repository or other repositories even
have a chance to run. Whereas the `after: error` hook doesn't run until all
actions for—and repositories in—a configuration file have had a chance to
execute.

And if there are multiple hooks defined for a particular step (e.g. `before:
action` for `create`), then those hooks are run in the order they're defined in
configuration.


### Deprecated command hooks

<span class="minilink minilink-addedin">Prior to version 2.0.0</span> The
command hooks worked a little differently. In these older versions of borgmatic,
you can specify `before_backup` hooks to perform preparation steps before
running backups and specify `after_backup` hooks to perform cleanup steps
afterwards. These deprecated command hooks still work in version 2.0.0+,
although see below about a few semantic differences starting in that version.

Here's an example of these deprecated hooks:

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

<span class="minilink minilink-addedin">New in version 2.0.0</span> An `after_*`
command hook runs even if an error occurs in the corresponding `before_*` hook
or between those two hooks. This allows you to perform cleanup steps that
correspond to `before_*` preparation commands—even when something goes wrong.

<span class="minilink minilink-addedin">New in version 2.0.0</span> When command
hooks run, they respect the `working_directory` option if it is configured,
meaning that the hook commands are run in that directory.

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

`on_error` hooks run when an error occurs, but only if there is a `create`,
`prune`, `compact`, or `check` action. For instance, borgmatic can run
configurable shell commands to fire off custom error notifications or take other
actions, so you can get alerted as soon as something goes wrong. Here's a
not-so-useful example:

```yaml
on_error:
    - echo "Error while creating a backup or running a backup hook."
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

The `on_error` hook supports interpolating particular runtime variables into
the hook command. Here's an example that assumes you provide a separate shell
script to handle the alerting:

```yaml
on_error:
    - send-text-message.sh
```

borgmatic does not run `on_error` hooks if an error occurs within a
`before_everything` or `after_everything` hook.


## Variable interpolation

The command action hooks support interpolating particular runtime variables into
the commands that are run. Here's are a couple examples that assume you provide
separate shell scripts:

```yaml
commands:
    - after: action
      when: [prune]
      run:
          - record-prune.sh {configuration_filename} {repository}
    - after: error
      when: [create]
      run:
          - send-text-message.sh {configuration_filename} {repository}
```

In this example, when the hook is triggered, borgmatic interpolates runtime
values into each hook command: the borgmatic configuration filename and the
paths of the current Borg repository.

Here's the full set of supported variables you can use here:

 * `configuration_filename`: borgmatic configuration filename in which the
   hook was defined
 * `log_file`
   <span class="minilink minilink-addedin">New in version 1.7.12</span>:
   path of the borgmatic log file, only set when the `--log-file` flag is used
 * `repository`: path of the current repository as configured in the current
   borgmatic configuration file, if applicable to the current hook
 * `repository_label` <span class="minilink minilink-addedin">New in version
   1.8.12</span>: label of the current repository as configured in the current
   borgmatic configuration file, if applicable to the current hook
 * `error`: the error message itself, only applies to `error` hooks
 * `output`: output of the command that failed, only applies to `error` hooks
   (may be blank if an error occurred without running a command)

Not all command hooks support all variables. For instance, the `everything` and
`configuration` hooks don't support repository variables because those hooks
don't run in the context of a single repository. But the deprecated command
hooks (`before_backup`, `on_error`, etc.) do generally support variable
interpolation.

borgmatic automatically escapes these interpolated values to prevent shell
injection attacks. One implication is that you shouldn't wrap the interpolated
values in your own quotes, as that will interfere with the quoting performed by
borgmatic and result in your command receiving incorrect arguments. For
instance, this won't work:

```yaml
commands:
    - after: error
      run:
          # Don't do this! It won't work, as the {error} value is already quoted.
          - send-text-message.sh "Uh oh: {error}"
```

Do this instead:

```yaml
commands:
    - after: error
      run:
          - send-text-message.sh {error}
```

Note that you can also interpolate [arbitrary environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).


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
