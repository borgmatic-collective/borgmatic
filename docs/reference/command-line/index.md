---
title: Command-line
eleventyNavigation:
  key: 💻 Command-line
  parent: Reference guides
  order: 1
---
Here are all of the available borgmatic command-line flags for the [most
recent version of
borgmatic](https://projects.torsion.org/borgmatic-collective/borgmatic/releases),
including the separate flags for each action (sub-command). Most of the flags
listed here do not have equivalents in borgmatic's [configuration
file](https://torsion.org/borgmatic/reference/configuration/).

If you're using an older version of borgmatic, some of these flags may not be
present in that version and you should instead use `borgmatic --help` or
`borgmatic [action name] --help` (where `[action name]` is the name of an
action like `list`, `create`, etc.).

```
{% include borgmatic/command-line.txt %}
```
