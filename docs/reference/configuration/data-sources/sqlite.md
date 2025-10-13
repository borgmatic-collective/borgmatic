---
title: SQLite
eleventyNavigation:
  key: • SQLite
  parent: 🗄️ Data sources
---
<span class="minilink minilink-addedin">New in version 1.7.9</span> To backup
SQLite with borgmatic, use the `sqlite_databases:` hook. For example:


```yaml
sqlite_databases:
    - name: mydb
      path: /var/lib/sqlite3/mydb.sqlite
```


## Full configuration

```yaml
{% include borgmatic/sqlite_databases.yaml %}
```
