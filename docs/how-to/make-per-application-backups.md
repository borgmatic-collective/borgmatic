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
sudo borgmatic config generate --destination /etc/borgmatic.d/app1.yaml
sudo borgmatic config generate --destination /etc/borgmatic.d/app2.yaml
```

Or, for repositories:

```bash
sudo mkdir /etc/borgmatic.d
sudo borgmatic config generate --destination /etc/borgmatic.d/repo1.yaml
sudo borgmatic config generate --destination /etc/borgmatic.d/repo2.yaml
```

<span class="minilink minilink-addedin">Prior to version 1.7.15</span> The
command to generate configuration files was `generate-borgmatic-config`
instead of `borgmatic config generate`.

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


## Configuration includes

Once you have multiple different configuration files, you might want to share
common configuration options across these files without having to copy and paste
them. To achieve this, you can put fragments of common configuration options
into a file and then include or inline that file into one or more borgmatic
configuration files.

Let's say that you want to include common consistency check configuration across all
of your configuration files. You could do that in each configuration file with
the following:

```yaml
repositories:
    - path: repo.borg

checks:
    !include /etc/borgmatic/common_checks.yaml
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> These
options were organized into sections like `location:` and `consistency:`.

The contents of `common_checks.yaml` could be:

```yaml
- name: repository
  frequency: 3 weeks
- name: archives
  frequency: 2 weeks
```

To prevent borgmatic from trying to load these configuration fragments by
themselves and complaining that they are not valid configuration files, you
should put them in a directory other than `/etc/borgmatic.d/`. (A subdirectory
is fine.)

When a configuration include is a relative path, borgmatic loads it from either
the current working directory or from the directory containing the file doing
the including.

Note that this form of include must be a value rather than an option name. For
example, this will not work:

```yaml
repositories:
    - path: repo.borg

# Don't do this. It won't work!
!include /etc/borgmatic/common_checks.yaml
```

But if you do want to merge in a option name *and* its values, keep reading!


## Include merging

If you need to get even fancier and merge in common configuration options, you
can perform a YAML merge of included configuration using the YAML `<<` key.
For instance, here's an example of a main configuration file that pulls in
retention and consistency checks options via a single include:

```yaml
repositories:
   - path: repo.borg

<<: !include /etc/borgmatic/common.yaml
```

This is what `common.yaml` might look like:

```yaml
keep_hourly: 24
keep_daily: 7

checks:
    - name: repository
      frequency: 3 weeks
    - name: archives
      frequency: 2 weeks
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> These
options were organized into sections like `retention:` and `consistency:`.

Once this include gets merged in, the resulting configuration has all of the
options from the original configuration file *and* the options from the
include.

Note that this `<<` include merging syntax is only for merging in mappings
(configuration options and their values). If you'd like to include a single
value directly, please see above about standard includes.


### Multiple merge includes

borgmatic has a limitation preventing multiple `<<` include merges per file or
option value. This means you can do a single `<<` merge at the global level,
another `<<` within each nested option value, etc. (This is a YAML
limitation.) For instance:

```yaml
repositories:
   - path: repo.borg

# This won't work! You can't do multiple merges like this at the same level.
<<: !include common1.yaml
<<: !include common2.yaml
```

But read on for a way around this.

<span class="minilink minilink-addedin">New in version 1.8.1</span> You can
include and merge multiple configuration files all at once. For instance:

```yaml
repositories:
   - path: repo.borg

<<: !include [common1.yaml, common2.yaml, common3.yaml]
```

This merges in each included configuration file in turn, such that later files
replace the options in earlier ones.

Here's another way to do the same thing:

```yaml
repositories:
   - path: repo.borg

<<: !include
    - common1.yaml
    - common2.yaml
    - common3.yaml
```


### Deep merge

<span class="minilink minilink-addedin">New in version 1.6.0</span> borgmatic
performs a deep merge of merged include files, meaning that values are merged
at all levels in the two configuration files. This allows you to include
common configuration—up to full borgmatic configuration files—while overriding
only the parts you want to customize.

For instance, here's an example of a main configuration file that pulls in
options via an include and then overrides one of them locally:

```yaml
<<: !include /etc/borgmatic/common.yaml

constants:
    base_directory: /opt

repositories:
    - path: repo.borg
```

This is what `common.yaml` might look like:

```yaml
constants:
    app_name: myapp
    base_directory: /var/lib
```

Once this include gets merged in, the resulting configuration would have an
`app_name` value of `myapp` and an overridden `base_directory` value of
`/opt`.

When there's an option collision between the local file and the merged
include, the local file's option takes precedence.


#### List merge

<span class="minilink minilink-addedin">New in version 1.6.1</span> Colliding
list values are appended together.

<span class="minilink minilink-addedin">New in version 1.7.12</span> If there
is a list value from an include that you *don't* want in your local
configuration file, you can omit it with an `!omit` tag. For instance:

```yaml
<<: !include /etc/borgmatic/common.yaml

source_directories:
    - !omit /home
    - /var
```

And `common.yaml` like this:

```yaml
source_directories:
    - /home
    - /etc
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put the
`source_directories` option in the `location:` section of your configuration.

Once this include gets merged in, the resulting configuration will have a
`source_directories` value of `/etc` and `/var`—with `/home` omitted.

This feature currently only works on scalar (e.g. string or number) list items
and will not work elsewhere in a configuration file. Be sure to put the
`!omit` tag *before* the list item (after the dash). Putting `!omit` after the
list item will not work, as it gets interpreted as part of the string. Here's
an example of some things not to do:

```yaml
<<: !include /etc/borgmatic/common.yaml

source_directories:
    # Do not do this! It will not work. "!omit" belongs before "/home".
    - /home !omit

# Do not do this either! "!omit" only works on scalar list items.
repositories: !omit
    # Also do not do this for the same reason! This is a list item, but it's
    # not a scalar.
    - !omit path: repo.borg
```

Additionally, the `!omit` tag only works in a configuration file that also
performs a merge include with `<<: !include`. It doesn't make sense within,
for instance, an included configuration file itself (unless it in turn
performs its own merge include). That's because `!omit` only applies to the
file doing the include; it doesn't work in reverse or propagate through
includes.


### Shallow merge

Even though deep merging is generally pretty handy for included files,
sometimes you want specific options in the local file to take precedence over
included options—without any merging occurring for them.

<span class="minilink minilink-addedin">New in version 1.7.12</span> That's
where the `!retain` tag comes in. Whenever you're merging an included file
into your configuration file, you can optionally add the `!retain` tag to
particular local mappings or lists to retain the local values and ignore
included values.

For instance, start with this configuration file containing the `!retain` tag
on the `retention` mapping:

```yaml
<<: !include /etc/borgmatic/common.yaml

repositories:
    - path: repo.borg

checks: !retain
    - name: repository
```

And `common.yaml` like this:

```yaml
repositories:
    - path: common.borg

checks:
    - name: archives
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> These
options were organized into sections like `location:` and `consistency:`.

Once this include gets merged in, the resulting configuration will have a
`checks` value with a name of `repository` and no other values. That's because
the `!retain` tag says to retain the local version of `checks` and ignore any
values coming in from the include. But because the `repositories` list doesn't
have a `!retain` tag, it still gets merged together to contain both
`common.borg` and `repo.borg`.

The `!retain` tag can only be placed on mappings (keys/values) and lists, and
it goes right after the name of the option (and its colon) on the same line.
The effects of `!retain` are recursive, meaning that if you place a `!retain`
tag on a top-level mapping, even deeply nested values within it will not be
merged.

Additionally, the `!retain` tag only works in a configuration file that also
performs a merge include with `<<: !include`. It doesn't make sense within,
for instance, an included configuration file itself (unless it in turn
performs its own merge include). That's because `!retain` only applies to the
file doing the include; it doesn't work in reverse or propagate through
includes.


## Debugging includes

<span class="minilink minilink-addedin">New in version 1.7.15</span> If you'd
like to see what the loaded configuration looks like after includes get merged
in, run the `validate` action on your configuration file:

```bash
sudo borgmatic config validate --show
```

<span class="minilink minilink-addedin">In version 1.7.12 through
1.7.14</span> Use this command instead:

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

<span class="minilink minilink-addedin">New in version 2.0.0</span>
Whatever the reason, you can override borgmatic configuration options at the
command-line, as there's a command-line flag corresponding to every
configuration option (with its underscores converted to dashes).

For instance, to override the `compression` configuration option, use the
corresponding `--compression` flag on the command-line:

```bash
borgmatic create --compression zstd
```

What this does is load your given configuration files and for each one, disregard
the configured value for the `compression` option and use the value given on the
command-line instead—but just for the duration of the borgmatic run.

You can override nested configuration options too by separating such option
names with a period. For instance:

```bash
borgmatic create --bootstrap.store-config-files false
```

You can even set complex option data structures by using inline YAML syntax. For
example, set the `repositories` option with a YAML list of key/value pairs:

```bash
borgmatic create --repositories "[{path: /mnt/backup, label: local}]"
```

If your override value contains characters like colons or spaces, then you'll
need to use quotes for it to parse correctly.

You can also set individual nested options within existing list elements:

```bash
borgmatic create --repositories[0].path /mnt/backup
```

This updates the `path` option for the first repository in `repositories`.
Change the `[0]` index as needed to address different list elements. And note
that this only works for elements already set in configuration; you can't append
new list elements from the command-line.

See the [command-line reference
documentation](https://torsion.org/borgmatic/docs/reference/command-line/) for
the full set of available arguments, including examples of each for the complex
values.

There are a handful of configuration options that don't have corresponding
command-line flags at the global scope, but instead have flags within individual
borgmatic actions. For instance, the `list_details` option can be overridden by
the `--list` flag that's only present on particular actions. Similarly with
`progress` and `--progress`, `statistics` and `--stats`, and `match_archives`
and `--match-archives`.

Also note that if you want to pass a command-line flag itself as a value to one
of these override flags, that may not work. For instance, specifying
`--extra-borg-options.create --no-cache-sync` results in an error, because
`--no-cache-sync` gets interpreted as a borgmatic option (which in this case
doesn't exist) rather than a Borg option.

An alternate to command-line overrides is passing in your values via
[environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).


### Deprecated overrides

<span class="minilink minilink-addedin">Prior to version 2.0.0</span>
Configuration overrides were performed with an `--override` flag. You can still
use `--override` with borgmatic 2.0.0+, but it's deprecated in favor of the new
command-line flags described above.

Here's an example of `--override`:

```bash
borgmatic create --override remote_path=/usr/local/bin/borg1
```

What this does is load your given configuration files and for each one, disregard
the configured value for the `remote_path` option and use the value given on the
command-line instead—but just for the duration of the borgmatic run.

You can even override nested values or multiple values at once. For instance:

```bash
borgmatic create --override parent_option.option1=value1 --override parent_option.option2=value2
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Don't
forget to specify the section that an option is in. That looks like a prefix
on the option name, e.g. `location.repositories`.

Note that each value is parsed as an actual YAML string, so you can set list
values by using brackets. For instance:

```bash
borgmatic create --override repositories=[test1.borg,test2.borg]
```

Or a single list element:

```bash
borgmatic create --override repositories=[/root/test.borg]
```

Or a single list element that is a key/value pair:

```bash
borgmatic create --override repositories="[{path: test.borg, label: test}]"
```

If your override value contains characters like colons or spaces, then you'll
need to use quotes for it to parse correctly.

Another example:

```bash
borgmatic create --override repositories="['user@server:test.borg']"
```

There is not currently a way to override a single element of a list without
replacing the whole list.

Using the `[ ]` list syntax is required when overriding an option of the list
type (like `location.repositories`). See the [configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/) for
which options are list types. (YAML list values look like `- this` with an
indentation and a leading dash.)


## Constant interpolation

<span class="minilink minilink-addedin">New in version 1.7.10</span> Another
tool is borgmatic's support for defining custom constants. This is similar to
the [variable interpolation
feature](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/#variable-interpolation)
for command hooks, but the constants feature lets you substitute your own
custom values into any option values in the entire configuration file.

Here's an example usage:

```yaml
constants:
    user: foo
    archive_prefix: bar

source_directories:
    - /home/{user}/.config
    - /home/{user}/.ssh

...

archive_name_format: '{archive_prefix}-{now}'
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Don't
forget to specify the section (like `location:` or `storage:`) that any option
is in.

In this example, when borgmatic runs, all instances of `{user}` get replaced
with `foo` and all instances of `{archive_prefix}` get replaced with `bar`.
And `{now}` doesn't get replaced with anything, but gets passed directly to
Borg, which has its own
[placeholders](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-placeholders)
using the same syntax as borgmatic constants. So borgmatic options like
`archive_name_format` that get passed directly to Borg can use either Borg
placeholders or borgmatic constants or both!

After substitution, the logical result looks something like this:

```yaml
source_directories:
    - /home/foo/.config
    - /home/foo/.ssh

...

archive_name_format: 'bar-{now}'
```

Note that if you'd like to interpolate a constant into the beginning of a
value, you'll need to quote it. For instance, this won't work:

```yaml
source_directories:
    - {my_home_directory}/.config   # This will error!
```

Instead, do this:

```yaml
source_directories:
    - "{my_home_directory}/.config"
```

<span class="minilink minilink-addedin">New in version 1.8.5</span> Constants
work across includes, meaning you can define a constant and then include a
separate configuration file that uses that constant.

An alternate to constants is passing in your values via [environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).
