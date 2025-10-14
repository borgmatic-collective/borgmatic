---
title: PostgreSQL
eleventyNavigation:
  key: PostgreSQL
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 1.4.0</span> To backup
PostgreSQL with borgmatic, use the `postgresql_databases:` hook. For instance:

```yaml
postgresql_databases:
    - name: users
```


## Full configuration

```yaml
{% include borgmatic/postgresql_databases.yaml %}
```
