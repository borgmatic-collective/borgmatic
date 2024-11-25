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
find that while borgmatic's default actions of `create`, `prune`, `compact`,
and `check` works well on small repositories, it's not so great on larger
ones. That's because running the default pruning, compact, and consistency
checks take a long time on large repositories.

<span class="minilink minilink-addedin">Prior to version 1.7.9</span> The
default action ordering was `prune`, `compact`, `create`, and `check`.

### A la carte actions

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
actions](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#skipping-actions).


### Consistency check configuration

Another option is to customize your consistency checks. By default, if you
omit consistency checks from configuration, borgmatic runs full-repository
checks (`repository`) and per-archive checks (`archives`) within each
repository, running the checks on a monthly basis. (See below about setting
your own check frequency.)

But if you find that archive checks are too slow, for example, you can
configure borgmatic to run repository checks only. Configure this in the
`consistency` section of borgmatic configuration:

```yaml
checks:
    - name: repository
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `consistency:` section of your configuration.

<span class="minilink minilink-addedin">Prior to version 1.6.2</span> The
`checks` option was a plain list of strings without the `name:` part, and
borgmatic ran each configured check every time checks were run. For example:

```yaml
checks:
    - repository
```


Here are the available checks, roughly from fastest to slowest:

 * `archives`: Checks all of the archives' metadata in the repository.
 * `repository`: Checks the consistency of the whole repository. The checks run
   on the server and do not cause significant network traffic.
 * `extract`: Performs an extraction dry-run of the latest archive.
 * `data`: Verifies the data integrity of all archives contents, decrypting
   and decompressing all data.
 * `spot`: Compares file counts and contents between your source files and the
   latest archive.

Note that the `data` check is a more thorough version of the `archives` check,
so enabling the `data` check implicitly enables the `archives` check as well.

See [Borg's check
documentation](https://borgbackup.readthedocs.io/en/stable/usage/check.html)
for more information.


### Spot check

The various consistency checks all have trade-offs around speed and
thoroughness, but most of them don't even look at your original source
files—arguably one important way to ensure your backups contain the files
you'll want to restore in the case of catastrophe (or an accidentally deleted
file). Because if something goes wrong with your source files, most
consistency checks will still pass with flying colors and you won't discover
there's a problem until you go to restore.

<span class="minilink minilink-addedin">New in version 1.8.10</span> That's
where the spot check comes in. This check actually compares your source file
counts and data against those in the latest archive, potentially catching
problems like incorrect excludes, inadvertent deletes, files changed by
malware, etc.

But because an exhaustive comparison of all source files against the latest
archive might be too slow, the spot check supports *sampling* a percentage of
your source files for the comparison, ensuring they fall within configured
tolerances.

Here's how it works. Start by installing the `xxhash` OS package if you don't
already have it, so the spot check can run the `xxh64sum` command and
efficiently hash files for comparison. Then add something like the following
to your borgmatic configuration:

```yaml
checks:
    - name: spot
      count_tolerance_percentage: 10
      data_sample_percentage: 1
      data_tolerance_percentage: 0.5
```

The `count_tolerance_percentage` is the percentage delta between the source
directories file count and the latest backup archive file count that is
allowed before the entire consistency check fails. For instance, if the spot
check runs and finds 100 source files on disk and 105 files in the latest
archive, that would be within the configured 10% count tolerance and the check
would succeed. But if there were 100 source files and 200 archive files, the
check would fail. (100 source files and only 50 archive files would also
fail.)

The `data_sample_percentage` is the percentage of total files in the source
directories to randomly sample and compare to their corresponding files in the
latest backup archive. A higher value allows a more accurate check—and a
slower one. The comparison is performed by hashing the selected source files
and counting hashes that don't match the latest archive. For instance, if you
have 1,000 source files and your sample percentage is 1%, then only 10 source
files will be compared against the latest archive. These sampled files are
selected randomly each time, so in effect the spot check is probabilistic.

The `data_tolerance_percentage` is the percentage of total files in the source
directories that can fail a spot check data comparison without failing the
entire consistency check. The value must be lower than or equal to the
`data_sample_percentage`, because `data_tolerance_percentage` only looks at
at the sampled files as determined by `data_sample_percentage`.

All three options are required when using the spot check. And because the
check relies on these configured tolerances, it may not be a
set-it-and-forget-it type of consistency check, at least until you get the
tolerances dialed in so there are minimal false positives or negatives. It is
recommended you run `borgmatic check` several times after configuring the spot
check, tweaking your tolerances as needed. For certain workloads where your
source files experience wild swings of file contents or counts, the spot check
may not suitable at all.

What if you add, delete, or change a bunch of your source files and you don't
want the spot check to fail the next time it's run? Run `borgmatic create` to
create a new backup, thereby allowing the next spot check to run against an
archive that contains your recent changes.

Because the spot check only looks at the most recent archive, you may not want
to run it immediately after a `create` action (borgmatic's default behavior).
Instead, it may make more sense to run the spot check on a separate schedule
from `create`.


### Check frequency

<span class="minilink minilink-addedin">New in version 1.6.2</span> You can
optionally configure checks to run on a periodic basis rather than every time
borgmatic runs checks. For instance:

```yaml
checks:
    - name: repository
      frequency: 2 weeks
    - name: archives
      frequency: 1 month
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `consistency:` section of your configuration.

This tells borgmatic to run the `repository` consistency check at most once
every two weeks for a given repository and the `archives` check at most once a
month. The `frequency` value is a number followed by a unit of time, e.g. `3
days`, `1 week`, `2 months`, etc. The set of possible time units is as
follows (singular or plural):

 * `second`
 * `minute`
 * `hour`
 * `day`
 * `week` (7 days)
 * `month` (30 days)
 * `year` (365 days)

The `frequency` defaults to `always` for a check configured without a
`frequency`, which means run this check every time checks run. But if you omit
consistency checks from configuration entirely, borgmatic runs full-repository
checks (`repository`) and per-archive checks (`archives`) within each
repository, at most once a month.

Unlike a real scheduler like cron, borgmatic only makes a best effort to run
checks on the configured frequency. It compares that frequency with how long
it's been since the last check for a given repository If it hasn't been long
enough, the check is skipped. And you still have to run `borgmatic check` (or
`borgmatic` without actions) in order for checks to run, even when a
`frequency` is configured!

This also applies *across* configuration files that have the same repository
configured. Make sure you have the same check frequency configured in each
though—or the most frequently configured check will apply.

<span class="minilink minilink-addedin">New in version 1.9.0</span>To support
this frequency logic, borgmatic records check timestamps within the
`~/.local/state/borgmatic/checks` directory. To override the `~/.local/state`
portion of this path, set the `user_state_directory` configuration option.
Alternatively, set the `XDG_STATE_HOME` environment variable.

<span class="minilink minilink-addedin">New in version 1.9.2</span>The
`STATE_DIRECTORY` environment variable also works for this purpose. It's set
by systemd if `StateDirectory=borgmatic` is added to borgmatic's systemd
service file.

<span class="minilink minilink-addedin">Prior to version 1.9.0</span>
borgmatic recorded check timestamps within the `~/.borgmatic` directory. At
that time, the path was configurable by the `borgmatic_source_directory`
configuration option (now deprecated).

If you want to temporarily ignore your configured frequencies, you can invoke
`borgmatic check --force` to run checks unconditionally.

<span class="minilink minilink-addedin">New in version 1.8.6</span> `borgmatic
check --force` runs `check` even if it's specified in the `skip_actions`
option.


### Check days

<span class="minilink minilink-addedin">New in version 1.8.13</span> You can
optionally configure checks to only run on particular days of the week. For
instance:

```yaml
checks:
    - name: repository
      only_run_on:
         - Saturday
         - Sunday
    - name: archives
      only_run_on:
         - weekday
    - name: spot
      only_run_on:
         - Friday
         - weekend
```

Each day of the week is specified in the current locale (system
language/country settings). `weekend` and `weekday` are also accepted.

As with `frequency`, borgmatic only makes a best effort to run checks on the
given day of the week. For instance, if you run `borgmatic check` daily, then
every day borgmatic will have an opportunity to determine whether your checks
are configured to run on that day. If they are, then the checks run. If not,
they are skipped.

For instance, with the above configuration, if borgmatic is run on a Saturday,
the `repository` check will run. But on a Monday? The repository check will
get skipped. And if borgmatic is never run on a Saturday or a Sunday, that
check will never get a chance to run.

Also, the day of the week configuration applies *after* any configured
`frequency` for a check. So for instance, imagine the following configuration:

```yaml
checks:
    - name: repository
      frequency: 2 weeks
      only_run_on:
         - Monday
```

If you run borgmatic daily with that configuration, then borgmatic will first
wait two weeks after the previous check before running the check again—on the
first Monday after the `frequency` duration elapses.


### Running only checks

<span class="minilink minilink-addedin">New in version 1.7.1</span> If you
would like to only run consistency checks without creating backups (for
instance with the `check` action on the command-line), you can omit
the `source_directories` option entirely.

<span class="minilink minilink-addedin">Prior to version 1.7.1</span> In older
versions of borgmatic, instead specify an empty `source_directories` value, as
it is a mandatory option there:

```yaml
location:
    source_directories: []
```


### Disabling checks

If that's still too slow, you can disable consistency checks entirely,
either for a single repository or for all repositories.

<span class="minilink minilink-addedin">New in version 1.8.5</span> Disabling
all consistency checks looks like this:

```yaml
skip_actions:
    - check
```

<span class="minilink minilink-addedin">Prior to version 1.8.5</span> Use this
configuration instead:

```yaml
checks:
    - name: disabled
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
`checks:` in the `consistency:` section of your configuration.

<span class="minilink minilink-addedin">Prior to version 1.6.2</span>
`checks:` was a plain list of strings without the `name:` part. For instance:

```yaml
checks:
    - disabled
```

If you have multiple repositories in your borgmatic configuration file,
you can keep running consistency checks, but only against a subset of the
repositories:

```yaml
check_repositories:
    - path/of/repository_to_check.borg
```

Finally, you can override your configuration file's consistency checks and
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
