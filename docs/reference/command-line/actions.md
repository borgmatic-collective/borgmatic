---
title: Actions
eleventyNavigation:
  key: 🎬 Actions
  parent: 💻 Command-line
---
An action in borgmatic is like a subcommand in Borg. The `create` action creates
a backup, the `list` action shows the files in an archive, and so on.


## Default actions

If you omit `create` and other actions from the command-line, borgmatic runs
through a set of default actions:

1. `prune` any old backups as per the configured retention policy
2. `compact` segments to free up space (with Borg 1.2+ and borgmatic 1.5.23+)
3. `create` a backup
4. `check` backups for consistency problems due to things like file damage

<span class="minilink minilink-addedin">Prior to version 1.7.9</span> The
default action ordering was `prune`, `compact`, `create`, and `check`.

### Disabling default actions

If you want to disable this default action behavior and require explicit actions
to be specified, add the following to your configuration:

```yaml
default_actions: false
```

With this setting, running `borgmatic` without arguments will show the help
message instead of performing any actions.


## A la carte actions

If you find yourself wanting to customize the actions, you have some options.
First, you can run borgmatic's `create`, `prune`, `compact`, or `check`
actions separately. For instance, the following optional actions are
available (among others):

```bash
borgmatic create
borgmatic prune
borgmatic compact
borgmatic check
```

You can run borgmatic with only one of these actions provided, or you can mix
and match any number of them in a single borgmatic run. This supports
approaches like skipping certain actions while running others. For instance,
this skips `prune` and `compact` and only runs `create` and `check`:

```bash
borgmatic create check
```

<span class="minilink minilink-addedin">New in version 1.7.9</span> borgmatic
now respects your specified command-line action order, running actions in the
order you specify. In previous versions, borgmatic ran your specified actions
in a fixed ordering regardless of the order they appeared on the command-line.

But instead of running actions together, another option is to run backups with
`create` on a frequent schedule (e.g. with `borgmatic create` called from one
cron job), while only running expensive consistency checks with `check` on a
much less frequent basis (e.g. with `borgmatic check` called from a separate
cron job).

<span class="minilink minilink-addedin">New in version 1.8.5</span> Instead of
(or in addition to) specifying actions on the command-line, you can configure
borgmatic to [skip particular
actions](https://torsion.org/borgmatic/how-to/set-up-backups/#skipping-actions).


### Skipping actions

<span class="minilink minilink-addedin">New in version 1.8.5</span> You can
configure borgmatic to skip running certain actions (default or otherwise).
For instance, to always skip the `compact` action (e.g., when using [Borg's
append-only
mode](https://borgbackup.readthedocs.io/en/stable/usage/notes.html#append-only-mode-forbid-compaction)),
set the `skip_actions` option in your configuration:

```yaml
skip_actions:
    - compact
```
