---
title: Overrides
eleventyNavigation:
  key: 🔄 Overrides
  parent: 💻 Command-line
---
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
documentation](https://torsion.org/borgmatic/reference/command-line/) for
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
variables](https://torsion.org/borgmatic/reference/configuration/environment-variables/).


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
reference](https://torsion.org/borgmatic/reference/configuration/) for
which options are list types. (YAML list values look like `- this` with an
indentation and a leading dash.)


