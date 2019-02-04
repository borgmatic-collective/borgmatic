---
title: How to make per-application backups
---
## Multiple backup configurations

You may find yourself wanting to create different backup policies for
different applications on your system. For instance, you may want one backup
configuration for your database data directory, and a different configuration
for your user home directories.

The way to accomplish that is pretty simple: Create multiple separate
configuration files and place each one in a `/etc/borgmatic.d/` directory. For
instance:

```bash
sudo mkdir /etc/borgmatic.d
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app1.yaml
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app2.yaml
```

When you set up multiple configuration files like this, borgmatic will run
each one in turn from a single borgmatic invocation. This includes, by
default, the traditional `/etc/borgmatic/config.yaml` as well.

And if you need even more customizability, you can specify alternate
configuration paths on the command-line with borgmatic's `--config` option.
See `borgmatic --help` for more information.


## Related documentation

 * [Set up backups with borgmatic](../../docs/how-to/set-up-backups.md)
