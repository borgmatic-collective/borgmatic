---
title: 🧹 How to add preparation and cleanup steps to backups
eleventyNavigation:
  key: 🧹 Add preparation and cleanup steps
  parent: How-to guides
  order: 10
---
If you find yourself performing preparation tasks before your backup runs or
doing cleanup work afterwards, borgmatic command hooks may be of interest. These
are custom shell commands you can configure borgmatic to execute at various
points as it runs.

(But if you're looking to backup a database, it's probably easier to use the
[database backup
feature](https://torsion.org/borgmatic/how-to/backup-your-databases/)
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
configuration](https://torsion.org/borgmatic/how-to/upgrade/#upgrading-your-configuration)
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

See the [command hooks
documentation](https://torsion.org/borgmatic/reference/configuration/command-hooks/)
for additional details about how to configure command hooks.


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


## Hook output

Any output produced by your hooks shows up both at the console and in syslog
(when enabled). For more information, see the <a
href="https://torsion.org/borgmatic/reference/command-line/logging/">logging
documentation</a>.


## Security

An important security note about hooks: borgmatic executes all hook commands
with the user permissions of borgmatic itself. So to prevent potential shell
injection or privilege escalation, do not forget to set secure permissions
on borgmatic configuration files (`chmod 0600`) and scripts (`chmod 0700`)
invoked by hooks.
