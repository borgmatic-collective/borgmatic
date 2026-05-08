---
title: MySQL
eleventyNavigation:
  key: MySQL
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 1.4.9</span> To backup
MySQL with borgmatic, use the `mysql_databases:` hook. For instance:

```yaml
mysql_databases:
    - name: posts
```


## Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/mysql_databases.yaml %}
```


## Related documentation

 * [How to backup your databases](https://torsion.org/borgmatic/how-to/backup-your-databases/)
