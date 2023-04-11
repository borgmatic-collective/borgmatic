---
title: How to make per-application backups
eleventyNavigation:
  key: 🔀 Make per-application backups
  parent: How-to guides
  order: 1
---
## Multiple backup configurations

You may find yourself wanting to create different backup policies for
different applications on your system or even for different backup
repositories. For instance, you might want one backup configuration for your
database data directory and a different configuration for your user home
directories. Or one backup configuration for your local backups with a
different configuration for your remote repository.

The way to accomplish that is pretty simple: Create multiple separate
configuration files and place each one in a `/etc/borgmatic.d/` directory. For
instance, for applications:

```bash
sudo mkdir /etc/borgmatic.d
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app1.yaml
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app2.yaml
```

Or, for repositories:

```bash
sudo mkdir /etc/borgmatic.d
sudo generate-borgmatic-config --destination /etc/borgmatic.d/repo1.yaml
sudo generate-borgmatic-config --destination /etc/borgmatic.d/repo2.yaml
```

When you set up multiple configuration files like this, borgmatic will run
each one in turn from a single borgmatic invocation. This includes, by
default, the traditional `/etc/borgmatic/config.yaml` as well.

Each configuration file is interpreted independently, as if you ran borgmatic
for each configuration file one at a time. In other words, borgmatic does not
perform any merging of configuration files by default. If you'd like borgmatic
to merge your configuration files, for instance to avoid duplication of
settings, see below about configuration includes.

Additionally, the `~/.config/borgmatic.d/` directory works the same way as
`/etc/borgmatic.d`.

If you need even more customizability, you can specify alternate configuration
paths on the command-line with borgmatic's `--config` flag. (See `borgmatic
--help` for more information.) For instance, if you want to schedule your
various borgmatic backups to run at different times, you'll need multiple
entries in your [scheduling software of
choice](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#autopilot),
each entry using borgmatic's `--config` flag instead of relying on
`/etc/borgmatic.d`.


## Archive naming

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
storage:
    ...
    archive_name_format: home-directories-{now}
```

This means that when borgmatic creates an archive, its name will start with
the string `home-directories-` and end with a timestamp for its creation time.
If `archive_name_format` is unspecified, the default is
`{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}`, meaning your system hostname plus a
timestamp in a particular format.

<span class="minilink minilink-addedin">New in version 1.7.11</span> borgmatic
uses the `archive_name_format` option to automatically limit which archives
get used for actions operating on multiple archives. This prevents, for
instance, duplicate archives from showing up in `rlist` or `info` results—even
if the same repository appears in multiple borgmatic configuration files. To
take advantage of this feature, simply use a different `archive_name_format`
in each configuration file.

Under the hood, borgmatic accomplishes this by substituting globs for certain
ephemeral data placeholders in your `archive_name_format`—and using the result
to filter archives when running supported actions.

For instance, let's say that you have this in your configuration:

```yaml
storage:
    ...
    archive_name_format: {hostname}-user-data-{now}
```

borgmatic considers `{now}` an emphemeral data placeholder that will probably
change per archive, while `{hostname}` won't. So it turns the example value
into `{hostname}-user-data-*` and applies it to filter down the set of
archives used for actions like `rlist`, `info`, `prune`, `check`, etc.

The end result is that when borgmatic runs the actions for a particular
application-specific configuration file, it only operates on the archives
created for that application. Of course, this doesn't apply to actions like
`compact` that operate on an entire repository.

If this behavior isn't quite smart enough for your needs, you can use the
`match_archives` option to override the pattern that borgmatic uses for
filtering archives. For example:

```yaml
storage:
    ...
    archive_name_format: {hostname}-user-data-{now}
    match_archives: sh:myhost-user-data-*        
```

For Borg 1.x, use a shell pattern for the `match_archives` value and see the
[Borg patterns
documentation](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns)
for more information. For Borg 2.x, see the [match archives
documentation](https://borgbackup.readthedocs.io/en/2.0.0b5/usage/help.html#borg-help-match-archives).

Some borgmatic command-line actions also have a `--match-archives` flag that
overrides both the auto-matching behavior and the `match_archives`
configuration option.

<span class="minilink minilink-addedin">Prior to 1.7.11</span> The way to
limit the archives used for the `prune` action was a `prefix` option in the
`retention` section for matching against the start of archive names. And the
option for limiting the archives used for the `check` action was a separate
`prefix` in the `consistency` section. Both of these options are deprecated in
favor of the auto-matching behavior (or `match_archives`/`--match-archives`)
in newer versions of borgmatic.


## Configuration includes

Once you have multiple different configuration files, you might want to share
common configuration options across these files with having to copy and paste
them. To achieve this, you can put fragments of common configuration options
into a file, and then include or inline that file into one or more borgmatic
configuration files.

Let's say that you want to include common retention configuration across all
of your configuration files. You could do that in each configuration file with
the following:

```yaml
location:
   ...

retention:
    !include /etc/borgmatic/common_retention.yaml
```

And then the contents of `common_retention.yaml` could be:

```yaml
keep_hourly: 24
keep_daily: 7
```

To prevent borgmatic from trying to load these configuration fragments by
themselves and complaining that they are not valid configuration files, you
should put them in a directory other than `/etc/borgmatic.d/`. (A subdirectory
is fine.)

When a configuration include is a relative path, borgmatic loads it from either
the current working directory or from the directory containing the file doing
the including.

Note that this form of include must be a YAML value rather than a key. For
example, this will not work:

```yaml
location:
   ...

# Don't do this. It won't work!
!include /etc/borgmatic/common_retention.yaml
```

But if you do want to merge in a YAML key *and* its values, keep reading!


## Include merging

If you need to get even fancier and merge in common configuration options, you
can perform a YAML merge of included configuration using the YAML `<<` key.
For instance, here's an example of a main configuration file that pulls in
retention and consistency options via a single include:

```yaml
<<: !include /etc/borgmatic/common.yaml

location:
   ...
```

This is what `common.yaml` might look like:

```yaml
retention:
    keep_hourly: 24
    keep_daily: 7

consistency:
    checks:
        - name: repository
```

Once this include gets merged in, the resulting configuration would have all
of the `location` options from the original configuration file *and* the
`retention` and `consistency` options from the include.

Prior to borgmatic version 1.6.0, when there's a section collision between the
local file and the merged include, the local file's section takes precedence.
So if the `retention` section appears in both the local file and the include
file, the included `retention` is ignored in favor of the local `retention`.
But see below about deep merge in version 1.6.0+.

Note that this `<<` include merging syntax is only for merging in mappings
(configuration options and their values). But if you'd like to include a
single value directly, please see the section above about standard includes.

Additionally, there is a limitation preventing multiple `<<` include merges
per section. So for instance, that means you can do one `<<` merge at the
global level, another `<<` within each configuration section, etc. (This is a
YAML limitation.)


### Deep merge

<span class="minilink minilink-addedin">New in version 1.6.0</span> borgmatic
performs a deep merge of merged include files, meaning that values are merged
at all levels in the two configuration files. This allows you to include
common configuration—up to full borgmatic configuration files—while overriding
only the parts you want to customize.

For instance, here's an example of a main configuration file that pulls in two
retention options via an include and then overrides one of them locally:

```yaml
<<: !include /etc/borgmatic/common.yaml

location:
   ...

retention:
    keep_daily: 5
```

This is what `common.yaml` might look like:

```yaml
retention:
    keep_hourly: 24
    keep_daily: 7
```

Once this include gets merged in, the resulting configuration would have a
`keep_hourly` value of `24` and an overridden `keep_daily` value of `5`.

When there's an option collision between the local file and the merged
include, the local file's option takes precedence.

<span class="minilink minilink-addedin">New in version 1.6.1</span> Colliding
list values are appended together.


## Debugging includes

<span class="minilink minilink-addedin">New in version 1.7.12</span> If you'd
like to see what the loaded configuration looks like after includes get merged
in, run `validate-borgmatic-config` on your configuration file:

```bash
sudo validate-borgmatic-config --show
```

You'll need to specify your configuration file with `--config` if it's not in
a default location.

This will output the merged configuration as borgmatic sees it, which can be
helpful for understanding how your includes work in practice.


## Configuration overrides

In more complex multi-application setups, you may want to override particular
borgmatic configuration file options at the time you run borgmatic. For
instance, you could reuse a common configuration file for multiple
applications, but then set the repository for each application at runtime. Or
you might want to try a variant of an option for testing purposes without
actually touching your configuration file.

Whatever the reason, you can override borgmatic configuration options at the
command-line via the `--override` flag. Here's an example:

```bash
borgmatic create --override location.remote_path=/usr/local/bin/borg1
```

What this does is load your configuration files, and for each one, disregard
the configured value for the `remote_path` option in the `location` section,
and use the value of `/usr/local/bin/borg1` instead.

You can even override multiple values at once. For instance:

```bash
borgmatic create --override section.option1=value1 section.option2=value2
```

This will accomplish the same thing:

```bash
borgmatic create --override section.option1=value1 --override section.option2=value2
```

Note that each value is parsed as an actual YAML string, so you can even set
list values by using brackets. For instance:

```bash
borgmatic create --override location.repositories=[test1.borg,test2.borg]
```

Or even a single list element:

```bash
borgmatic create --override location.repositories=[/root/test.borg]
```

If your override value contains special YAML characters like colons, then
you'll need quotes for it to parse correctly:

```bash
borgmatic create --override location.repositories="['user@server:test.borg']"
```

There is not currently a way to override a single element of a list without
replacing the whole list.

Note that if you override an option of the list type (like
`location.repositories`), you do need to use the `[ ]` list syntax. See the
[configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/) for
which options are list types. (YAML list values look like `- this` with an
indentation and a leading dash.)

Be sure to quote your overrides if they contain spaces or other characters
that your shell may interpret.

An alternate to command-line overrides is passing in your values via [environment variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).


## Constant interpolation

<span class="minilink minilink-addedin">New in version 1.7.10</span> Another
tool is borgmatic's support for defining custom constants. This is similar to
the [variable interpolation
feature](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/#variable-interpolation)
for command hooks, but the constants feature lets you substitute your own
custom values into anywhere in the entire configuration file. (Constants don't
work across includes or separate configuration files though.)

Here's an example usage:

```yaml
constants:
    user: foo
    archive_prefix: bar

location:
    source_directories:
        - /home/{user}/.config
        - /home/{user}/.ssh
    ...

storage:
    archive_name_format: '{archive_prefix}-{now}'
```

In this example, when borgmatic runs, all instances of `{user}` get replaced
with `foo` and all instances of `{archive-prefix}` get replaced with `bar-`.
(And in this particular example, `{now}` doesn't get replaced with anything,
but gets passed directly to Borg.) After substitution, the logical result
looks something like this:

```yaml
location:
    source_directories:
        - /home/foo/.config
        - /home/foo/.ssh
    ...

storage:
    archive_name_format: 'bar-{now}'
```

An alternate to constants is passing in your values via [environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).
