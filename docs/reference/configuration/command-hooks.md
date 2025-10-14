---
title: Command hooks
eleventyNavigation:
  key: 🪝 Command hooks
  parent: ⚙️  Configuration
---
<span class="minilink minilink-addedin">New in version 2.0.0</span> Command
hooks are configured via a list of `commands:` in your borgmatic
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

Each command in the `commands:` list has the following options:

 * `before` or `after`: Name for the point in borgmatic's execution that the commands should be run before or after, one of:
    * `action` runs before or after each action for each repository. This replaces the deprecated `before_create`, `after_prune`, etc.
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


## Order of execution

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
variables](https://torsion.org/borgmatic/reference/configuration/environment-variables/).


## Soft failure

If any of your hook commands return a special exit status of 75, that indicates
to borgmatic that it's a temporary failure and borgmatic should skip all
subsequent actions for the current repository.

If you return any status besides 75, then it's a standard success or error.
(Zero is success; anything else other than 75 is an error).

Example of a soft failure command:

```yaml
commands:
    - before: repository
      run:
          - findmnt /mnt/removable > /dev/null || exit 75
```

### Caveats and details

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
   single configuration file, have a look at [variable
   interpolation](#variable-interpolation) above.
   And there's always still the option of putting anything that you don't want
   soft-failed (like always-online cloud backups) in separate configuration
   files from your soft-failing repositories.
 * The soft failure doesn't have to test anything related to a repository. You
   can even perform a test that individual source directories are mounted and
   available. Use your imagination!
 * Soft failures are not currently implemented for `everything`,
   `before_everything`, or `after_everything` command hooks.


## Full configuration

```yaml
{% include borgmatic/commands.yaml %}
```
