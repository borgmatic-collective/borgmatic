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
