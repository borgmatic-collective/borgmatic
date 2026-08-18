---
title: ⛔ Patterns and excludes
eleventyNavigation:
  key: ⛔ Patterns and excludes
  parent: ⚙️  Configuration
---

borgmatic's configuration has multiple options for specifying the source files
to include in your backups. Which of these options you use depends on how
complex your file matching needs are.

## Source directories

The `source_directories` option is the simplest way to specify the files and
directories to include in your backups. Globs (`*`) allow you to match multiple
paths at once, and tildes (`~`) get expanded to the current user's home
directory. Here's an example:

```yaml
source_directories:
    - /home
    - /etc
    - /var/log/syslog*
    - /home/user/path with spaces
    - ~/.config
```

## Excludes

The `exclude_patterns` options lists particular paths to exclude from your
backups, paths that would otherwise get included by `source_directories`. Globs
and tildes are also supported here. Use quotes as needed. For example:

```yaml
exclude_patterns:
    - '*.pyc'
    - '/home/*/.cache'
    - '*/.vim*.tmp'
    - /etc/ssl
    - /home/user/path with spaces
```

See the [Borg patterns
documentation](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-patterns)
for more details about the specific "fnmatch"-style syntax used by excludes.

The `exclude_from` option is similar to `exclude_patterns`, but with your patterns
listed in an external file instead of directly within borgmatic's configuration.
Here's an example:

```yaml
exclude_from:
    - /etc/borgmatic/excludes
```

Also see the [borgmatic configuration
reference](https://torsion.org/borgmatic/reference/configuration/) for
additional exclude-related options.


## Patterns

When you have more complex needs for including and excluding files to backup,
the `patterns` option is available. The definitive documentation on patterns is
the [Borg patterns
documentation](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-patterns),
but here are the basics.

First, unless you have `source_directories`, you need root patterns. In fact,
root patterns are just another way to specify the same paths as in
`source_directories`; they tell Borg the starting point for recursing into
directories to find files to backup. Root patterns are prefixed with "`R `". For
instance:

```yaml
patterns:
  - R /home
  - R /etc
```

You can also add excludes and includes to your patterns. Excludes are prefixed
with "`- `". If you're defining these directly in borgmatic's configuration
file, use quotes around the pattern. For example:

```yaml
patterns:
  - R /home
  - '- /home/user/.cache'
  - R /etc
```

How this works is that when Borg discovers a particular file path as it's
recursing into root directories, it tries to match that path against any
excludes and includes in your patterns *in order*, one at a time. If the first
match is to an exclude, then Borg excludes the file from the backup. But if the
first match is to an include, Borg includes it—even if there's a subsequent
exclude.

The respective order of root patterns vs. exclude and include patterns doesn't
matter to Borg, so organize root patterns how you like.

Here's an example of an include, which is prefixed with "`+ `":

```yaml
patterns:
  - R /home
  - '+ /home/user/.cache/keep-me'
  - '- /home/user/.cache'
  - R /etc
```

This example excludes all of the `.cache` directory—except for the `keep-me`
subdirectory, which gets included since it's listed first.

There's also a different kind of exclude pattern—a no-recurse exclude. That's
prefixed with "`! `" and tells Borg to not only exclude any matching paths but
also to ignore any subdirectories, saving file processing time. Here's an
example:

```yaml
patterns:
  - R /home
  - '! /home/user/.cache'
  - R /etc
```

The `patterns_from` option is similar to `patterns`, but with your patterns
listed in an external file instead of directly within borgmatic's configuration.
Here's an example:

```yaml
patterns_from:
    - /etc/borgmatic/patterns
```

## Debugging

Under the hood, borgmatic actually converts `source_directories`,
`exclude_patterns`, and `exclude_from` values to Borg patterns and merges them
with any `patterns` and `patterns_from` values you've configured—passing the
resulting processed patterns to Borg.

To see the combined patterns that borgmatic passes to Borg, run borgmatic with
[`--verbosity 2`](https://torsion.org/borgmatic/reference/command-line/logging/)
(and optionally `--dry-run`) and look for "`Writing patterns to ...`" in the
output. For instance:

```
repo: Writing patterns to /tmp/borgmatic-xzwb6s07/borgmatic/tmp61shymp0:
R /tmp/borgmatic-xzwb6s07/./borgmatic/sqlite_databases
+ /tmp/borgmatic-xzwb6s07/./borgmatic/sqlite_databases
R /home
R /etc
! fm:/home/user/.cache
```

You'll notice that borgmatic prepends your patterns with its own to support
use cases like streaming database dumps to Borg, creating filesystem snapshots,
saving bootstrap metadata, and so on.
