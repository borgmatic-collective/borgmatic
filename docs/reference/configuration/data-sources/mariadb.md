---
title: MariaDB
eleventyNavigation:
  key: MariaDB
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 1.8.2</span> To backup
MariaDB with borgmatic, use the `mariadb_databases:` hook instead of
`mysql_databases:` as the MariaDB hook calls native MariaDB commands instead of
the deprecated MySQL ones. For instance:

```yaml
mariadb_databases:
    - name: comments
```


### Full configuration

```yaml
{% include borgmatic/mariadb_databases.yaml %}
```
