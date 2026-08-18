---
title: ⚙️  Configuration
eleventyNavigation:
  key: ⚙️  Configuration
  parent: Reference guides
  order: 0
---
Below is a sample borgmatic configuration snippet for every available option in
the [most recent version of
borgmatic](https://projects.torsion.org/borgmatic-collective/borgmatic/releases).
A full example configuration file is also [available for
download](https://torsion.org/borgmatic/reference/config.yaml).

If you're using an older version of borgmatic, some of these options may not
work, and you should instead [generate a sample configuration file specific to
your borgmatic
version](https://torsion.org/borgmatic/how-to/set-up-backups/#configuration).

<span data-pagefind-weight="6.0">
{% for option_name in option_names %}
### {{ option_name }} option
```yaml
{% include borgmatic/{{ option_name }}.yaml %}
```
{% endfor %}
</span>
