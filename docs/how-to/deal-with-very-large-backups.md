---
title: 📏 How to deal with very large backups
eleventyNavigation:
  key: 📏 Deal with very large backups
  parent: How-to guides
  order: 4
---
<a id="a-la-carte-actions"></a>

Borg itself is great for efficiently de-duplicating data across successive
backup archives, even when dealing with very large repositories. But you may
find that while borgmatic's default actions of `create`, `prune`, `compact`,
and `check` works well on small repositories, it's not so great on larger
ones. That's because running the default pruning, compact, and consistency
checks take a long time on large repositories.

See the [actions
documentation](https://torsion.org/borgmatic/reference/command-line/actions/)
for details on customizing the actions that borgmatic runs.


<a id="spot-check"></a>
<a id="check-frequency"></a>
<a id="check-days"></a>
<a id="running-only-checks"></a>
<a id="disabling-checks"></a>


### Consistency check configuration

Another way of dealing with large backups is to customize your consistency
checks. By default, if you omit consistency checks from configuration, borgmatic
runs full-repository checks and per-archive checks within each repository on a
monthly basis.

But if you find that archive checks are too slow and/or you'd like to customize
the check frequency, see the [consistency checks
documentation](https://torsion.org/borgmatic/reference/configuration/consistency-checks/)
for details.


## Troubleshooting

### Broken pipe with remote repository

When running borgmatic on a large remote repository, you may receive errors
like the following, particularly while "borg check" is validating backups for
consistency:

```text
    Write failed: Broken pipe
    borg: Error: Connection closed by remote host
```

This error can be caused by an ssh timeout, which you can rectify by adding
the following to the `~/.ssh/config` file on the client:

```text
    Host *
        ServerAliveInterval 120
```

This should make the client keep the connection alive while validating
backups.
