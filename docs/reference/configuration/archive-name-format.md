---
title: 📛 Archive name format
eleventyNavigation:
  key: 📛 Archive name format
  parent: ⚙️  Configuration
---
If you've got multiple borgmatic configuration files, you might want to create
archives with different naming schemes for each one. This is especially handy
if each configuration file is backing up to the same Borg repository but you
still want to be able to distinguish backup archives for one application from
another.

borgmatic supports this use case with an `archive_name_format` option. The
idea is that you define a string format containing a number of [Borg
placeholders](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-placeholders),
and borgmatic uses that format to name any new archive it creates. For
instance:

```yaml
archive_name_format: home-directories-{now}
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `storage:` section of your configuration.

This example means that when borgmatic creates an archive, its name will start
with the string `home-directories-` and end with a timestamp for its creation
time. If `archive_name_format` is unspecified, the default with Borg 1 is
`{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}`, meaning your system hostname plus a
timestamp in a particular format.

<span class="minilink minilink-addedin">New in borgmatic version 1.9.0 with
Borg version 2.x</span>The default is just `{hostname}`, as Borg 2 does not
require unique archive names; identical archive names form a common "series"
that can be targeted together.


### Archive filtering

<span class="minilink minilink-addedin">New in version 1.7.11</span> borgmatic
uses the `archive_name_format` option to automatically limit which archives
get used for actions operating on multiple archives. This prevents, for
instance, duplicate archives from showing up in `repo-list` or `info`
results—even if the same repository appears in multiple borgmatic
configuration files. To take advantage of this feature, use a different
`archive_name_format` in each configuration file.

Under the hood, borgmatic accomplishes this by substituting globs for certain
ephemeral data placeholders in your `archive_name_format`—and using the result
to filter archives when running supported actions.

For instance, let's say that you have this in your configuration:

```yaml
archive_name_format: {hostname}-user-data-{now}
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `storage:` section of your configuration.

borgmatic considers `{now}` an emphemeral data placeholder that will probably
change per archive, while `{hostname}` won't. So it turns the example value
into `{hostname}-user-data-*` and applies it to filter down the set of
archives used for actions like `repo-list`, `info`, `prune`, `check`, etc.

The end result is that when borgmatic runs the actions for a particular
application-specific configuration file, it only operates on the archives
created for that application. But this doesn't apply to actions like `compact`
that operate on an entire repository.

If this behavior isn't quite smart enough for your needs, you can use the
`match_archives` option to override the pattern that borgmatic uses for
filtering archives. For example:

```yaml
archive_name_format: {hostname}-user-data-{now}
match_archives: sh:myhost-user-data-*        
```

<span class="minilink minilink-addedin">With Borg version 1.x</span>Use a shell
pattern for the `match_archives` value and see the [Borg patterns
documentation](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns)
for more information.

<span class="minilink minilink-addedin">With Borg version 2.x</span>See the
[match archives
documentation](https://borgbackup.readthedocs.io/en/2.0.0b16/usage/help.html#borg-help-match-archives).

Some borgmatic command-line actions also have a `--match-archives` flag that
overrides both the auto-matching behavior and the `match_archives`
configuration option.

<span class="minilink minilink-addedin">Prior to version 1.7.11</span> The way
to limit the archives used for the `prune` action was a `prefix` option in the
`retention` section for matching against the start of archive names. And the
option for limiting the archives used for the `check` action was a separate
`prefix` in the `consistency` section. Both of these options are deprecated in
favor of the auto-matching behavior (or `match_archives`/`--match-archives`)
in newer versions of borgmatic.

