---
title: ❗ Includes
eleventyNavigation:
  key: ❗ Includes
  parent: ⚙️  Configuration
---
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

Also see the [`config show`
action](https://torsion.org/borgmatic/reference/command-line/actions/config-show/).
