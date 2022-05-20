---
title: How to deal with very large backups
eleventyNavigation:
  key: 📏 Deal with very large backups
  parent: How-to guides
  order: 3
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

(No borgmatic `prune`, `create`, or `check` actions? Try the old-style
`--prune`, `--create`, or `--check`. Or upgrade borgmatic!)

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

Another option is to customize your consistency checks. The default
consistency checks run both full-repository checks and per-archive checks
within each repository.

But if you find that archive checks are too slow, for example, you can
configure borgmatic to run repository checks only. Configure this in the
`consistency` section of borgmatic configuration:

```yaml
consistency:
    checks:
        - repository
```

Here are the available checks from fastest to slowest:

 * `repository`: Checks the consistency of the repository itself.
 * `archives`: Checks all of the archives in the repository.
 * `extract`: Performs an extraction dry-run of the most recent archive.
 * `data`: Verifies the data integrity of all archives contents, decrypting and decompressing all data (implies `archives` as well).

See [Borg's check documentation](https://borgbackup.readthedocs.io/en/stable/usage/check.html) for more information.

If that's still too slow, you can disable consistency checks entirely,
either for a single repository or for all repositories.

Disabling all consistency checks looks like this:

```yaml
consistency:
    checks:
        - disabled
```

Or, if you have multiple repositories in your borgmatic configuration file,
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
separate from your regular checks.


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
