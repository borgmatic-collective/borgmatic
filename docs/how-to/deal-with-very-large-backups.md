---
title: How to deal with very large backups
---
## Biggish data

Borg itself is great for efficiently de-duplicating data across successive
backup archives, even when dealing with very large repositories. However, you
may find that while borgmatic's default mode of "prune, create, and check"
works well on small repositories, it's not so great on larger ones. That's
because running the default consistency checks just takes a long time on large
repositories.

### A la carte actions

If you find yourself in this situation, you have some options. First, you can
run borgmatic's pruning, creating, or checking actions separately. For
instance, the the following optional flags are available:

```bash
borgmatic --prune
borgmatic --create
borgmatic --check
```

You can run with only one of these flags provided, or you can mix and match
any number of them in a single borgmatic run. This supports approaches like
making backups with `--create` on a frequent schedule, while only running
expensive consistency checks with `--check` on a much less frequent basis from
a separate cron job.

### Consistency check configuration

Another option is to customize your consistency checks. The default
consistency checks run both full-repository checks and per-archive checks
within each repository.

But if you find that archive checks are just too slow, for example, you can
configure borgmatic to run repository checks only. Configure this in the
`consistency` section of borgmatic configuration:

```yaml
consistency:
    checks:
        - repository
```

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

## Related documentation

 * [How to set up backups with borgmatic](../../docs/how-to/set-up-backups.md)
 * [borgmatic README](../../../../)
