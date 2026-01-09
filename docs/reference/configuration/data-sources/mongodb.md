---
title: MongoDB
eleventyNavigation:
  key: MongoDB
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 1.5.22</span> To backup
MongoDB with borgmatic, use the `mongodb_databases:` hook.  For example:

```yaml
mongodb_databases:
    - name: messages
```


### Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/mongodb_databases.yaml %}
```
