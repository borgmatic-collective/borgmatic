---
title: Command-line
eleventyNavigation:
  key: 💻 Command-line
  parent: Reference guides
  order: 1
---
Here are all of the available global borgmatic command-line flags for the [most
recent version of
borgmatic](https://projects.torsion.org/borgmatic-collective/borgmatic/releases),
including the separate flags for each action (sub-command). Most of the flags
listed here have equivalents in borgmatic's [configuration
file](https://torsion.org/borgmatic/reference/configuration/).

Also see the [actions
documentation](https://torsion.org/borgmatic/reference/command-line/actions/)
for the command-line flags for individual actions.

If you're using an older version of borgmatic, some of these flags may not be
present in that version and you should instead use `borgmatic --help` or
`borgmatic [action name] --help` (where `[action name]` is the name of an
action like `list`, `create`, etc.).

```
{% include borgmatic/command-line/global.txt %}
```
