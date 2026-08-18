---
title: 🟰 Constants
eleventyNavigation:
  key: 🟰 Constants
  parent: ⚙️  Configuration
---
<span class="minilink minilink-addedin">New in version 1.7.10</span> borgmatic
supports defining custom configuration constants. This is similar to the
[variable interpolation
feature](https://torsion.org/borgmatic/reference/configuration/command-hooks/#variable-interpolation)
for command hooks, but the constants feature lets you substitute your own custom
values into any option values in the entire configuration file.

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
work across
[includes](https://torsion.org/borgmatic/reference/configuration/includes/),
meaning you can define a constant and then include a separate configuration file
that uses that constant.

An alternate to constants is passing in your values via [environment
variables](https://torsion.org/borgmatic/reference/configuration/environment-variables/).


## Disabling constants

<span class="minilink minilink-addedin">New in version 2.1.0</span> To prevent
borgmatic from attempting constant interpolation on a specific would-be
constant name, you can backslash its curly brackets. For instance:

```yaml
constants:
    name: foo

source_directories:
    - /home/user/\{name\}
```

This tells borgmatic to skip constant interpolation for `{name}` and instead use
the `{name}` literal. This is handy if you've got a filename that has literal
curly brackets around a name that happens to match a constant.
