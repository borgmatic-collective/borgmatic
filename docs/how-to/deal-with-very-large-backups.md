---
title: How to deal with very large backups
eleventyNavigation:
  key: 📏 Deal with very large backups
  parent: How-to guides
  order: 4
---
## Biggish data

Borg itself is great for efficiently de-duplicating data across successive
backup archives, even when dealing with very large repositories. But you may
find that while borgmatic's default mode of `prune`, `compact`, `create`, and
`check` works well on small repositories, it's not so great on larger ones.
That's because running the default pruning, compact, and consistency checks
take a long time on large repositories.

### A la carte actions

If you find yourself in this situation, you have some options. First, you can
run borgmatic's `prune`, `compact`, `create`, or `check` actions separately.
For instance, the following optional actions are available:

```bash
borgmatic prune
borgmatic compact
borgmatic create
borgmatic check
```

You can run with only one of these actions provided, or you can mix and match
any number of them in a single borgmatic run. This supports approaches like
skipping certain actions while running others. For instance, this skips
`prune` and `compact` and only runs `create` and `check`:

```bash
borgmatic create check
```

Or, you can make backups with `create` on a frequent schedule (e.g. with
`borgmatic create` called from one cron job), while only running expensive
consistency checks with `check` on a much less frequent basis (e.g. with
`borgmatic check` called from a separate cron job).


### Consistency check configuration

Another option is to customize your consistency checks. By default, if you
omit consistency checks from configuration, borgmatic runs full-repository
checks (`repository`) and per-archive checks (`archives`) within each
repository, no more than once a month. This is equivalent to what `borg check`
does if run without options.

But if you find that archive checks are too slow, for example, you can
configure borgmatic to run repository checks only. Configure this in the
`consistency` section of borgmatic configuration:

```yaml
consistency:
    checks:
        - name: repository
```

<span class="minilink minilink-addedin">Prior to version 1.6.2</span> `checks`
was a plain list of strings without the `name:` part. For example:

```yaml
consistency:
    checks:
        - repository
```


Here are the available checks from fastest to slowest:

 * `repository`: Checks the consistency of the repository itself.
 * `archives`: Checks all of the archives in the repository.
 * `extract`: Performs an extraction dry-run of the most recent archive.
 * `data`: Verifies the data integrity of all archives contents, decrypting and decompressing all data.

Note that the `data` check is a more thorough version of the `archives` check,
so enabling the `data` check implicitly enables the `archives` check as well.

See [Borg's check
documentation](https://borgbackup.readthedocs.io/en/stable/usage/check.html)
for more information.

### Check frequency

<span class="minilink minilink-addedin">New in version 1.6.2</span> You can
optionally configure checks to run on a periodic basis rather than every time
borgmatic runs checks. For instance:

```yaml
consistency:
    checks:
        - name: repository
          frequency: 2 weeks
        - name: archives
          frequency: 1 month
```

This tells borgmatic to run the `repository` consistency check at most once
every two weeks for a given repository and the `archives` check at most once a
month. The `frequency` value is a number followed by a unit of time, e.g. "3
days", "1 week", "2 months", etc. The `frequency` defaults to `always`, which
means run this check every time checks run.

Unlike a real scheduler like cron, borgmatic only makes a best effort to run
checks on the configured frequency. It compares that frequency with how long
it's been since the last check for a given repository (as recorded in a file
within `~/.borgmatic/checks`). If it hasn't been long enough, the check is
skipped. And you still have to run `borgmatic check` (or `borgmatic` without
actions) in order for checks to run, even when a `frequency` is configured!

This also applies *across* configuration files that have the same repository
configured. Make sure you have the same check frequency configured in each
though—or the most frequently configured check will apply.

If you want to temporarily ignore your configured frequencies, you can invoke
`borgmatic check --force` to run checks unconditionally.


### Disabling checks

If that's still too slow, you can disable consistency checks entirely,
either for a single repository or for all repositories.

Disabling all consistency checks looks like this:

```yaml
consistency:
    checks:
        - name: disabled
```

<span class="minilink minilink-addedin">Prior to version 1.6.2</span> `checks`
was a plain list of strings without the `name:` part. For instance:

```yaml
consistency:
    checks:
        - disabled
```

If you have multiple repositories in your borgmatic configuration file,
you can keep running consistency checks, but only against a subset of the
repositories:

```yaml
consistency:
    check_repositories:
        - path/of/repository_to_check.borg
```

Finally, you can override your configuration file's consistency checks, and
run particular checks via the command-line. For instance:

```bash
borgmatic check --only data --only extract
```

This is useful for running slow consistency checks on an infrequent basis,
separate from your regular checks. It is still subject to any configured
check frequencies unless the `--force` flag is used.


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
